from services.library_service.app import (
    database as library_database,
)

from services.library_service.app import (
    messaging as library_messaging,
)

from services.library_service.app.router import (
    router,
)

from shared.web.service_factory import (
    create_service_app,
)


SERVICE_NAME = "library-service"


async def initialize_library_service() -> None:

    library_database.initialize_database()

    await (
        library_messaging
        .initialize_messaging()
    )


async def shutdown_library_service() -> None:

    await (
        library_messaging
        .shutdown_messaging()
    )

    library_database.shutdown_database()


async def library_readiness_check() -> dict:

    checks = (
        library_database
        .readiness_check()
    )

    checks.update(
        await (
            library_messaging
            .readiness_check()
        )
    )

    return checks


app = create_service_app(
    service_name=SERVICE_NAME,
    title="GameHub Library Service",
    description=(
        "Purchased game library "
        "microservice for GameHub."
    ),
    version="0.1.0",
    startup_handler=(
        initialize_library_service
    ),
    shutdown_handler=(
        shutdown_library_service
    ),
    readiness_check=(
        library_readiness_check
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
            "GameHub Library Service"
        ),
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
        "library": "/api/library",
    }