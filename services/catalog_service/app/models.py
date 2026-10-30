from datetime import (
    date,
    datetime,
)

from decimal import (
    Decimal,
)

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Table,
    Unicode,
    UnicodeText,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from services.catalog_service.app.database import (
    CatalogBase,
)


game_genres = Table(
    "game_genres",
    CatalogBase.metadata,

    Column(
        "game_id",
        BigInteger,
        ForeignKey(
            "games.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),

    Column(
        "genre_id",
        BigInteger,
        ForeignKey(
            "genres.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
)


class Genre(
    CatalogBase
):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        Unicode(100),
        unique=True,
        nullable=False,
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        nullable=False,
        index=True,
    )

    games: Mapped[
        list["Game"]
    ] = relationship(
        secondary=game_genres,
        back_populates="genres",
    )


class Game(
    CatalogBase
):
    __tablename__ = "games"

    __table_args__ = (
        CheckConstraint(
            "price >= 0",
            name=(
                "ck_games_price_nonnegative"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    title: Mapped[str] = mapped_column(
        Unicode(200),
        nullable=False,
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(220),
        unique=True,
        nullable=False,
        index=True,
    )

    description: Mapped[
        str | None
    ] = mapped_column(
        UnicodeText,
        nullable=True,
    )

    price: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            precision=10,
            scale=2,
        ),
        nullable=False,
        default=Decimal("0.00"),
    )

    release_date: Mapped[
        date | None
    ] = mapped_column(
        Date,
        nullable=True,
    )

    developer: Mapped[
        str | None
    ] = mapped_column(
        Unicode(150),
        nullable=True,
    )

    publisher: Mapped[
        str | None
    ] = mapped_column(
        Unicode(150),
        nullable=True,
    )

    is_published: Mapped[
        bool
    ] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    genres: Mapped[
        list[Genre]
    ] = relationship(
        secondary=game_genres,
        back_populates="games",
        lazy="selectin",
    )

    created_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=False,
        server_default=(
            func.sysdatetimeoffset()
        ),
    )

    updated_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=False,
        server_default=(
            func.sysdatetimeoffset()
        ),
        onupdate=(
            func.sysdatetimeoffset()
        ),
    )