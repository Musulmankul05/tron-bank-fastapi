from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_session
from models import UserModel
from models.cards import CardModel, Currencies_choice
from models.transactions import TransactionModel, TransactionStatus_choices
from schemas.transactions import TransactionCreateSchema, TransactionResponseSchema
from utils.dependencies import get_current_user
from utils.security import decrypt_data, encrypt_data

router = APIRouter(prefix="/transactions", tags=["Transactions"])

EXCHANGE_RATES = {
    (Currencies_choice.SOM, Currencies_choice.DOLLAR): Decimal("0.011"),
    (Currencies_choice.DOLLAR, Currencies_choice.SOM): Decimal("87.50"),
}


def calculate_exchanged(
    sender_currency, receiver_currency, amount: Decimal
) -> tuple[Decimal, Decimal]:
    if sender_currency == receiver_currency:
        return amount, Decimal("1.0000")
    rate_key = (sender_currency, receiver_currency)
    if rate_key not in EXCHANGE_RATES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Converting from {sender_currency.value} to {receiver_currency.value} is not available",
        )
    rate = EXCHANGE_RATES[rate_key]
    received = (amount * rate).quantize(Decimal("0.01"))
    return received, rate


@router.post(
    "/transfer",
    response_model=TransactionResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def transfer(
    payload: TransactionCreateSchema,
    db: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    if payload.sender_card_id == payload.receiver_card_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Wrong Card")
    card_ids = sorted([payload.sender_card_id, payload.receiver_card_id])
    query = select(CardModel).where(CardModel.id.in_(card_ids)).with_for_update()
    result = await db.execute(query)
    cards = result.scalars().all()
    sender_card = next((c for c in cards if c.id == payload.sender_card_id), None)
    fee = Decimal("1.02")
    if not sender_card:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sender card not found")
    if sender_card.owner_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Card is not yours")
    if sender_card.balance < payload.sent * fee:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Insufficient balance")
    receiver_card = next((c for c in cards if c.id == payload.receiver_card_id), None)
    if not receiver_card:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Receiver card not found")
    sent = payload.sent
    received, rate = calculate_exchanged(
        sender_currency=sender_card.currency,
        receiver_currency=receiver_card.currency,
        amount=sent,
    )

    payload_to_encrypt = {
        "sender_id": sender_card.id,
        "receiver_id": receiver_card.id,
        "amount": str(sent),
        "timestamp": str(datetime.now()),
    }

    transaction = TransactionModel(
        sender_id=sender_card.id,
        receiver_id=receiver_card.id,
        sent=sent * fee,
        received=received,
        fee=fee,
        exchange_rate=rate,
        encryption=encrypt_data(payload_to_encrypt),
    )
    db.add(transaction)
    await db.commit()
    print(transaction.status)
    try:
        sender_card.balance -= sent * fee
        receiver_card.balance += received
        transaction.status = TransactionStatus_choices.COMPLETED
        await db.commit()
        await db.refresh(transaction)
        return transaction
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transaction failed",
        )


@router.get(
    "/get-transactions",
    response_model=list[TransactionResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_transactions(
    limit: int = 20,
    offset: int = 0,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    cards_query = select(CardModel.id).where(CardModel.owner_id == current_user.id)
    query = (
        select(TransactionModel)
        .where(
            or_(
                TransactionModel.sender_id.in_(cards_query),
                TransactionModel.receiver_id.in_(cards_query),
            )
        )
        .order_by(TransactionModel.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    transactions = result.scalars().all()
    return transactions


@router.get("/transactions/{tx_id}")
async def transaction(
    tx_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    query = (
        select(TransactionModel)
        .where(TransactionModel.id == tx_id)
        .options(
            joinedload(TransactionModel.sender), joinedload(TransactionModel.receiver)
        )
    )
    result = await db.execute(query)
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")
    if (
        tx.sender.owner_id != current_user.id
        and tx.receiver.owner_id != current_user.id
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Wrong transaction page")
    decrypted_tx: dict = decrypt_data(tx.encryption)
    return {
        "id": tx.id,
        "status": tx.status,
        "sent": tx.sent,
        "received": tx.received,
        "fee": tx.fee,
        "created_at": tx.created_at,
        "payload": decrypted_tx
    }
