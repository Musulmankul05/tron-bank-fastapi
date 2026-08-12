from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from models import UserModel
from models.users import KYCStatus_choice
from schemas.admin import KYCPendingSchema
from schemas.users import UserResponseSchema
from utils.dependencies import get_current_admin

router = APIRouter(prefix="/admin", tags=["ADMIN"])


@router.get("/kyc/pending", response_model=list[KYCPendingSchema])
async def get_kyc_pending_list(
    limit: int = 20,
    offset: int = 0,
    current_admin: UserModel = Depends(get_current_admin),
    db: AsyncSession = Depends(get_session),
):
    query = (
        select(UserModel)
        .where(UserModel.kyc_status == KYCStatus_choice.PENDING)
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    pending_list = result.scalars().all()
    return pending_list


@router.patch("/kyc/{user_id}/approve", response_model=UserResponseSchema)
async def approve_kyc(
    user_id: int,
    current_admin: UserModel = Depends(get_current_admin),
    db: AsyncSession = Depends(get_session),
):
    query = select(UserModel).where(
        and_(UserModel.id == user_id, UserModel.kyc_status == KYCStatus_choice.PENDING)
    )
    result = await db.execute(query)
    pending_kyc = result.scalar_one_or_none()
    if not pending_kyc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Incorrect user id")
    pending_kyc.kyc_status = KYCStatus_choice.VERIFIED
    await db.commit()
    await db.refresh(pending_kyc)
    return pending_kyc


@router.patch("/kyc/{user_id}/reject", response_model=UserResponseSchema)
async def reject_kyc(
    user_id: int,
    current_admin: UserModel = Depends(get_current_admin),
    db: AsyncSession = Depends(get_session),
):
    query = select(UserModel).where(
        and_(UserModel.id == user_id, UserModel.kyc_status == KYCStatus_choice.PENDING)
    )
    result = await db.execute(query)
    pending_kyc = result.scalar_one_or_none()
    if not pending_kyc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Incorrect user id")
    pending_kyc.kyc_status = KYCStatus_choice.REJECTED
    await db.commit()
    await db.refresh(pending_kyc)
    return pending_kyc
