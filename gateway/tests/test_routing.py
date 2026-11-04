import pytest

from gateway.app.routing import (
    resolve_service,
)


@pytest.mark.parametrize(
    (
        "path",
        "expected_service",
    ),
    [
        (
            "auth/login",
            "auth-service",
        ),
        (
            "auth/register",
            "auth-service",
        ),
        (
            "users/1",
            "user-service",
        ),
        (
            "games",
            "catalog-service",
        ),
        (
            "games/1",
            "catalog-service",
        ),
        (
            "genres",
            "catalog-service",
        ),
        (
            "orders",
            "order-service",
        ),
        (
            "orders/1",
            "order-service",
        ),
        (
            "library",
            "library-service",
        ),
        (
            "games/1/reviews",
            "review-service",
        ),
        (
            "reviews/1",
            "review-service",
        ),
        (
            "notifications",
            "notification-service",
        ),
        (
            "notifications/1/read",
            "notification-service",
        ),
    ],
)
def test_routing(
    path: str,
    expected_service: str,
) -> None:

    target = resolve_service(
        path
    )

    assert target is not None

    assert (
        target.name
        == expected_service
    )


def test_unknown_route() -> None:

    assert (
        resolve_service(
            "something-unknown"
        )
        is None
    )