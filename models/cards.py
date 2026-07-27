import enum
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from models.users import UserModel


class Currencies_choice(str, enum.Enum):
    DOLLAR = "USD"
    EURO = "EUR"
    SOM = "KGS"


class CardModel(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    owner: Mapped["UserModel"] = relationship(back_populates="cards")
    currency: Mapped[Currencies_choice] = mapped_column(
        Enum(Currencies_choice), default=Currencies_choice.SOM
    )
    name: Mapped[str | None] = mapped_column(String(32), nullable=True)
    balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2), default=Decimal("0.00")
    )
    favorite: Mapped[bool] = mapped_column(Boolean, default=False)
