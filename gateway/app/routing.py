from dataclasses import dataclass

from shared.config.settings import settings


@dataclass(frozen=True)
class ServiceTarget:
    name: str
    base_url: str


AUTH = ServiceTarget(
    name="auth-service",
    base_url=settings.auth_service_url,
)

USERS = ServiceTarget(
    name="user-service",
    base_url=settings.user_service_url,
)

CATALOG = ServiceTarget(
    name="catalog-service",
    base_url=settings.catalog_service_url,
)

ORDERS = ServiceTarget(
    name="order-service",
    base_url=settings.order_service_url,
)

LIBRARY = ServiceTarget(
    name="library-service",
    base_url=settings.library_service_url,
)

REVIEWS = ServiceTarget(
    name="review-service",
    base_url=settings.review_service_url,
)

NOTIFICATIONS = ServiceTarget(
    name="notification-service",
    base_url=settings.notification_service_url,
)


ALL_SERVICES = [
    AUTH,
    USERS,
    CATALOG,
    ORDERS,
    LIBRARY,
    REVIEWS,
    NOTIFICATIONS,
]


def resolve_service(
    path: str,
) -> ServiceTarget | None:
    """
    Resolve an /api/* path to the
    responsible GameHub microservice.

    Examples:

    auth/login
        -> Auth Service

    games/1
        -> Catalog Service

    games/1/reviews
        -> Review Service

    orders
        -> Order Service
    """

    normalized = path.strip("/")

    if not normalized:
        return None

    parts = normalized.split("/")

    resource = parts[0]

    if resource == "auth":
        return AUTH

    if resource == "users":
        return USERS

    if resource == "genres":
        return CATALOG

    if resource == "games":

        #
        # /api/games/{id}/reviews
        # belongs to Review Service.
        #

        if (
            len(parts) >= 3
            and parts[2] == "reviews"
        ):
            return REVIEWS

        return CATALOG

    if resource == "orders":
        return ORDERS

    if resource == "library":
        return LIBRARY

    if resource == "reviews":
        return REVIEWS

    if resource == "notifications":
        return NOTIFICATIONS

    return None