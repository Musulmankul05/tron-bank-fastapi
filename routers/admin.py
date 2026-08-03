from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_session
from models import KYCModel, UserModel
from models.users import KYCStatus_choice
from schemas.admin import KYCPendingSchema
from utils.dependencies import get_current_admin

router = APIRouter(prefix="/admin", tags=["ADMIN"])


@router.get("/kyc/pending", response_model=list[KYCPendingSchema])
async def get_kyc_pending_list(
    current_admin: UserModel = Depends(get_current_admin),
    db: AsyncSession = Depends(get_session),
):
    query = (
        select(UserModel)
        .where(UserModel.kyc_status == KYCStatus_choice.PENDING)
        .options(joinedload(UserModel.kyc))
    )
    result = await db.execute(query)
    pending_list = result.scalars().all()
    if not pending_list:
        raise HTTPException(status.HTTP_204_NO_CONTENT, "No pending requests yet")
    return pending_list
