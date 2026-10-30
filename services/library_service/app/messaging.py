from decimal import Decimal

from services.library_service.app.database import (
    SessionLocal,
)

from services.library_service.app.repository import (
    LibraryRepository,
)

from shared.config.settings import settings

from shared.logging.setup import get_logger

from shared.messaging.rabbitmq import (
    RabbitMQClient,
)


SERVICE_NAME = "library-service"

QUEUE_NAME = (
    "library-service.order-completed"
)


rabbitmq = RabbitMQClient(
    service_name=SERVICE_NAME
)


def _logger():
    return get_logger(
        SERVICE_NAME
    )


async def handle_order_completed(
    event: dict,
) -> None:

    data = (
        event.get("data")
        or {}
    )

    order_id = int(
        data["order_id"]
    )

    user_id = int(
        data["user_id"]
    )

    game_id = int(
        data["game_id"]
    )

    game_title = str(
        data["game_title"]
    )

    price = Decimal(
        str(
            data["price"]
        )
    )

    with SessionLocal() as session:

        repository = LibraryRepository(
            session
        )

        existing_order = (
            repository
            .get_by_order_id(
                order_id
            )
        )

        if existing_order is not None:

            _logger().info(
                (
                    "order_event_"
                    "already_processed"
                ),
                order_id=order_id,
                event_id=(
                    event.get(
                        "event_id"
                    )
                ),
            )

            return

        existing_game = (
            repository.get_user_game(
                user_id=user_id,
                game_id=game_id,
            )
        )

        if existing_game is not None:

            _logger().info(
                (
                    "library_game_"
                    "already_exists"
                ),
                user_id=user_id,
                game_id=game_id,
            )

            return

        item = repository.create_item(
            user_id=user_id,
            game_id=game_id,
            order_id=order_id,
            game_title=game_title,
            purchase_price=price,
        )

        _logger().info(
            "library_item_created",
            library_item_id=item.id,
            order_id=order_id,
            user_id=user_id,
            game_id=game_id,
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
            .event_order_completed
        ],
        handler=(
            handle_order_completed
        ),
    )


async def shutdown_messaging() -> None:

    await rabbitmq.close()


async def readiness_check() -> dict:

    return await (
        rabbitmq.readiness_check()
    )