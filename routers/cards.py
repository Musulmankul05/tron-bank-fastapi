from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from models import UserModel
from models.cards import CardModel, Currencies_choice
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
    count_query = select(func.count(CardModel.id)).where(
        CardModel.owner_id == current_user.id, CardModel.currency == payload.currency
    )
    result = await db.execute(count_query)
    existing_cards_count = result.scalar() or 0

    if payload.currency == Currencies_choice.SOM and existing_cards_count >= 2:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "You have a maximum cards of this currency"
        )
    if (
        payload.currency in (Currencies_choice.DOLLAR, Currencies_choice.EURO)
        and existing_cards_count >= 1
    ):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "You have a maximum cards of this currency"
        )

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
