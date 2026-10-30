from services.notification_service.app.database import (
    SessionLocal,
)

from services.notification_service.app.repository import (
    NotificationRepository,
)

from shared.config.settings import settings

from shared.logging.setup import get_logger

from shared.messaging.rabbitmq import (
    RabbitMQClient,
)


SERVICE_NAME = "notification-service"

QUEUE_NAME = (
    "notification-service.events"
)


rabbitmq = RabbitMQClient(
    service_name=SERVICE_NAME
)


def _logger():
    return get_logger(
        SERVICE_NAME
    )


async def handle_event(
    event: dict,
) -> None:

    event_id = str(
        event["event_id"]
    )

    event_type = str(
        event["event_type"]
    )

    data = (
        event.get("data")
        or {}
    )

    with SessionLocal() as session:

        repository = (
            NotificationRepository(
                session
            )
        )

        existing = (
            repository.get_by_event_id(
                event_id
            )
        )

        if existing is not None:
            _logger().info(
                (
                    "notification_event_"
                    "already_processed"
                ),
                event_id=event_id,
                event_type=event_type,
            )

            return

        if (
            event_type
            == settings
            .event_order_completed
        ):
            user_id = int(
                data["user_id"]
            )

            game_title = str(
                data["game_title"]
            )

            notification_type = (
                "purchase_completed"
            )

            title = (
                "Purchase completed"
            )

            message = (
                f"{game_title} was added "
                "to your GameHub library."
            )

        elif (
            event_type
            == settings
            .event_review_created
        ):
            user_id = int(
                data["user_id"]
            )

            game_title = str(
                data["game_title"]
            )

            rating = int(
                data["rating"]
            )

            notification_type = (
                "review_published"
            )

            title = "Review published"

            message = (
                f"Your {rating}/5 review "
                f"for {game_title} "
                "was published."
            )

        else:
            _logger().warning(
                "unsupported_notification_event",
                event_id=event_id,
                event_type=event_type,
            )

            return

        notification = (
            repository
            .create_notification(
                user_id=user_id,
                notification_type=(
                    notification_type
                ),
                title=title,
                message=message,
                source_event_id=event_id,
            )
        )

        _logger().info(
            "notification_created",
            notification_id=(
                notification.id
            ),
            user_id=user_id,
            notification_type=(
                notification_type
            ),
            event_id=event_id,
            correlation_id=(
                event.get(
                    "correlation_id"
                )
            ),
        )


async def initialize_messaging() -> None:

    await rabbitmq.connect()

    await rabbitmq.consume(
        queue_name=QUEUE_NAME,
        routing_keys=[
            settings
            .event_order_completed,

            settings
            .event_review_created,
        ],
        handler=handle_event,
    )


async def shutdown_messaging() -> None:

    await rabbitmq.close()


async def readiness_check() -> dict:

    return await (
        rabbitmq.readiness_check()
    )