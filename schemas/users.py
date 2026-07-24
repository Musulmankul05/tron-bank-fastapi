from datetime import date
from pydantic import BaseModel, Field, EmailStr

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