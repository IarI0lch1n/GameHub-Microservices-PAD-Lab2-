import asyncio

import httpx

from fastapi import (
    HTTPException,
    Request,
    status,
)

from fastapi.responses import Response

from gateway.app.routing import (
    ALL_SERVICES,
    ServiceTarget,
)

from shared.config.settings import settings

from shared.logging.setup import get_logger


SERVICE_NAME = "api-gateway"


HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


REQUEST_HEADERS_TO_SKIP = (
    HOP_BY_HOP_HEADERS
    | {
        "host",
        "content-length",
    }
)


RESPONSE_HEADERS_TO_SKIP = (
    HOP_BY_HOP_HEADERS
    | {
        "content-length",
        "content-encoding",
    }
)


class GatewayProxy:

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

        self.client = httpx.AsyncClient(
            timeout=(
                settings
                .http_timeout_seconds
            ),
            follow_redirects=False,
        )

        self._logger().info(
            "gateway_http_client_started"
        )

    async def close(
        self,
    ) -> None:

        if self.client is not None:
            await self.client.aclose()

        self.client = None

        self._logger().info(
            "gateway_http_client_stopped"
        )

    def _forward_headers(
        self,
        *,
        request: Request,
    ) -> dict[str, str]:

        headers = {
            key: value
            for key, value
            in request.headers.items()
            if (
                key.lower()
                not in REQUEST_HEADERS_TO_SKIP
            )
        }

        #
        # Gateway becomes the authority
        # for distributed request context.
        #

        headers[
            settings.request_id_header
        ] = request.state.request_id

        headers[
            settings.correlation_id_header
        ] = (
            request.state.correlation_id
        )

        headers[
            "X-Forwarded-Host"
        ] = (
            request.headers.get(
                "host",
                ""
            )
        )

        headers[
            "X-Forwarded-Proto"
        ] = request.url.scheme

        return headers

    @staticmethod
    def _response_headers(
        response: httpx.Response,
    ) -> dict[str, str]:

        return {
            key: value
            for key, value
            in response.headers.items()
            if (
                key.lower()
                not in RESPONSE_HEADERS_TO_SKIP
            )
        }

    async def forward(
        self,
        *,
        request: Request,
        target: ServiceTarget,
        path: str,
    ) -> Response:

        if self.client is None:
            raise RuntimeError(
                (
                    "Gateway HTTP client "
                    "is not initialized."
                )
            )

        target_url = (
            target.base_url.rstrip("/")
            + "/api/"
            + path.lstrip("/")
        )

        body = await request.body()

        self._logger().info(
            "gateway_proxy_started",
            target_service=(
                target.name
            ),
            target_url=target_url,
        )

        try:

            upstream = (
                await self.client.request(
                    method=request.method,
                    url=target_url,
                    params=(
                        request.query_params
                    ),
                    headers=(
                        self._forward_headers(
                            request=request
                        )
                    ),
                    content=(
                        body
                        if body
                        else None
                    ),
                )
            )

        except httpx.TimeoutException:

            self._logger().warning(
                "gateway_upstream_timeout",
                target_service=(
                    target.name
                ),
                target_url=target_url,
            )

            raise HTTPException(
                status_code=(
                    status
                    .HTTP_504_GATEWAY_TIMEOUT
                ),
                detail={
                    "message": (
                        "Upstream service "
                        "timed out."
                    ),
                    "service": target.name,
                },
            )

        except httpx.RequestError:

            self._logger().exception(
                "gateway_upstream_unavailable",
                target_service=(
                    target.name
                ),
                target_url=target_url,
            )

            raise HTTPException(
                status_code=(
                    status
                    .HTTP_503_SERVICE_UNAVAILABLE
                ),
                detail={
                    "message": (
                        "Upstream service "
                        "is unavailable."
                    ),
                    "service": target.name,
                },
            )

        self._logger().info(
            "gateway_proxy_completed",
            target_service=(
                target.name
            ),
            upstream_status=(
                upstream.status_code
            ),
        )

        return Response(
            content=upstream.content,
            status_code=(
                upstream.status_code
            ),
            headers=(
                self._response_headers(
                    upstream
                )
            ),
        )

    async def check_services(
        self,
    ) -> dict:

        if self.client is None:
            raise RuntimeError(
                (
                    "Gateway HTTP client "
                    "is not initialized."
                )
            )

        async def check(
            target: ServiceTarget,
        ) -> tuple[
            str,
            dict,
        ]:

            try:

                response = (
                    await self.client.get(
                        (
                            target
                            .base_url
                            .rstrip("/")
                            + "/ready"
                        ),
                        timeout=5.0,
                    )
                )

                if response.status_code == 200:

                    return (
                        target.name,
                        {
                            "status": "ok",
                            "url": (
                                target.base_url
                            ),
                        },
                    )

                return (
                    target.name,
                    {
                        "status": (
                            "not_ready"
                        ),
                        "url": (
                            target.base_url
                        ),
                        "http_status": (
                            response
                            .status_code
                        ),
                    },
                )

            except httpx.RequestError:

                return (
                    target.name,
                    {
                        "status": (
                            "unavailable"
                        ),
                        "url": (
                            target.base_url
                        ),
                    },
                )

        results = await asyncio.gather(
            *[
                check(service)
                for service
                in ALL_SERVICES
            ]
        )

        return {
            name: result
            for name, result
            in results
        }

    async def readiness_check(
        self,
    ) -> dict:

        services = await (
            self.check_services()
        )

        failed = [
            name
            for name, result
            in services.items()
            if (
                result["status"]
                != "ok"
            )
        ]

        if failed:

            raise RuntimeError(
                (
                    "Unavailable or unready "
                    "services: "
                    + ", ".join(
                        failed
                    )
                )
            )

        return {
            "services": services
        }


gateway_proxy = GatewayProxy()