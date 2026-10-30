from collections.abc import (
    Generator,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
)

from shared.config.settings import (
    settings,
)

from shared.database.connection import (
    create_database_engine,
    ensure_database_exists,
    test_database_connection,
)

from shared.database.session import (
    create_session_factory,
)

from shared.logging.setup import (
    get_logger,
)


SERVICE_NAME = "user-service"


def _logger():
    return get_logger(
        SERVICE_NAME
    )


class UserBase(
    DeclarativeBase
):
    pass


engine = create_database_engine(
    database_name=(
        settings.user_db_name
    )
)


SessionLocal = create_session_factory(
    engine
)


def initialize_database(
) -> None:
    created = (
        ensure_database_exists(
            database_name=(
                settings.user_db_name
            )
        )
    )

    logger = _logger()

    if created:
        logger.info(
            "database_created",
            database=(
                settings.user_db_name
            ),
        )

    else:
        logger.info(
            "database_exists",
            database=(
                settings.user_db_name
            ),
        )

    from services.user_service.app import (
        models,
    )

    UserBase.metadata.create_all(
        bind=engine
    )

    logger.info(
        "database_initialized",
        database=(
            settings.user_db_name
        ),
        tables=list(
            UserBase
            .metadata
            .tables
            .keys()
        ),
    )


def readiness_check(
) -> dict:
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
                settings.user_db_name
            ),
        }
    }


def get_db(
) -> Generator[
    Session,
    None,
    None,
]:
    session = SessionLocal()

    try:
        yield session

    finally:
        session.close()


def shutdown_database(
) -> None:
    engine.dispose()

    _logger().info(
        "database_engine_disposed",
        database=(
            settings.user_db_name
        ),
    )