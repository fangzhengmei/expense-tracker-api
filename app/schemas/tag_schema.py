from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern=r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', description="Hex color code like #FF5733")


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern=r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str
    user_id: int


class TagWithStats(TagOut):
    expense_count: int = 0
    total_amount: float = 0.0
