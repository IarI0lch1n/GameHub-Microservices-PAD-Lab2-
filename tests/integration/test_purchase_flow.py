import os
import re
import time

from uuid import uuid4

import httpx
import pytest


pytestmark = pytest.mark.integration


RUN_INTEGRATION_TESTS = (
    os.getenv(
        "RUN_INTEGRATION_TESTS",
        "",
    ).lower()
    in {
        "1",
        "true",
        "yes",
    }
)


if not RUN_INTEGRATION_TESTS:

    pytest.skip(
        (
            "Integration tests require "
            "RUN_INTEGRATION_TESTS=1 and "
            "a running GameHub stack."
        ),
        allow_module_level=True,
    )


GATEWAY_URL = os.getenv(
    "INTEGRATION_GATEWAY_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


TRACE_ID_PATTERN = re.compile(
    r"^[0-9a-f]{32}$"
)


def wait_for(
    callback,
    *,
    timeout_seconds: float = 10.0,
    interval_seconds: float = 0.25,
):
    deadline = (
        time.monotonic()
        + timeout_seconds
    )

    while (
        time.monotonic()
        < deadline
    ):

        result = callback()

        if result is not None:
            return result

        time.sleep(
            interval_seconds
        )

    return None


def test_complete_purchase_flow() -> None:

    with httpx.Client(
        base_url=GATEWAY_URL,
        timeout=10.0,
    ) as client:

        #
        # Entire microservice system
        # must be ready.
        #

        status_response = client.get(
            "/services/status"
        )

        assert (
            status_response.status_code
            == 200
        )

        services = (
            status_response
            .json()
            ["services"]
        )

        assert len(
            services
        ) == 7

        assert all(
            service["status"]
            == "ok"
            for service
            in services.values()
        )

        #
        # Find a published game.
        #

        games_response = client.get(
            "/api/games"
        )

        assert (
            games_response.status_code
            == 200
        )

        games = (
            games_response.json()
        )

        published_games = [
            game
            for game
            in games
            if game[
                "is_published"
            ]
        ]

        if not published_games:

            pytest.skip(
                (
                    "Integration test "
                    "requires at least one "
                    "published catalog game."
                )
            )

        game = (
            published_games[0]
        )

        #
        # Register a unique user.
        #

        email = (
            "integration-"
            + uuid4().hex
            + "@example.com"
        )

        password = (
            "IntegrationTest123!"
        )

        register_response = (
            client.post(
                "/api/auth/register",
                json={
                    "email": email,
                    "password": (
                        password
                    ),
                },
            )
        )

        assert (
            register_response.status_code
            == 201
        )

        register_payload = (
            register_response.json()
        )

        user_id = (
            register_payload[
                "user"
            ][
                "id"
            ]
        )

        token = (
            register_payload[
                "tokens"
            ][
                "access_token"
            ]
        )

        headers = {
            "Authorization": (
                f"Bearer {token}"
            )
        }

        #
        # user.registered must eventually
        # create a User Service profile.
        #

        def get_profile():

            response = client.get(
                (
                    "/api/users/"
                    f"{user_id}"
                )
            )

            if response.status_code != 200:
                return None

            return response.json()

        profile = wait_for(
            get_profile
        )

        assert profile is not None

        assert (
            profile[
                "auth_user_id"
            ]
            == user_id
        )

        assert (
            profile[
                "email"
            ]
            == email
        )

        #
        # New user's library must start empty.
        #

        library_response = client.get(
            "/api/library",
            headers=headers,
        )

        assert (
            library_response.status_code
            == 200
        )

        assert (
            library_response.json()
            == []
        )

        #
        # Purchase through API Gateway.
        #

        order_response = client.post(
            "/api/orders",
            headers=headers,
            json={
                "game_id": (
                    game["id"]
                )
            },
        )

        assert (
            order_response.status_code
            == 201
        )

        order = (
            order_response.json()
        )

        assert (
            order["user_id"]
            == user_id
        )

        assert (
            order["game_id"]
            == game["id"]
        )

        assert (
            order["status"]
            == "completed"
        )

        #
        # Distributed request context.
        #

        request_id = (
            order_response.headers.get(
                "X-Request-ID"
            )
        )

        correlation_id = (
            order_response.headers.get(
                "X-Correlation-ID"
            )
        )

        assert request_id

        assert correlation_id

        assert (
            request_id
            == correlation_id
        )

        trace_id = (
            order_response.headers.get(
                "X-Langfuse-Trace-ID"
            )
        )

        if trace_id is not None:

            assert (
                TRACE_ID_PATTERN
                .fullmatch(
                    trace_id
                )
            )

        #
        # order.completed must eventually
        # create the Library item.
        #

        def get_library_item():

            response = client.get(
                "/api/library",
                headers=headers,
            )

            if response.status_code != 200:
                return None

            for item in (
                response.json()
            ):

                if (
                    item["game_id"]
                    == game["id"]
                ):

                    return item

            return None

        library_item = wait_for(
            get_library_item
        )

        assert (
            library_item
            is not None
        )

        assert (
            library_item[
                "order_id"
            ]
            == order["id"]
        )

        #
        # The same order.completed event
        # must create a Notification.
        #

        def get_purchase_notification():

            response = client.get(
                "/api/notifications",
                headers=headers,
            )

            if response.status_code != 200:
                return None

            for notification in (
                response.json()
            ):

                if (
                    notification[
                        "notification_type"
                    ]
                    == "purchase_completed"
                    and game["title"]
                    in notification[
                        "message"
                    ]
                ):

                    return notification

            return None

        notification = wait_for(
            get_purchase_notification
        )

        assert (
            notification
            is not None
        )

        assert (
            notification[
                "is_read"
            ]
            is False
        )

        #
        # Duplicate purchase protection.
        #

        duplicate_response = (
            client.post(
                "/api/orders",
                headers=headers,
                json={
                    "game_id": (
                        game["id"]
                    )
                },
            )
        )

        assert (
            duplicate_response
            .status_code
            == 409
        )