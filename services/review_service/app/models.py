from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Integer,
    Unicode,
    UnicodeText,
    UniqueConstraint,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from services.review_service.app.database import (
    ReviewBase,
)


class Review(
    ReviewBase
):
    __tablename__ = "reviews"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "game_id",
            name="uq_reviews_user_game",
        ),
        CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_reviews_rating",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    game_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    game_title: Mapped[str] = mapped_column(
        Unicode(200),
        nullable=False,
    )

    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        UnicodeText,
        nullable=False,
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