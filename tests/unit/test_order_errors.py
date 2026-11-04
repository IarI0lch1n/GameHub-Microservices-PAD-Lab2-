from types import (
    SimpleNamespace,
)

import pytest

from fastapi import (
    HTTPException,
)

import services.order_service.app.router as order_router

from services.order_service.app.catalog_client import (
    CatalogGameNotFoundError,
    CatalogUnavailableError,
)

from services.order_service.app.schemas import (
    OrderCreate,
)

from shared.security.jwt import (
    AuthIdentity,
)


class FakeRepository:

    existing_purchase = None

    def __init__(
        self,
        session,
    ) -> None:

        self.session = session

    def get_existing_purchase(
        self,
        *,
        user_id: int,
        game_id: int,
    ):

        return (
            self.existing_purchase
        )


def make_request():

    return SimpleNamespace(
        state=SimpleNamespace(
            request_id=(
                "test-request-id"
            ),
            correlation_id=(
                "test-correlation-id"
            ),
        )
    )


def make_identity():

    return AuthIdentity(
        user_id=123,
        role="user",
    )


@pytest.mark.asyncio
async def test_duplicate_purchase_returns_409(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    class DuplicateRepository(
        FakeRepository
    ):
        existing_purchase = object()

    monkeypatch.setattr(
        order_router,
        "OrderRepository",
        DuplicateRepository,
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:

        await (
            order_router
            .create_order(
                payload=OrderCreate(
                    game_id=1
                ),
                request=(
                    make_request()
                ),
                identity=(
                    make_identity()
                ),
                db=object(),
            )
        )

    assert (
        exc_info.value.status_code
        == 409
    )

    assert (
        exc_info.value.detail
        == (
            "This game has already "
            "been purchased."
        )
    )


@pytest.mark.asyncio
async def test_catalog_unavailable_returns_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    monkeypatch.setattr(
        order_router,
        "OrderRepository",
        FakeRepository,
    )

    async def unavailable(
        **kwargs,
    ):

        raise (
            CatalogUnavailableError(
                "Catalog unavailable"
            )
        )

    monkeypatch.setattr(
        order_router.catalog_client,
        "get_game",
        unavailable,
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:

        await (
            order_router
            .create_order(
                payload=OrderCreate(
                    game_id=1
                ),
                request=(
                    make_request()
                ),
                identity=(
                    make_identity()
                ),
                db=object(),
            )
        )

    assert (
        exc_info.value.status_code
        == 503
    )

    assert (
        exc_info.value.detail
        == (
            "Catalog Service "
            "is unavailable."
        )
    )


@pytest.mark.asyncio
async def test_missing_catalog_game_returns_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    monkeypatch.setattr(
        order_router,
        "OrderRepository",
        FakeRepository,
    )

    async def missing_game(
        **kwargs,
    ):

        raise (
            CatalogGameNotFoundError(
                "Game not found"
            )
        )

    monkeypatch.setattr(
        order_router.catalog_client,
        "get_game",
        missing_game,
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:

        await (
            order_router
            .create_order(
                payload=OrderCreate(
                    game_id=999
                ),
                request=(
                    make_request()
                ),
                identity=(
                    make_identity()
                ),
                db=object(),
            )
        )

    assert (
        exc_info.value.status_code
        == 404
    )

    assert (
        exc_info.value.detail
        == "Game not found."
    )


@pytest.mark.asyncio
async def test_unpublished_game_returns_409(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    monkeypatch.setattr(
        order_router,
        "OrderRepository",
        FakeRepository,
    )

    async def unpublished_game(
        **kwargs,
    ):

        return SimpleNamespace(
            id=1,
            title="Hidden Game",
            price=29.99,
            is_published=False,
        )

    monkeypatch.setattr(
        order_router.catalog_client,
        "get_game",
        unpublished_game,
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:

        await (
            order_router
            .create_order(
                payload=OrderCreate(
                    game_id=1
                ),
                request=(
                    make_request()
                ),
                identity=(
                    make_identity()
                ),
                db=object(),
            )
        )

    assert (
        exc_info.value.status_code
        == 409
    )

    assert (
        exc_info.value.detail
        == (
            "Game is not currently "
            "available for purchase."
        )
    )