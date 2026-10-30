from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    String,
    Unicode,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from services.notification_service.app.database import (
    NotificationBase,
)


class Notification(
    NotificationBase
):
    __tablename__ = "notifications"

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

    notification_type: Mapped[
        str
    ] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        Unicode(200),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Unicode(500),
        nullable=False,
    )

    source_event_id: Mapped[
        str
    ] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    is_read: Mapped[
        bool
    ] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
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