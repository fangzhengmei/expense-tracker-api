from pydantic import BaseModel, Field, ConfigDict


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    icon: str | None = Field(default="📝", max_length=20)
    color: str | None = Field(default="#6B7280", max_length=7)


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    icon: str | None = Field(None, max_length=20)
    color: str | None = Field(None, max_length=7)


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    icon: str
    color: str
    is_default: bool
    user_id: int | None


class CategoryStats(BaseModel):
    category: CategoryOut
    total_amount: float
    expense_count: int
