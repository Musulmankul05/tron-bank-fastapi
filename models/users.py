import enum
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class KYCStatus_choice(str, enum.Enum):
    PENDING = "PEN"
    UNVERIFIED = "UNV"
    VERIFIED = "VER"
    REJECTED = "REJ"


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(60), nullable=False)
    last_name: Mapped[str] = mapped_column(String(60), nullable=False)
    username: Mapped[str] = mapped_column(String(30), unique=True)
    email: Mapped[str | None] = mapped_column(String(80), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    kyc_status: Mapped[KYCStatus_choice] = mapped_column(
        Enum(KYCStatus_choice, name="kycstatus"),
        default=KYCStatus_choice.UNVERIFIED,
        nullable=False,
    )
    date_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    phone: Mapped[str] = mapped_column(String(24), unique=True)
    is_phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_2fa_enabled: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    totp_secret: Mapped[str | None] = mapped_column(String(32), nullable=True)
    country: Mapped[str | None] = mapped_column(String(30), nullable=True)
    
    cards: Mapped[list["CardModel"]] = relationship(back_populates="owner")
    backups: Mapped["BackupCodesModel"] = relationship(back_populates="user_backups")
    kyc: Mapped["KYCModel"] = relationship(back_populates="user")


class BackupCodesModel(Base):
    __tablename__ = "backup_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user_backups: Mapped["UserModel"] = relationship(back_populates="backups")
    code: Mapped[str | None] = mapped_column(String(128), nullable=True)


class AccountType_choice(str, enum.Enum):
    PRIVATE = "STANDART"
    CORPORATE = "BUSINESS"


class KYCModel(Base):
    __tablename__ = "kyc_model"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    user: Mapped["UserModel"] = relationship(back_populates="kyc")
    inn: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    passport_id: Mapped[str | None] = mapped_column(String, nullable=True)
    account_type: Mapped[AccountType_choice] = mapped_column(
        Enum(AccountType_choice), default=AccountType_choice.PRIVATE
    )
    signature: Mapped[str | None] = mapped_column(String, nullable=True)
