from sqlalchemy import (
    select,
)

from sqlalchemy.orm import (
    Session,
)

from services.auth_service.app.models import (
    User,
)


class UserRepository:

    def __init__(
        self,
        session: Session,
    ) -> None:

        self.session = session

    def get_by_id(
        self,
        user_id: int,
    ) -> User | None:

        return (
            self.session.execute(
                select(
                    User
                ).where(
                    User.id
                    == user_id
                )
            )
            .scalar_one_or_none()
        )

    def get_by_email(
        self,
        email: str,
    ) -> User | None:

        normalized_email = (
            email.strip().lower()
        )

        return (
            self.session.execute(
                select(
                    User
                ).where(
                    User.email
                    == normalized_email
                )
            )
            .scalar_one_or_none()
        )

    def create(
        self,
        *,
        email: str,
        password_hash: str,
        role: str = "user",
    ) -> User:

        user = User(
            email=(
                email
                .strip()
                .lower()
            ),
            password_hash=(
                password_hash
            ),
            role=role,
            is_active=True,
        )

        self.session.add(
            user
        )

        self.session.commit()

        self.session.refresh(
            user
        )

        return user