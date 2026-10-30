from services.review_service.app.models import (
    Review,
)

from shared.config.settings import settings

from shared.messaging.events import (
    create_event,
)

from shared.messaging.rabbitmq import (
    RabbitMQClient,
)


SERVICE_NAME = "review-service"


rabbitmq = RabbitMQClient(
    service_name=SERVICE_NAME
)


async def initialize_messaging() -> None:

    await rabbitmq.connect()


async def shutdown_messaging() -> None:

    await rabbitmq.close()


async def readiness_check() -> dict:

    return await (
        rabbitmq.readiness_check()
    )


async def publish_review_created(
    *,
    review: Review,
    correlation_id: str,
) -> None:

    event = create_event(
        event_type=(
            settings
            .event_review_created
        ),
        correlation_id=(
            correlation_id
        ),
        data={
            "review_id": review.id,
            "user_id": review.user_id,
            "game_id": review.game_id,
            "game_title": (
                review.game_title
            ),
            "rating": review.rating,
        },
    )

    await rabbitmq.publish(
        routing_key=(
            settings.event_review_created
        ),
        event=(
            event.to_dict()
        ),
    )