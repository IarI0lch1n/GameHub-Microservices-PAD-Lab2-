from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class OrderCreate(
    BaseModel
):
    game_id: int = Field(
        gt=0
    )


class OrderResponse(
    BaseModel
):
    id: int
    user_id: int
    game_id: int
    game_title: str
    total_price: float
    status: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )