from sqlalchemy import select

from sqlalchemy.orm import Session

from services.notification_service.app.models import (
    Notification,
)


class NotificationRepository:

    def __init__(
        self,
        session: Session,
    ) -> None:

        self.session = session

    def get_by_event_id(
        self,
        event_id: str,
    ) -> Notification | None:

        return (
            self.session.execute(
                select(
                    Notification
                ).where(
                    (
                        Notification
                        .source_event_id
                    )
                    == event_id
                )
            )
            .scalar_one_or_none()
        )

    def get_user_notification(
        self,
        *,
        notification_id: int,
        user_id: int,
    ) -> Notification | None:

        return (
            self.session.execute(
                select(
                    Notification
                ).where(
                    Notification.id
                    == notification_id,
                    Notification.user_id
                    == user_id,
                )
            )
            .scalar_one_or_none()
        )

    def list_user_notifications(
        self,
        *,
        user_id: int,
        unread_only: bool = False,
    ) -> list[Notification]:

        statement = (
            select(
                Notification
            )
            .where(
                Notification.user_id
                == user_id
            )
        )

        if unread_only:
            statement = (
                statement.where(
                    Notification.is_read
                    == False
                )
            )

        statement = (
            statement.order_by(
                Notification
                .created_at
                .desc()
            )
        )

        return list(
            self.session.execute(
                statement
            )
            .scalars()
            .all()
        )

    def create_notification(
        self,
        *,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        source_event_id: str,
    ) -> Notification:

        notification = Notification(
            user_id=user_id,
            notification_type=(
                notification_type
            ),
            title=title,
            message=message,
            source_event_id=(
                source_event_id
            ),
            is_read=False,
        )

        self.session.add(
            notification
        )

        self.session.commit()

        self.session.refresh(
            notification
        )

        return notification

    def mark_read(
        self,
        notification: Notification,
    ) -> Notification:

        notification.is_read = True

        self.session.commit()

        self.session.refresh(
            notification
        )

        return notification