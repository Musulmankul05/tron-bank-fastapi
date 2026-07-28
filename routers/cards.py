from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from models import UserModel
from models.cards import CardModel
from schemas.cards import CardCreateSchema, CardResponseSchema
from utils.dependencies import get_current_user

router = APIRouter(prefix="/cards", tags=["Cards"])


@router.post(
    "/new", response_model=CardResponseSchema, status_code=status.HTTP_201_CREATED
)
async def new_card(
    payload: CardCreateSchema,
    db: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    card_name = (
        payload.name.strip() if payload.name else f"Карта {payload.currency.value}"
    )
    card = CardModel(
        owner_id=current_user.id,
        name=card_name,
        currency=payload.currency,
    )
    db.add(card)
    await db.commit()
    await db.refresh(card)
    return card


@router.get("/my-cards", response_model=list[CardResponseSchema])
async def get_my_cards(
    db: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    query = select(CardModel).where(CardModel.owner_id == current_user.id)
    result = await db.execute(query)
    card = result.scalars().all()
    return card
