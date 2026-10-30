from services.review_service.app import (
    database as review_database,
)

from services.review_service.app import (
    messaging as review_messaging,
)

from services.review_service.app.catalog_client import (
    catalog_client,
)

from services.review_service.app.router import (
    router,
)

from shared.web.service_factory import (
    create_service_app,
)


SERVICE_NAME = "review-service"


async def initialize_review_service() -> None:

    review_database.initialize_database()

    await catalog_client.connect()

    await (
        review_messaging
        .initialize_messaging()
    )


async def shutdown_review_service() -> None:

    await (
        review_messaging
        .shutdown_messaging()
    )

    await catalog_client.close()

    review_database.shutdown_database()


async def review_readiness_check() -> dict:

    checks = (
        review_database
        .readiness_check()
    )

    checks.update(
        await (
            review_messaging
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
    title="GameHub Review Service",
    description=(
        "Game ratings and reviews "
        "microservice for GameHub."
    ),
    version="0.1.0",
    startup_handler=(
        initialize_review_service
    ),
    shutdown_handler=(
        shutdown_review_service
    ),
    readiness_check=(
        review_readiness_check
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
            "GameHub Review Service"
        ),
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
    }