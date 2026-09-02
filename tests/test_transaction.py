from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.cards import CardModel, Currencies_choice
from models.transactions import TransactionModel
from models.users import KYCStatus_choice, UserModel
from utils.security import auth, hash_password


@pytest.mark.asyncio
async def test_transfer_success(client: AsyncClient, db_session: AsyncSession, mock_rabbitmq):
    test_sender = UserModel(
        first_name="Sender",
        last_name="User",
        username="sender_user",
        phone="+996555123456",
        hashed_password=hash_password("sender123"),
        kyc_status=KYCStatus_choice.VERIFIED,
    )
    test_receiver = UserModel(
        first_name="Receiver",
        last_name="User",
        username="receiver_user",
        phone="+996555654321",
        hashed_password=hash_password("receiver123"),
        kyc_status=KYCStatus_choice.VERIFIED,
    )
    db_session.add(test_receiver)
    db_session.add(test_sender)
    await db_session.flush()

    test_receiver_card = CardModel(
        owner_id=test_receiver.id,
        currency=Currencies_choice.EURO,
        name="My EURO card",
        balance=Decimal("0.00"),
    )
    test_sender_card = CardModel(
        owner_id=test_sender.id,
        currency=Currencies_choice.SOM,
        name="My SOM card",
        balance=Decimal("1000.00"),
    )
    db_session.add(test_sender_card)
    db_session.add(test_receiver_card)

    await db_session.commit()

    token = auth.create_access_token(uid=str(test_sender.id))
    cookies = {"auth_access_token": token}

    client.cookies = cookies
    response = await client.post(
        "/api/v1/transactions/transfer",
        json={
            "sender_card_id": 1,
            "receiver_card_id": 2,
            "sent": "-50.00",
        }
    )
    assert response.status_code == 422

    mock_rabbitmq.assert_not_called()
    await db_session.refresh(test_sender_card)

    assert test_sender_card.balance == Decimal("1000.00")
