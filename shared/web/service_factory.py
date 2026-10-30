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


async def _run_callback(
    callback: (
        Callable
        | None
    ),
):
    if callback is None:
        return None

    result = callback()

    if inspect.isawaitable(
        result
    ):
        return await result

    return result


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
    startup_handler: (
        Callable
        | None
    ) = None,
    shutdown_handler: (
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
    - lifespan handling.
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
            "service_starting",
            environment=(
                settings.app_env
            ),
            version=version,
        )

        await _run_callback(
            startup_handler
        )

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
                "service_stopping"
            )

            await _run_callback(
                shutdown_handler
            )

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

        if readiness_check is None:

            return {
                "status": "ready",
                "service": (
                    service_name
                ),
                "checks": {},
            }

        try:

            result = await (
                _run_callback(
                    readiness_check
                )
            )

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