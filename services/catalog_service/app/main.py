from services.catalog_service.app import (
    database as catalog_database,
)

from services.catalog_service.app.router import (
    internal_router,
    router,
)

from shared.web.service_factory import (
    create_service_app,
)


SERVICE_NAME = "catalog-service"


def initialize_catalog_service(
) -> None:
    catalog_database.initialize_database()


def shutdown_catalog_service(
) -> None:
    catalog_database.shutdown_database()


def catalog_readiness_check(
) -> dict:
    return (
        catalog_database
        .readiness_check()
    )


app = create_service_app(
    service_name=SERVICE_NAME,
    title="GameHub Catalog Service",
    description=(
        "Game catalog and genres "
        "microservice for GameHub."
    ),
    version="0.1.0",
    startup_handler=(
        initialize_catalog_service
    ),
    shutdown_handler=(
        shutdown_catalog_service
    ),
    readiness_check=(
        catalog_readiness_check
    ),
)


app.include_router(
    router
)


app.include_router(
    internal_router
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
            "GameHub Catalog Service"
        ),
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
        "catalog": {
            "games": "/api/games",
            "genres": "/api/genres",
        },
    }