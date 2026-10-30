from services.user_service.app.database import (
    SessionLocal,
)

from services.user_service.app.repository import (
    UserProfileRepository,
)

from shared.config.settings import (
    settings,
)

from shared.logging.setup import (
    get_logger,
)

from shared.messaging.rabbitmq import (
    RabbitMQClient,
)


SERVICE_NAME = "user-service"

QUEUE_NAME = (
    "user-service.user-registered"
)


rabbitmq = RabbitMQClient(
    service_name=SERVICE_NAME
)


def _logger():
    return get_logger(
        SERVICE_NAME
    )


async def handle_user_registered(
    event: dict,
) -> None:
    """
    Handle user.registered events from
    Auth Service.
    """

    data = (
        event.get(
            "data"
        )
        or {}
    )

    auth_user_id = int(
        data[
            "user_id"
        ]
    )

    email = str(
        data[
            "email"
        ]
    )

    role = str(
        data.get(
            "role",
            "user",
        )
    )

    with SessionLocal() as session:
        repository = (
            UserProfileRepository(
                session
            )
        )

        existing = (
            repository
            .get_by_auth_user_id(
                auth_user_id
            )
        )

        if existing is not None:
            _logger().info(
                (
                    "user_profile_event_"
                    "already_processed"
                ),
                auth_user_id=(
                    auth_user_id
                ),
                event_id=(
                    event.get(
                        "event_id"
                    )
                ),
                correlation_id=(
                    event.get(
                        "correlation_id"
                    )
                ),
            )

            return

        profile = (
            repository
            .create_from_registration(
                auth_user_id=(
                    auth_user_id
                ),
                email=email,
                role=role,
            )
        )

        _logger().info(
            "user_profile_created",
            profile_id=(
                profile.id
            ),
            auth_user_id=(
                profile.auth_user_id
            ),
            email=(
                profile.email
            ),
            correlation_id=(
                event.get(
                    "correlation_id"
                )
            ),
        )


async def initialize_messaging(
) -> None:
    await rabbitmq.connect()

    await rabbitmq.consume(
        queue_name=QUEUE_NAME,
        routing_keys=[
            settings
            .event_user_registered
        ],
        handler=(
            handle_user_registered
        ),
    )


async def shutdown_messaging(
) -> None:
    await rabbitmq.close()


async def readiness_check(
) -> dict:
    return await (
        rabbitmq.readiness_check()
    )