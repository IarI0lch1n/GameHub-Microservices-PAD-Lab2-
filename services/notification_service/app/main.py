from services.notification_service.app import (
    database as notification_database,
)

from services.notification_service.app import (
    messaging as notification_messaging,
)

from services.notification_service.app.router import (
    router,
)

from shared.web.service_factory import (
    create_service_app,
)


SERVICE_NAME = "notification-service"


async def initialize_notification_service(
) -> None:

    notification_database.initialize_database()

    await (
        notification_messaging
        .initialize_messaging()
    )


async def shutdown_notification_service(
) -> None:

    await (
        notification_messaging
        .shutdown_messaging()
    )

    notification_database.shutdown_database()


async def notification_readiness_check(
) -> dict:

    checks = (
        notification_database
        .readiness_check()
    )

    checks.update(
        await (
            notification_messaging
            .readiness_check()
        )
    )

    return checks


app = create_service_app(
    service_name=SERVICE_NAME,
    title="GameHub Notification Service",
    description=(
        "User notification microservice "
        "for GameHub."
    ),
    version="0.1.0",
    startup_handler=(
        initialize_notification_service
    ),
    shutdown_handler=(
        shutdown_notification_service
    ),
    readiness_check=(
        notification_readiness_check
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
            "GameHub Notification Service"
        ),
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
        "notifications": (
            "/api/notifications"
        ),
    }