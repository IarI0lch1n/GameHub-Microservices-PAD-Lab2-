import pytest

from shared.config.settings import (
    settings,
)


@pytest.fixture(
    autouse=True
)
def disable_external_tracing(
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Unit tests must not send telemetry
    to external Langfuse infrastructure.
    """

    monkeypatch.setattr(
        settings,
        "langfuse_enabled",
        False,
    )

    yield