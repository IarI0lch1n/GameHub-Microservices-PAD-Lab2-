from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
)


class LibraryItemResponse(
    BaseModel
):
    id: int
    user_id: int
    game_id: int
    order_id: int
    game_title: str
    purchase_price: float
    acquired_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )