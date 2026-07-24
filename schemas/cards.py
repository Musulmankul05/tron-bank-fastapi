from pydantic import Field, BaseModel
class CardCreate(BaseModel):
    owner_id: int = Field(..., gt=0, description="Cards owner ID")