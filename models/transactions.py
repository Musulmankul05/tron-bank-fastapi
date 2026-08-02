import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, LargeBinary, Numeric, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class TransactionStatus_choices(str, enum.Enum):
    PENDING = "PEN"
    COMPLETED = "COM"
    REJECTED = "REJ"
    FAILED = "ERR"


class TransactionModel(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("cards.id", ondelete="CASCADE"))
    sender: Mapped["CardModel"] = relationship(back_populates="sent", foreign_keys=[sender_id])
    receiver_id: Mapped[int] = mapped_column(ForeignKey("cards.id", ondelete="CASCADE"))
    receiver: Mapped["CardModel"] = relationship(back_populates="received", foreign_keys=[receiver_id])

    sent: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=2))
    received: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=2))
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=2))
    reference: Mapped[uuid.UUID] = mapped_column(Uuid, default=uuid.uuid4, unique=True)
    fee: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=2))
    encryption: Mapped[bytes] = mapped_column(LargeBinary)
    status: Mapped[TransactionStatus_choices] = mapped_column(
        Enum(TransactionStatus_choices), default=TransactionStatus_choices.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), server_onupdate=func.now()
    )
