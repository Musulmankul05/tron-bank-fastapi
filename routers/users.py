import secrets
import string
from datetime import timedelta
from typing import Optional

import pyotp
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from models import BackupCodesModel, KYCModel
from models.users import KYCStatus_choice, UserModel
from schemas.users import (
    BackupEnterSchema,
    KYCSchema,
    TokenSchema,
    TwoFARequiredSchema,
    UserCreateSchema,
    UserLoginSchema,
    UserResponseSchema,
)
from utils.dependencies import get_2fa_session, get_current_user
from utils.security import (
    auth,
    hash_backups,
    hash_password,
    verify_backups,
    verify_password,
)

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


@router.post(
    "/login",
    response_model=TokenSchema | TwoFARequiredSchema,
    status_code=status.HTTP_200_OK,
)
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
    if user is None or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Incorrect username/phone or password"
        )
    token = auth.create_access_token(uid=str(user.id), expiry=timedelta(minutes=5))
    response.set_cookie("temp_token", token)
    if user.is_2fa_enabled:
        return {"status": "2fa_required", "action": "verify"}
    return {"status": "2fa_required", "action": "setup"}


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


@router.post("/2fa/setup")
async def setup_2fa(
    user: UserModel = Depends(get_2fa_session), db: AsyncSession = Depends(get_session)
):
    if user.is_2fa_enabled:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Your 2FA is enabled")
    user.totp_secret = pyotp.random_base32()
    await db.commit()
    await db.refresh(user)
    totp_uri = pyotp.TOTP(user.totp_secret).provisioning_uri(
        name=user.username, issuer_name="tron.bank"
    )
    return {"totp_uri": totp_uri}


@router.post("/2fa/enable")
async def enable_2fa(
    code: str,
    response: Response,
    user: UserModel = Depends(get_2fa_session),
    db: AsyncSession = Depends(get_session),
):
    if not user.totp_secret:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Setup 2FA first")
    if pyotp.TOTP(user.totp_secret).verify(code, valid_window=1):
        user.is_2fa_enabled = True
        await db.commit()
        await db.refresh(user)
        response.delete_cookie("temp_token")
        token = auth.create_access_token(uid=str(user.id))
        response.set_cookie("auth_access_token", token)
        return {"auth_access_token": token}
    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Wrong TOTP code")


@router.post("/2fa/verify")
async def verify_2fa(
    code: str,
    response: Response,
    user: UserModel = Depends(get_2fa_session),
):
    if not user.totp_secret or not user.is_2fa_enabled:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Setup 2FA first")
    if pyotp.TOTP(user.totp_secret).verify(code, valid_window=1):
        response.delete_cookie("temp_token")
        token = auth.create_access_token(uid=str(user.id))
        response.set_cookie("auth_access_token", token)
        return {"auth_access_token": token}
    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Wrong TOTP code")


@router.get("/recovery/get")
async def get_backups(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    query = select(BackupCodesModel).where(BackupCodesModel.user_id == current_user.id)
    result = await db.execute(query)
    existing_code = result.scalar_one_or_none()
    if existing_code:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "You already have recovery codes"
        )
    plain_codes_list = []
    for _ in range(4):
        random_string = "".join(
            secrets.choice(string.ascii_letters.lower()) for _ in range(4)
        )
        plain_codes_list.append(random_string)
    plain_codes = "-".join(i for i in plain_codes_list)
    codes = BackupCodesModel(user_id=current_user.id, code=hash_backups(plain_codes))
    db.add(codes)
    await db.commit()
    await db.refresh(codes)
    plain_dict = {i: j for i, j in enumerate(plain_codes_list, 1)}
    return plain_dict


@router.post("/recovery")
async def reset_backups(
    payload: BackupEnterSchema,
    response: Response,
    current_user: UserModel = Depends(get_2fa_session),
    db: AsyncSession = Depends(get_session),
):
    query = select(BackupCodesModel).where(BackupCodesModel.user_id == current_user.id)
    result = await db.execute(query)
    codes = result.scalar_one_or_none()
    if not codes:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "You don't have recovery codes"
        )
    if not verify_backups(payload.code, codes.code):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect code")
    current_user.totp_secret = None
    current_user.is_2fa_enabled = False
    await db.delete(codes)
    await db.commit()
    response.delete_cookie("temp_token")
    token = auth.create_access_token(uid=str(current_user.id))
    response.set_cookie("auth_access_token", token)
    return {
        "message": "Backup code is deleted. You can set a new",
        "auth_access_token": token,
    }
