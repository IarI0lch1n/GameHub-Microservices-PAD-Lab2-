from decimal import Decimal

import httpx

from pydantic import BaseModel

from shared.config.settings import settings

from shared.logging.setup import get_logger


SERVICE_NAME = "order-service"


class CatalogGame(
    BaseModel
):
    id: int
    title: str
    price: Decimal
    is_published: bool


class CatalogUnavailableError(
    RuntimeError
):
    pass


class CatalogGameNotFoundError(
    RuntimeError
):
    pass


class CatalogClient:

    def __init__(
        self,
    ) -> None:

        self.client: (
            httpx.AsyncClient
            | None
        ) = None

    def _logger(
        self,
    ):
        return get_logger(
            SERVICE_NAME
        )

    async def connect(
        self,
    ) -> None:

        if self.client is not None:
            return

        self.client = (
            httpx.AsyncClient(
                base_url=(
                    settings
                    .catalog_service_url
                    .rstrip("/")
                ),
                timeout=(
                    settings
                    .http_timeout_seconds
                ),
            )
        )

        self._logger().info(
            "catalog_client_initialized",
            base_url=(
                settings.catalog_service_url
            ),
        )

    def _headers(
        self,
        *,
        request_id: str,
        correlation_id: str,
    ) -> dict[str, str]:

        return {
            settings.request_id_header: (
                request_id
            ),
            settings.correlation_id_header: (
                correlation_id
            ),
        }

    async def get_game(
        self,
        *,
        game_id: int,
        request_id: str,
        correlation_id: str,
    ) -> CatalogGame:

        if self.client is None:
            raise RuntimeError(
                (
                    "Catalog HTTP client "
                    "is not initialized."
                )
            )

        try:
            response = await self.client.get(
                f"/internal/games/{game_id}",
                headers=self._headers(
                    request_id=request_id,
                    correlation_id=(
                        correlation_id
                    ),
                ),
            )

        except httpx.RequestError as exc:
            raise CatalogUnavailableError(
                (
                    "Catalog Service "
                    "is unavailable."
                )
            ) from exc

        if response.status_code == 404:
            raise CatalogGameNotFoundError(
                "Game not found."
            )

        if response.status_code != 200:
            raise CatalogUnavailableError(
                (
                    "Catalog Service returned "
                    f"HTTP {response.status_code}."
                )
            )

        game = CatalogGame.model_validate(
            response.json()
        )

        self._logger().info(
            "catalog_game_resolved",
            game_id=game.id,
            game_title=game.title,
            correlation_id=(
                correlation_id
            ),
        )

        return game

    async def readiness_check(
        self,
    ) -> dict:

        if self.client is None:
            raise RuntimeError(
                (
                    "Catalog HTTP client "
                    "is not initialized."
                )
            )

        try:
            response = await self.client.get(
                "/ready"
            )

        except httpx.RequestError as exc:
            raise RuntimeError(
                (
                    "Catalog Service "
                    "is unavailable."
                )
            ) from exc

        if response.status_code != 200:
            raise RuntimeError(
                (
                    "Catalog Service "
                    "is not ready."
                )
            )

        return {
            "catalog_service": {
                "status": "ok",
                "url": (
                    settings
                    .catalog_service_url
                ),
            }
        }

    async def close(
        self,
    ) -> None:

        if self.client is not None:
            await self.client.aclose()

        self.client = None

        self._logger().info(
            "catalog_client_closed"
        )


catalog_client = CatalogClient()