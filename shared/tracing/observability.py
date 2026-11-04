import logging
import re

from contextlib import (
    contextmanager,
)

from threading import (
    Lock,
)

from langfuse import Langfuse

from shared.config.settings import (
    settings,
)


TRACE_ID_HEADER = (
    "X-Langfuse-Trace-ID"
)

PARENT_SPAN_HEADER = (
    "X-Langfuse-Parent-Span-ID"
)


_logger = logging.getLogger(
    __name__
)


_client: (
    Langfuse
    | None
) = None


_client_lock = Lock()


TRACE_ID_PATTERN = re.compile(
    r"^[0-9a-f]{32}$"
)

SPAN_ID_PATTERN = re.compile(
    r"^[0-9a-f]{16}$"
)


def tracing_configured() -> bool:
    """
    Return True only when Langfuse tracing
    is enabled and both API keys exist.
    """

    return bool(
        settings.langfuse_enabled
        and settings.langfuse_public_key
        and settings.langfuse_secret_key
    )


def initialize_tracing() -> bool:
    """
    Lazily initialize the Langfuse client.

    Observability must never be required
    for the business application to work.
    """

    global _client

    if not tracing_configured():

        if settings.langfuse_enabled:

            _logger.warning(
                (
                    "Langfuse is enabled but "
                    "API credentials are missing."
                )
            )

        return False

    if _client is not None:
        return True

    with _client_lock:

        if _client is not None:
            return True

        try:

            _client = Langfuse(
                public_key=(
                    settings
                    .langfuse_public_key
                ),
                secret_key=(
                    settings
                    .langfuse_secret_key
                ),
                base_url=(
                    settings
                    .langfuse_base_url
                ),
                environment=(
                    settings
                    .langfuse_environment
                ),
                tracing_enabled=True,

                #
                # Short flush interval is useful
                # for a local lab demonstration.
                #

                flush_interval=1.0,
            )

        except Exception:

            _logger.exception(
                (
                    "Unable to initialize "
                    "Langfuse tracing."
                )
            )

            _client = None

            return False

    return True


def get_tracing_client(
) -> Langfuse | None:

    if (
        _client is None
        and not initialize_tracing()
    ):
        return None

    return _client


def _valid_trace_id(
    value: str | None,
) -> bool:

    if value is None:
        return False

    return bool(
        TRACE_ID_PATTERN.fullmatch(
            value.lower()
        )
    )


def _valid_span_id(
    value: str | None,
) -> bool:

    if value is None:
        return False

    return bool(
        SPAN_ID_PATTERN.fullmatch(
            value.lower()
        )
    )


def trace_context_from_headers(
    headers,
) -> dict | None:
    """
    Reconstruct distributed trace context
    from another GameHub service.
    """

    trace_id = headers.get(
        TRACE_ID_HEADER
    )

    parent_span_id = headers.get(
        PARENT_SPAN_HEADER
    )

    if (
        not _valid_trace_id(
            trace_id
        )
        or not _valid_span_id(
            parent_span_id
        )
    ):
        return None

    return {
        "trace_id": (
            trace_id.lower()
        ),
        "parent_span_id": (
            parent_span_id.lower()
        ),
    }


def trace_context_from_event(
    event: dict,
) -> dict | None:
    """
    Extract trace context carried through
    a RabbitMQ event.
    """

    raw_context = event.get(
        "_trace"
    )

    if not isinstance(
        raw_context,
        dict,
    ):
        return None

    trace_id = raw_context.get(
        "trace_id"
    )

    parent_span_id = (
        raw_context.get(
            "parent_span_id"
        )
    )

    if (
        not _valid_trace_id(
            trace_id
        )
        or not _valid_span_id(
            parent_span_id
        )
    ):
        return None

    return {
        "trace_id": (
            trace_id.lower()
        ),
        "parent_span_id": (
            parent_span_id.lower()
        ),
    }


@contextmanager
def start_span(
    *,
    name: str,
    trace_context: (
        dict
        | None
    ) = None,
    input_data=None,
    metadata: (
        dict
        | None
    ) = None,
):
    """
    Create a Langfuse/OpenTelemetry span.

    When Langfuse is disabled this becomes
    a no-op context manager, so tracing
    never becomes a runtime dependency.
    """

    client = (
        get_tracing_client()
    )

    if client is None:

        yield None

        return

    with (
        client
        .start_as_current_observation(
            as_type="span",
            name=name,
            trace_context=(
                trace_context
            ),
            input=input_data,
            metadata=metadata,
        )
    ) as span:

        yield span


def current_trace_headers(
) -> dict[str, str]:
    """
    Return distributed tracing headers for
    an outgoing HTTP request.

    The current observation becomes the
    parent of the remote service span.
    """

    client = (
        get_tracing_client()
    )

    if client is None:
        return {}

    trace_id = (
        client
        .get_current_trace_id()
    )

    span_id = (
        client
        .get_current_observation_id()
    )

    if (
        not _valid_trace_id(
            trace_id
        )
        or not _valid_span_id(
            span_id
        )
    ):
        return {}

    return {
        TRACE_ID_HEADER: trace_id,
        PARENT_SPAN_HEADER: span_id,
    }


def attach_current_trace(
    event: dict,
) -> dict:
    """
    Copy an integration event and attach
    distributed trace information.

    The application-level event fields are
    left unchanged.
    """

    traced_event = dict(
        event
    )

    client = (
        get_tracing_client()
    )

    if client is None:
        return traced_event

    trace_id = (
        client
        .get_current_trace_id()
    )

    span_id = (
        client
        .get_current_observation_id()
    )

    if (
        _valid_trace_id(
            trace_id
        )
        and _valid_span_id(
            span_id
        )
    ):

        traced_event[
            "_trace"
        ] = {
            "trace_id": trace_id,
            "parent_span_id": span_id,
        }

    return traced_event


def shutdown_tracing(
) -> None:
    """
    Flush all pending observations before
    the service process terminates.
    """

    global _client

    if _client is None:
        return

    try:

        _client.shutdown()

    except Exception:

        _logger.exception(
            (
                "Error while shutting "
                "down Langfuse."
            )
        )

    finally:

        _client = None