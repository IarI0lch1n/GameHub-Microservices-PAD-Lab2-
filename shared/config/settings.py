from functools import lru_cache

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    """
    Shared GameHub configuration.

    Values are loaded from environment variables
    and from the local .env file.
    """

    #
    # Application
    #

    app_env: str = "development"
    log_level: str = "INFO"

    #
    # API Gateway
    #

    api_gateway_host: str = "127.0.0.1"
    api_gateway_port: int = 8000

    #
    # Service ports
    #

    auth_service_port: int = 8001
    user_service_port: int = 8002
    catalog_service_port: int = 8003
    order_service_port: int = 8004
    library_service_port: int = 8005
    review_service_port: int = 8006
    notification_service_port: int = 8007

    #
    # Service URLs
    #

    auth_service_url: str = (
        "http://127.0.0.1:8001"
    )

    user_service_url: str = (
        "http://127.0.0.1:8002"
    )

    catalog_service_url: str = (
        "http://127.0.0.1:8003"
    )

    order_service_url: str = (
        "http://127.0.0.1:8004"
    )

    library_service_url: str = (
        "http://127.0.0.1:8005"
    )

    review_service_url: str = (
        "http://127.0.0.1:8006"
    )

    notification_service_url: str = (
        "http://127.0.0.1:8007"
    )

    #
    # Microsoft SQL Server
    #

    mssql_server: str = "localhost"
    mssql_port: int = 1433

    mssql_driver: str = (
        "ODBC Driver 17 for SQL Server"
    )

    mssql_trusted_connection: bool = True

    mssql_username: str = ""
    mssql_password: str = ""

    mssql_trust_server_certificate: bool = True

    auth_db_name: str = "gamehub_auth"
    user_db_name: str = "gamehub_users"
    catalog_db_name: str = "gamehub_catalog"
    order_db_name: str = "gamehub_orders"
    library_db_name: str = "gamehub_library"
    review_db_name: str = "gamehub_reviews"

    notification_db_name: str = (
        "gamehub_notifications"
    )

    #
    # JWT
    #

    jwt_secret_key: str = (
        "change-me-in-local-env"
    )

    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = 30

    refresh_token_expire_days: int = 7

    #
    # RabbitMQ
    #

    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672

    rabbitmq_username: str = "guest"
    rabbitmq_password: str = "guest"

    rabbitmq_vhost: str = "/"

    rabbitmq_exchange: str = (
        "gamehub.events"
    )

    rabbitmq_dead_letter_exchange: str = (
        "gamehub.events.dead-letter"
    )

    rabbitmq_max_delivery_attempts: int = 3

    rabbitmq_retry_delay_seconds: float = 1.0

    rabbitmq_publish_max_attempts: int = 3

    rabbitmq_publish_retry_delay_seconds: float = 0.5

    rabbitmq_management_url: str = (
        "http://localhost:15672"
    )

    event_user_registered: str = (
        "user.registered"
    )

    event_order_completed: str = (
        "order.completed"
    )

    event_review_created: str = (
        "review.created"
    )

    #
    # Langfuse
    #

    langfuse_enabled: bool = False

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""

    langfuse_base_url: str = (
        "https://cloud.langfuse.com"
    )

    langfuse_environment: str = (
        "development"
    )

    #
    # HTTP / distributed tracing
    #

    http_timeout_seconds: float = 10.0

    request_id_header: str = (
        "X-Request-ID"
    )

    correlation_id_header: str = (
        "X-Correlation-ID"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()