from sqlalchemy import (
    Engine,
)

from sqlalchemy.orm import (
    Session,
    sessionmaker,
)


def create_session_factory(
    engine: Engine,
) -> sessionmaker:
    """
    Create a standard SQLAlchemy session
    factory for a microservice database.
    """

    return sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )