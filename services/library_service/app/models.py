from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    Numeric,
    Unicode,
    UniqueConstraint,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from services.library_service.app.database import (
    LibraryBase,
)


class LibraryItem(
    LibraryBase
):
    __tablename__ = "library_items"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "game_id",
            name="uq_library_user_game",
        ),
        UniqueConstraint(
            "order_id",
            name="uq_library_order",
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

    order_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    game_title: Mapped[str] = mapped_column(
        Unicode(200),
        nullable=False,
    )

    purchase_price: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            precision=10,
            scale=2,
        ),
        nullable=False,
    )

    acquired_at: Mapped[
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