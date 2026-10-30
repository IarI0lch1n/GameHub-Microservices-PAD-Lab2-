from datetime import (
    datetime,
)

from sqlalchemy import (
    BigInteger,
    DateTime,
    String,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from services.user_service.app.database import (
    UserBase,
)


class UserProfile(
    UserBase
):
    __tablename__ = (
        "user_profiles"
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    auth_user_id: Mapped[int] = (
        mapped_column(
            BigInteger,
            unique=True,
            nullable=False,
            index=True,
        )
    )

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    display_name: Mapped[
        str | None
    ] = mapped_column(
        String(100),
        nullable=True,
    )

    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="user",
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