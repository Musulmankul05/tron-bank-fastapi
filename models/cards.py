import enum
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import Boolean, Enum, ForeignKey, Numeric, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from models.users import UserModel


class Currencies_choice(str, enum.Enum):
    DOLLAR = "USD"
    EURO = "EUR"
    SOM = "KGS"


def default_expiration_date() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=365 * 5)


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
    expiration_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=default_expiration_date
    )
