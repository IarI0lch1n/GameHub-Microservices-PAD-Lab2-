from sqlalchemy import (
    select,
)

from sqlalchemy.orm import (
    Session,
)

from services.user_service.app.models import (
    UserProfile,
)


class UserProfileRepository:

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def get_by_auth_user_id(
        self,
        auth_user_id: int,
    ) -> UserProfile | None:
        return (
            self.session.execute(
                select(
                    UserProfile
                ).where(
                    (
                        UserProfile
                        .auth_user_id
                    )
                    == auth_user_id
                )
            )
            .scalar_one_or_none()
        )

    def create_from_registration(
        self,
        *,
        auth_user_id: int,
        email: str,
        role: str,
    ) -> UserProfile:
        """
        Create the user profile only if
        this Auth Service user has not
        already been processed.

        This makes event processing
        idempotent.
        """

        existing = (
            self.get_by_auth_user_id(
                auth_user_id
            )
        )

        if existing is not None:
            return existing

        profile = UserProfile(
            auth_user_id=(
                auth_user_id
            ),
            email=(
                email
                .strip()
                .lower()
            ),
            role=role,
        )

        self.session.add(
            profile
        )

        self.session.commit()

        self.session.refresh(
            profile
        )

        return profile