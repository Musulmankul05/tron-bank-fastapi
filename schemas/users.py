from datetime import date

from pydantic import BaseModel, EmailStr, Field

from models.users import AccountType_choice


class UserCreateSchema(BaseModel):
    username: str
    email: EmailStr | None = None
    password: str
    first_name: str
    last_name: str
    phone: str
    date_birth: date | None = None
    totp_secret: str | None = None
    country: str | None = None


class UserResponseSchema(BaseModel):
    id: int
    username: str
    email: EmailStr | None = None
    first_name: str
    last_name: str
    phone: str
    kyc_status: str

    model_config = {"from_attributes": True}


class UserLoginSchema(BaseModel):
    phone: str | None = None
    username: str | None = None
    password: str


class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TwoFARequiredSchema(BaseModel):
    status: str
    action: str


class KYCSchema(BaseModel):
    inn: int | None = Field(le=14)
    account_type: AccountType_choice
    passport_id: str | None
    signature: str | None

class BackupEnterSchema(BaseModel):
    code: str