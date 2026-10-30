import time
from uuid import uuid4

from fastapi import (
    Request,
)

from starlette.middleware.base import (
    BaseHTTPMiddleware,
)

from structlog.contextvars import (
    bind_contextvars,
    clear_contextvars,
)

from shared.config.settings import (
    settings,
)

from shared.logging.setup import (
    get_logger,
)


class RequestContextMiddleware(
    BaseHTTPMiddleware
):
    """
    Adds request and correlation IDs
    to every HTTP request.

    These IDs will later be propagated
    between microservices and RabbitMQ.
    """

    def __init__(
        self,
        app,
        service_name: str,
    ) -> None:

        super().__init__(
            app
        )

        self.service_name = (
            service_name
        )

        self.logger = get_logger(
            service_name
        )

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        clear_contextvars()

        request_id = (
            request.headers.get(
                settings.request_id_header
            )
            or str(
                uuid4()
            )
        )

        correlation_id = (
            request.headers.get(
                settings
                .correlation_id_header
            )
            or request_id
        )

        request.state.request_id = (
            request_id
        )

        request.state.correlation_id = (
            correlation_id
        )

        bind_contextvars(
            service=(
                self.service_name
            ),
            request_id=request_id,
            correlation_id=(
                correlation_id
            ),
            method=request.method,
            path=request.url.path,
        )

        started_at = (
            time.perf_counter()
        )

        self.logger.info(
            "request_started"
        )

        try:
            response = await call_next(
                request
            )

        except Exception:
            duration_ms = round(
                (
                    time.perf_counter()
                    - started_at
                )
                * 1000,
                2,
            )

            self.logger.exception(
                "request_failed",
                duration_ms=(
                    duration_ms
                ),
            )

            raise

        duration_ms = round(
            (
                time.perf_counter()
                - started_at
            )
            * 1000,
            2,
        )

        response.headers[
            settings.request_id_header
        ] = request_id

        response.headers[
            settings
            .correlation_id_header
        ] = correlation_id

        self.logger.info(
            "request_completed",
            status_code=(
                response.status_code
            ),
            duration_ms=(
                duration_ms
            ),
        )

        clear_contextvars()

        return response