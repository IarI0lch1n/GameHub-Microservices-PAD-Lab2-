from services.user_service.app import (
    database as user_database,
)

from services.user_service.app import (
    messaging as user_messaging,
)

from services.user_service.app.router import (
    router as user_router,
)

from shared.web.service_factory import (
    create_service_app,
)


SERVICE_NAME = "user-service"


async def initialize_user_service(
) -> None:
    user_database.initialize_database()

    await (
        user_messaging
        .initialize_messaging()
    )


async def shutdown_user_service(
) -> None:
    await (
        user_messaging
        .shutdown_messaging()
    )

    user_database.shutdown_database()


async def user_readiness_check(
) -> dict:
    checks = (
        user_database
        .readiness_check()
    )

    checks.update(
        await (
            user_messaging
            .readiness_check()
        )
    )

    return checks


app = create_service_app(
    service_name=SERVICE_NAME,
    title="GameHub User Service",
    description=(
        "User profile microservice "
        "for GameHub."
    ),
    version="0.1.0",
    startup_handler=(
        initialize_user_service
    ),
    shutdown_handler=(
        shutdown_user_service
    ),
    readiness_check=(
        user_readiness_check
    ),
)


app.include_router(
    user_router
)


@app.get(
    "/",
    include_in_schema=False,
)
async def root():
    return {
        "service": (
            SERVICE_NAME
        ),
        "message": (
            "GameHub User Service"
        ),
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
    }