import logging
import sys

import structlog

from shared.config.settings import (
    settings,
)


def configure_logging(
    service_name: str,
) -> None:
    """
    Configure structured JSON logging
    for a GameHub microservice.
    """

    level = getattr(
        logging,
        settings.log_level.upper(),
        logging.INFO,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
        force=True,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(
                fmt="iso",
                utc=True,
                key="timestamp",
            ),
            structlog.processors.EventRenamer(
                "message"
            ),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=(
            structlog.make_filtering_bound_logger(
                level
            )
        ),
        logger_factory=(
            structlog.stdlib.LoggerFactory()
        ),
        cache_logger_on_first_use=True,
    )

    logger = get_logger(
        service_name
    )

    logger.info(
        "logging_configured",
        environment=settings.app_env,
        log_level=settings.log_level,
    )


def get_logger(
    service_name: str,
):
    return (
        structlog
        .get_logger()
        .bind(
            service=service_name
        )
    )