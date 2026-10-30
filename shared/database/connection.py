from urllib.parse import quote_plus

from sqlalchemy import (
    Engine,
    create_engine,
    text,
)

from shared.config.settings import settings


def _yes_no(
    value: bool,
) -> str:
    return "yes" if value else "no"


def build_odbc_connection_string(
    *,
    database_name: str,
) -> str:
    """
    Build a Microsoft SQL Server ODBC
    connection string.

    Supports:
    - Windows Authentication;
    - SQL Server Authentication.
    """

    server = (
        f"{settings.mssql_server},"
        f"{settings.mssql_port}"
    )

    trust_server_certificate = _yes_no(
        settings.mssql_trust_server_certificate
    )

    parts = [
        (
            "DRIVER="
            f"{{{settings.mssql_driver}}}"
        ),
        f"SERVER={server}",
        f"DATABASE={database_name}",
        (
            "TrustServerCertificate="
            f"{trust_server_certificate}"
        ),
    ]

    if settings.mssql_trusted_connection:

        parts.append(
            "Trusted_Connection=yes"
        )

    else:

        if not (
            settings.mssql_username
            and settings.mssql_password
        ):
            raise RuntimeError(
                (
                    "SQL Server authentication "
                    "requires MSSQL_USERNAME "
                    "and MSSQL_PASSWORD."
                )
            )

        parts.append(
            f"UID={settings.mssql_username}"
        )

        parts.append(
            f"PWD={settings.mssql_password}"
        )

    return ";".join(
        parts
    ) + ";"


def build_sqlalchemy_url(
    *,
    database_name: str,
) -> str:
    """
    Convert the ODBC connection string
    to a SQLAlchemy pyodbc URL.
    """

    connection_string = (
        build_odbc_connection_string(
            database_name=database_name,
        )
    )

    encoded = quote_plus(
        connection_string
    )

    return (
        "mssql+pyodbc:///"
        f"?odbc_connect={encoded}"
    )


def create_database_engine(
    *,
    database_name: str,
    autocommit: bool = False,
) -> Engine:
    """
    Create a SQLAlchemy engine for a
    single microservice database.
    """

    engine_options = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
        "future": True,
    }

    if autocommit:
        engine_options[
            "isolation_level"
        ] = "AUTOCOMMIT"

    return create_engine(
        build_sqlalchemy_url(
            database_name=database_name,
        ),
        **engine_options,
    )


def ensure_database_exists(
    *,
    database_name: str,
) -> bool:
    """
    Ensure that a SQL Server database
    exists.

    Returns:
        True  - database was created.
        False - database already existed.
    """

    master_engine = (
        create_database_engine(
            database_name="master",
            autocommit=True,
        )
    )

    try:

        with (
            master_engine.connect()
            as connection
        ):

            existing_database = (
                connection.execute(
                    text(
                        (
                            "SELECT "
                            "DB_ID(:database_name)"
                        )
                    ),
                    {
                        "database_name": (
                            database_name
                        ),
                    },
                )
                .scalar()
            )

            if (
                existing_database
                is not None
            ):
                return False

            #
            # SQL identifiers cannot be
            # passed as normal parameters.
            #
            # Escape closing square brackets
            # before using the value as an
            # identifier.
            #

            safe_database_name = (
                database_name.replace(
                    "]",
                    "]]",
                )
            )

            connection.exec_driver_sql(
                (
                    "CREATE DATABASE "
                    f"[{safe_database_name}]"
                )
            )

            return True

    finally:

        master_engine.dispose()


def test_database_connection(
    engine: Engine,
) -> None:
    """
    Raise an exception if SQL Server
    cannot execute a simple query.
    """

    with (
        engine.connect()
        as connection
    ):

        result = (
            connection.execute(
                text(
                    "SELECT 1"
                )
            )
            .scalar_one()
        )

        if result != 1:

            raise RuntimeError(
                (
                    "Unexpected SQL Server "
                    "health check result."
                )
            )