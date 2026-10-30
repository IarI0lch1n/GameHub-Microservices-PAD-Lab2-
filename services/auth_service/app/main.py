from services.auth_service.app import (
    database as auth_database,
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


def initialize_auth_service() -> None:

    validate_security_configuration()

    auth_database.initialize_database()


app = create_service_app(
    service_name=SERVICE_NAME,
    title="GameHub Auth Service",
    description=(
        "Authentication and authorization "
        "microservice for GameHub."
    ),
    version="0.3.0",
    startup_handler=(
        initialize_auth_service
    ),
    shutdown_handler=(
        auth_database
        .shutdown_database
    ),
    readiness_check=(
        auth_database
        .readiness_check
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

        "version": "0.3.0",

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