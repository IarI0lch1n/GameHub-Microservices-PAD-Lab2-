from fastapi.testclient import (
    TestClient,
)

from services.auth_service.app.main import (
    app,
)


client = TestClient(
    app
)


def test_health() -> None:

    response = client.get(
        "/health"
    )

    assert (
        response.status_code
        == 200
    )

    payload = response.json()

    assert (
        payload["status"]
        == "healthy"
    )

    assert (
        payload["service"]
        == "auth-service"
    )


def test_ready() -> None:

    response = client.get(
        "/ready"
    )

    assert (
        response.status_code
        == 200
    )

    payload = response.json()

    assert (
        payload["status"]
        == "ready"
    )

    assert (
        payload["service"]
        == "auth-service"
    )