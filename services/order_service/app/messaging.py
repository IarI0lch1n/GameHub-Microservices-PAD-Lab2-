from services.order_service.app.models import (
    Order,
)

from shared.config.settings import settings

from shared.messaging.events import (
    create_event,
)

from shared.messaging.rabbitmq import (
    RabbitMQClient,
)


SERVICE_NAME = "order-service"


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


async def publish_order_completed(
    *,
    order: Order,
    correlation_id: str,
) -> None:

    event = create_event(
        event_type=(
            settings
            .event_order_completed
        ),
        correlation_id=(
            correlation_id
        ),
        data={
            "order_id": order.id,
            "user_id": order.user_id,
            "game_id": order.game_id,
            "game_title": (
                order.game_title
            ),
            "price": str(
                order.total_price
            ),
        },
    )

    await rabbitmq.publish(
        routing_key=(
            settings
            .event_order_completed
        ),
        event=(
            event.to_dict()
        ),
    )