from datetime import (
    date,
    datetime,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class GenreCreate(
    BaseModel
):
    name: str = Field(
        min_length=2,
        max_length=100,
    )


class GenreResponse(
    BaseModel
):
    id: int
    name: str
    slug: str

    model_config = ConfigDict(
        from_attributes=True
    )


class GameCreate(
    BaseModel
):
    title: str = Field(
        min_length=1,
        max_length=200,
    )

    description: (
        str
        | None
    ) = None

    price: float = Field(
        ge=0,
    )

    release_date: (
        date
        | None
    ) = None

    developer: (
        str
        | None
    ) = Field(
        default=None,
        max_length=150,
    )

    publisher: (
        str
        | None
    ) = Field(
        default=None,
        max_length=150,
    )

    is_published: bool = False

    genre_ids: list[int] = Field(
        default_factory=list
    )


class GameUpdate(
    BaseModel
):
    title: (
        str
        | None
    ) = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    description: (
        str
        | None
    ) = None

    price: (
        float
        | None
    ) = Field(
        default=None,
        ge=0,
    )

    release_date: (
        date
        | None
    ) = None

    developer: (
        str
        | None
    ) = Field(
        default=None,
        max_length=150,
    )

    publisher: (
        str
        | None
    ) = Field(
        default=None,
        max_length=150,
    )

    is_published: (
        bool
        | None
    ) = None

    genre_ids: (
        list[int]
        | None
    ) = None


class GameResponse(
    BaseModel
):
    id: int
    title: str
    slug: str

    description: (
        str
        | None
    )

    price: float

    release_date: (
        date
        | None
    )

    developer: (
        str
        | None
    )

    publisher: (
        str
        | None
    )

    is_published: bool

    genres: list[
        GenreResponse
    ]

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class InternalGameResponse(
    BaseModel
):
    id: int
    title: str
    price: float
    is_published: bool

    model_config = ConfigDict(
        from_attributes=True
    )