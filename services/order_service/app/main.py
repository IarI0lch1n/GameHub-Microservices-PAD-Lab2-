from services.order_service.app import (
    database as order_database,
)

from services.order_service.app import (
    messaging as order_messaging,
)

from services.order_service.app.catalog_client import (
    catalog_client,
)

from services.order_service.app.router import (
    router,
)

from shared.web.service_factory import (
    create_service_app,
)


SERVICE_NAME = "order-service"


async def initialize_order_service() -> None:

    order_database.initialize_database()

    await catalog_client.connect()

    await (
        order_messaging
        .initialize_messaging()
    )


async def shutdown_order_service() -> None:

    await (
        order_messaging
        .shutdown_messaging()
    )

    await catalog_client.close()

    order_database.shutdown_database()


async def order_readiness_check() -> dict:

    checks = (
        order_database
        .readiness_check()
    )

    checks.update(
        await (
            order_messaging
            .readiness_check()
        )
    )

    checks.update(
        await (
            catalog_client
            .readiness_check()
        )
    )

    return checks


app = create_service_app(
    service_name=SERVICE_NAME,
    title="GameHub Order Service",
    description=(
        "Game purchase and order "
        "microservice for GameHub."
    ),
    version="0.1.0",
    startup_handler=(
        initialize_order_service
    ),
    shutdown_handler=(
        shutdown_order_service
    ),
    readiness_check=(
        order_readiness_check
    ),
)


app.include_router(
    router
)


@app.get(
    "/",
    include_in_schema=False,
)
async def root():

    return {
        "service": SERVICE_NAME,
        "message": (
            "GameHub Order Service"
        ),
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
        "orders": "/api/orders",
    }