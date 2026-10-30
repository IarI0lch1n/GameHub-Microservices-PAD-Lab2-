from services.auth_service.app.models import (
    User,
)

from shared.config.settings import (
    settings,
)

from shared.messaging.events import (
    create_event,
)

from shared.messaging.rabbitmq import (
    RabbitMQClient,
)


SERVICE_NAME = "auth-service"


rabbitmq = RabbitMQClient(
    service_name=SERVICE_NAME
)


async def initialize_messaging(
) -> None:
    await rabbitmq.connect()


async def shutdown_messaging(
) -> None:
    await rabbitmq.close()


async def readiness_check(
) -> dict:
    return await (
        rabbitmq.readiness_check()
    )


async def publish_user_registered(
    *,
    user: User,
    correlation_id: str,
) -> None:
    """
    Publish the user.registered domain
    event after successful registration.
    """

    event = create_event(
        event_type=(
            settings
            .event_user_registered
        ),
        correlation_id=(
            correlation_id
        ),
        data={
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
        },
    )

    await rabbitmq.publish(
        routing_key=(
            settings
            .event_user_registered
        ),
        event=(
            event.to_dict()
        ),
    )