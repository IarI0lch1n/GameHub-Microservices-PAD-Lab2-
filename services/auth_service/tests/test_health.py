import pytest

from fastapi.testclient import (
    TestClient,
)

from services.auth_service.app import (
    database as auth_database,
)

from services.auth_service.app import (
    messaging as auth_messaging,
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


def test_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    def fake_database_readiness(
    ) -> dict:

        return {
            "database": {
                "status": "ok",
                "provider": (
                    "Microsoft SQL Server"
                ),
                "database": (
                    "gamehub_auth"
                ),
            }
        }

    async def fake_rabbitmq_readiness(
    ) -> dict:

        return {
            "rabbitmq": {
                "status": "ok",
                "exchange": (
                    "gamehub.events"
                ),
            }
        }

    monkeypatch.setattr(
        auth_database,
        "readiness_check",
        fake_database_readiness,
    )

    monkeypatch.setattr(
        auth_messaging,
        "readiness_check",
        fake_rabbitmq_readiness,
    )

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

    assert (
        payload["checks"]
        ["database"]
        ["status"]
        == "ok"
    )

    assert (
        payload["checks"]
        ["rabbitmq"]
        ["status"]
        == "ok"
    )


def test_ready_returns_503_when_dependency_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    def failing_database_readiness(
    ) -> dict:

        raise RuntimeError(
            "Database unavailable"
        )

    monkeypatch.setattr(
        auth_database,
        "readiness_check",
        failing_database_readiness,
    )

    response = client.get(
        "/ready"
    )

    assert (
        response.status_code
        == 503
    )

    payload = response.json()

    assert (
        payload["status"]
        == "not_ready"
    )

    assert (
        payload["service"]
        == "auth-service"
    )