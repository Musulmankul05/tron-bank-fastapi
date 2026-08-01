from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, computed_field

from models.cards import Currencies_choice


class CardCreateSchema(BaseModel):
    currency: Currencies_choice = Field(default=Currencies_choice.SOM)
    name: str | None = Field(default=None, max_length=32)


class CardResponseSchema(BaseModel):
    id: int
    owner_id: int
    currency: Currencies_choice
    balance: Decimal
    name: str | None = None
    favorite: bool
    created_at: datetime
    expiration_date: datetime

    @computed_field
    def expiration_date_formatted(self) -> str:
        return self.expiration_date.strftime("%m/%y")

    model_config = {"from_attributes": True}
