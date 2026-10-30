from services.auth_service.app import (
    database as auth_database,
)

from services.auth_service.app import (
    messaging as auth_messaging,
)

from services.auth_service.app.router import (
    router as auth_router,
)

from services.auth_service.app.security import (
    validate_security_configuration,
)

from shared.web.service_factory import (
    create_service_app,
)


SERVICE_NAME = "auth-service"


async def initialize_auth_service(
) -> None:
    """
    Initialize infrastructure required by
    the Auth Service.
    """

    validate_security_configuration()

    auth_database.initialize_database()

    await (
        auth_messaging
        .initialize_messaging()
    )


async def shutdown_auth_service(
) -> None:
    """
    Gracefully close infrastructure
    connections.
    """

    await (
        auth_messaging
        .shutdown_messaging()
    )

    auth_database.shutdown_database()


async def auth_readiness_check(
) -> dict:
    """
    Auth Service is ready only when
    both MSSQL and RabbitMQ are ready.
    """

    checks = (
        auth_database
        .readiness_check()
    )

    checks.update(
        await (
            auth_messaging
            .readiness_check()
        )
    )

    return checks


app = create_service_app(
    service_name=SERVICE_NAME,
    title="GameHub Auth Service",
    description=(
        "Authentication and authorization "
        "microservice for GameHub."
    ),
    version="0.4.0",
    startup_handler=(
        initialize_auth_service
    ),
    shutdown_handler=(
        shutdown_auth_service
    ),
    readiness_check=(
        auth_readiness_check
    ),
)


app.include_router(
    auth_router
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
            "GameHub Auth Service"
        ),
        "version": "0.4.0",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
        "authentication": {
            "register": (
                "/api/auth/register"
            ),
            "login": (
                "/api/auth/login"
            ),
            "refresh": (
                "/api/auth/refresh"
            ),
            "me": (
                "/api/auth/me"
            ),
        },
    }