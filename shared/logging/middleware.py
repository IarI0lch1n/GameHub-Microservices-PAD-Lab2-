import time

from uuid import uuid4

from fastapi import Request

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

from shared.tracing.observability import (
    PARENT_SPAN_HEADER,
    TRACE_ID_HEADER,
    start_span,
    trace_context_from_headers,
)


class RequestContextMiddleware(
    BaseHTTPMiddleware
):

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

        trace_context = (
            trace_context_from_headers(
                request.headers
            )
        )

        started_at = (
            time.perf_counter()
        )

        self.logger.info(
            "request_started"
        )

        with start_span(
            name=(
                f"{self.service_name} "
                f"{request.method} "
                f"{request.url.path}"
            ),
            trace_context=(
                trace_context
            ),
            input_data={
                "method": (
                    request.method
                ),
                "path": (
                    request.url.path
                ),
                "query": str(
                    request.url.query
                ),
            },
            metadata={
                "service": (
                    self.service_name
                ),
                "request_id": (
                    request_id
                ),
                "correlation_id": (
                    correlation_id
                ),
            },
        ) as trace_span:

            if trace_span is not None:

                request.state.langfuse_trace_id = (
                    trace_span.trace_id
                )

                request.state.langfuse_span_id = (
                    trace_span.id
                )

            try:

                response = await call_next(
                    request
                )

            except Exception as exc:

                duration_ms = round(
                    (
                        time.perf_counter()
                        - started_at
                    )
                    * 1000,
                    2,
                )

                if trace_span is not None:

                    trace_span.update(
                        level="ERROR",
                        status_message=str(
                            exc
                        ),
                        metadata={
                            "duration_ms": (
                                duration_ms
                            ),
                        },
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

            if trace_span is not None:

                response.headers[
                    TRACE_ID_HEADER
                ] = trace_span.trace_id

                response.headers[
                    PARENT_SPAN_HEADER
                ] = trace_span.id

                trace_span.update(
                    output={
                        "status_code": (
                            response
                            .status_code
                        )
                    },
                    metadata={
                        "duration_ms": (
                            duration_ms
                        ),
                    },
                )

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