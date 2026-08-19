from pydantic import BaseModel


class KYCPendingSchema(BaseModel):
    id: int
    user_id: int
    inn: int
    passport_id: str
    account_type: str

    model_config = {"from_attributes": True}
    