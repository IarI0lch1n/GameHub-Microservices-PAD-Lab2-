from fastapi import (
    HTTPException,
    Request,
    status,
)

from gateway.app.proxy import (
    gateway_proxy,
)

from gateway.app.routing import (
    ALL_SERVICES,
    resolve_service,
)

from shared.web.service_factory import (
    create_service_app,
)


SERVICE_NAME = "api-gateway"


async def initialize_gateway(
) -> None:

    await gateway_proxy.connect()


async def shutdown_gateway(
) -> None:

    await gateway_proxy.close()


async def gateway_readiness_check(
) -> dict:

    return await (
        gateway_proxy
        .readiness_check()
    )


app = create_service_app(
    service_name=SERVICE_NAME,
    title="GameHub API Gateway",
    description=(
        "Single public entry point for "
        "the GameHub microservice system."
    ),
    version="0.1.0",
    startup_handler=(
        initialize_gateway
    ),
    shutdown_handler=(
        shutdown_gateway
    ),
    readiness_check=(
        gateway_readiness_check
    ),
)


@app.get(
    "/",
    tags=[
        "Gateway",
    ],
    summary="Gateway information",
)
async def root():

    return {
        "service": SERVICE_NAME,
        "message": (
            "GameHub API Gateway"
        ),
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
        "service_status": (
            "/services/status"
        ),
        "public_api": "/api/*",
    }


@app.get(
    "/services",
    tags=[
        "Gateway",
    ],
    summary="List routed services",
)
async def list_services():

    return {
        "services": [
            {
                "name": service.name,
                "url": service.base_url,
            }
            for service
            in ALL_SERVICES
        ]
    }


@app.get(
    "/services/status",
    tags=[
        "Gateway",
    ],
    summary=(
        "Check all downstream services"
    ),
)
async def service_status():

    return {
        "services": (
            await gateway_proxy
            .check_services()
        )
    }


@app.api_route(
    "/api/{path:path}",
    methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
        "HEAD",
    ],
    tags=[
        "Gateway Proxy",
    ],
    summary=(
        "Proxy a request to a "
        "GameHub microservice"
    ),
)
async def proxy_api(
    path: str,
    request: Request,
):

    target = resolve_service(
        path
    )

    if target is None:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail={
                "message": (
                    "No GameHub service "
                    "is registered for "
                    "this API path."
                ),
                "path": (
                    "/api/"
                    + path
                ),
            },
        )

    return await gateway_proxy.forward(
        request=request,
        target=target,
        path=path,
    )