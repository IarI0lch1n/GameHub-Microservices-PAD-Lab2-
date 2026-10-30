from shared.web.service_factory import (
    create_service_app,
)


SERVICE_NAME = "auth-service"


app = create_service_app(
    service_name=SERVICE_NAME,
    title="GameHub Auth Service",
    description=(
        "Authentication and authorization "
        "microservice for GameHub."
    ),
    version="0.1.0",
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
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
    }