from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class ReviewCreate(
    BaseModel
):
    rating: int = Field(
        ge=1,
        le=5,
    )

    content: str = Field(
        min_length=3,
        max_length=4000,
    )


class ReviewUpdate(
    BaseModel
):
    rating: (
        int
        | None
    ) = Field(
        default=None,
        ge=1,
        le=5,
    )

    content: (
        str
        | None
    ) = Field(
        default=None,
        min_length=3,
        max_length=4000,
    )


class ReviewResponse(
    BaseModel
):
    id: int
    user_id: int
    game_id: int
    game_title: str
    rating: int
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )