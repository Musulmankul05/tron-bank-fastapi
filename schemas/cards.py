from decimal import Decimal

from pydantic import BaseModel, Field

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

    model_config = {"from_attributes": True}
