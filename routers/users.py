from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from models import KYCModel
from models.users import KYCStatus_choice, UserModel
from schemas.users import (
    KYCSchema,
    TokenSchema,
    UserCreateSchema,
    UserLoginSchema,
    UserResponseSchema,
)
from utils.dependencies import get_current_user
from utils.security import auth, hash_password, verify_password

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/register", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED
)
async def register_user(
    payload: UserCreateSchema, db: AsyncSession = Depends(get_session)
):
    """
    Registration Endpoint

    Args:
        payload (UserCreateSchema): Example from Pydantic Schema
        db (AsyncSession): Database session
    """
    query = select(UserModel).where(
        (UserModel.username == payload.username) | (UserModel.phone == payload.phone)
    )
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="user exists"
        )

    hashed_pwd = hash_password(payload.password)
    new_user = UserModel(
        first_name=payload.first_name,
        last_name=payload.last_name,
        username=payload.username,
        hashed_password=hashed_pwd,
        phone=payload.phone,
        email=payload.email,
        country=payload.country,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/login", response_model=TokenSchema, status_code=status.HTTP_200_OK)
async def login_user(
    response: Response, creds: UserLoginSchema, db: AsyncSession = Depends(get_session)
):
    conditions = []
    if creds.username:
        conditions.append(UserModel.username == creds.username)
    if creds.phone:
        conditions.append(UserModel.phone == creds.phone)
    if not conditions:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Enter username or phone"
        )
    query = select(UserModel).where(or_(*conditions))
    result = await db.execute(query)
    user = result.scalars().first()
    if user is not None and verify_password(creds.password, user.hashed_password):
        token = auth.create_access_token(uid=str(user.id))
        response.set_cookie("auth_access_token", token)
        return {"access_token": token}
    raise HTTPException(
        status.HTTP_401_UNAUTHORIZED, detail="Incorrect username/phone or password"
    )


@router.post("/logout")
async def logout_user(response: Response):
    response.delete_cookie("auth_access_token")
    return {"message": "Logout success"}


@router.get("/users", response_model=list[UserResponseSchema])
async def get_users(
    db: AsyncSession = Depends(get_session), username: Optional[str | None] = None
):
    query = select(UserModel)
    if username:
        query = query.where(UserModel.username == username)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/users/{user_id}")
async def get_user_by_id(user_id: int, db: AsyncSession = Depends(get_session)):
    query = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/me", response_model=UserResponseSchema)
async def get_my_profile(current_user: UserModel = Depends(get_current_user)):
    return current_user


@router.post("/kyc-verify", response_model=KYCSchema)
async def kyc_verification(
    payload: KYCSchema,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    if current_user.kyc_status == KYCStatus_choice.VERIFIED:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account already verified")
    query = select(KYCModel).where(
        or_(KYCModel.inn == payload.inn, KYCModel.user_id == current_user.id)
    )
    result = await db.execute(query)
    existing_kyc = result.scalar_one_or_none()
    if existing_kyc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account already exist")
    try:
        kyc = KYCModel(
            user_id=current_user.id,
            inn=payload.inn,
            passport_id=payload.passport_id,
            account_type=payload.account_type,
            signature=payload.signature,
        )
        db.add(kyc)
        current_user.kyc_status = KYCStatus_choice.VERIFIED
        await db.commit()
        await db.refresh(kyc)
        return kyc
    except Exception:
        current_user.kyc_status = KYCStatus_choice.REJECTED
        await db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Something went wrong")
