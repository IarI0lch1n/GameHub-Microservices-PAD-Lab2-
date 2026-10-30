from collections.abc import Generator

from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
)

from shared.config.settings import settings

from shared.database.connection import (
    create_database_engine,
    ensure_database_exists,
    test_database_connection,
)

from shared.database.session import (
    create_session_factory,
)

from shared.logging.setup import get_logger


SERVICE_NAME = "auth-service"


def _logger():
    """
    Resolve logger lazily.

    Logging configuration is initialized
    by the FastAPI service factory before
    database startup handlers are executed.
    """

    return get_logger(
        SERVICE_NAME
    )


class AuthBase(
    DeclarativeBase
):
    pass


engine = create_database_engine(
    database_name=(
        settings.auth_db_name
    )
)


SessionLocal = create_session_factory(
    engine
)


def initialize_database() -> None:
    """
    Create the auth database if required
    and initialize all auth tables.
    """

    created = ensure_database_exists(
        database_name=(
            settings.auth_db_name
        )
    )

    logger = _logger()

    if created:

        logger.info(
            "database_created",
            database=(
                settings.auth_db_name
            ),
        )

    else:

        logger.info(
            "database_exists",
            database=(
                settings.auth_db_name
            ),
        )

    #
    # Models must be imported before
    # SQLAlchemy create_all().
    #

    from services.auth_service.app import models

    AuthBase.metadata.create_all(
        bind=engine
    )

    logger.info(
        "database_initialized",
        database=(
            settings.auth_db_name
        ),
        tables=list(
            AuthBase.metadata.tables.keys()
        ),
    )


def readiness_check() -> dict:
    """
    Used by /ready.

    If SELECT 1 fails, the service factory
    converts the exception to HTTP 503.
    """

    test_database_connection(
        engine
    )

    return {
        "database": {
            "status": "ok",
            "provider": (
                "Microsoft SQL Server"
            ),
            "database": (
                settings.auth_db_name
            ),
        }
    }


def get_db() -> Generator[
    Session,
    None,
    None,
]:
    session = SessionLocal()

    try:

        yield session

    finally:

        session.close()


def shutdown_database() -> None:
    engine.dispose()

    _logger().info(
        "database_engine_disposed",
        database=(
            settings.auth_db_name
        ),
    )