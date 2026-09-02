from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, computed_field


class TransactionResponseSchema(BaseModel):
    sender_id: int
    receiver_id: int
    sent: Decimal = Field(..., gt=0)
    received: Decimal
    exchange_rate: Decimal
    fee: Decimal
    status: str
    created_at: datetime
    updated_at: datetime

    @computed_field
    def created_at_formatted(self) -> str:
        return self.created_at.strftime("%d.%m.%Y %H:%M")

    @computed_field
    def updated_at_formatted(self) -> str:
        return self.updated_at.strftime("%d.%m.%Y %H:%M")


class TransactionCreateSchema(BaseModel):
    sender_card_id: int
    receiver_card_id: int
    sent: Decimal = Field(..., gt=0)
