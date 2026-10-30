from contextlib import (
    asynccontextmanager,
)

import inspect

from collections.abc import (
    Callable,
)

from fastapi import (
    FastAPI,
)

from fastapi.responses import (
    JSONResponse,
)

from shared.config.settings import (
    settings,
)

from shared.logging.middleware import (
    RequestContextMiddleware,
)

from shared.logging.setup import (
    configure_logging,
    get_logger,
)


def create_service_app(
    *,
    service_name: str,
    title: str,
    description: str,
    version: str = "0.1.0",
    readiness_check: (
        Callable
        | None
    ) = None,
) -> FastAPI:
    """
    Create a standard GameHub FastAPI service.

    Every service receives:
    - structured logging;
    - request/correlation IDs;
    - Swagger/OpenAPI;
    - /health;
    - /ready;
    - lifespan startup/shutdown logging.
    """

    configure_logging(
        service_name
    )

    logger = get_logger(
        service_name
    )

    @asynccontextmanager
    async def lifespan(
        app: FastAPI,
    ):
        logger.info(
            "service_started",
            environment=(
                settings.app_env
            ),
            version=version,
        )

        try:
            yield

        finally:
            logger.info(
                "service_stopped"
            )

    app = FastAPI(
        title=title,
        description=description,
        version=version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.state.service_name = (
        service_name
    )

    app.add_middleware(
        RequestContextMiddleware,
        service_name=(
            service_name
        ),
    )

    @app.get(
        "/health",
        tags=[
            "Infrastructure",
        ],
        summary=(
            "Liveness health check"
        ),
    )
    async def health():
        """
        Kubernetes-style liveness endpoint.

        It only confirms that the FastAPI
        process itself is alive.
        """

        return {
            "status": "healthy",
            "service": (
                service_name
            ),
            "environment": (
                settings.app_env
            ),
            "version": version,
        }

    @app.get(
        "/ready",
        tags=[
            "Infrastructure",
        ],
        summary=(
            "Readiness health check"
        ),
    )
    async def ready():
        """
        Kubernetes-style readiness endpoint.

        Individual services can provide
        additional infrastructure checks,
        for example MSSQL or RabbitMQ.
        """

        if readiness_check is None:

            return {
                "status": "ready",
                "service": (
                    service_name
                ),
                "checks": {},
            }

        try:
            result = (
                readiness_check()
            )

            if inspect.isawaitable(
                result
            ):
                result = await result

            return {
                "status": "ready",
                "service": (
                    service_name
                ),
                "checks": (
                    result
                    or {}
                ),
            }

        except Exception as exc:

            logger.exception(
                "readiness_check_failed"
            )

            return JSONResponse(
                status_code=503,
                content={
                    "status": (
                        "not_ready"
                    ),
                    "service": (
                        service_name
                    ),
                    "error": str(
                        exc
                    ),
                },
            )

    return app