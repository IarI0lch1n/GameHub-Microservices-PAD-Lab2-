from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    Numeric,
    String,
    Unicode,
    UniqueConstraint,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from services.order_service.app.database import (
    OrderBase,
)


class Order(
    OrderBase
):
    __tablename__ = "orders"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "game_id",
            name="uq_orders_user_game",
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

    total_price: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            precision=10,
            scale=2,
        ),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="completed",
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