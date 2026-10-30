from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)

from sqlalchemy.exc import (
    IntegrityError,
)

from sqlalchemy.orm import Session

from services.order_service.app.catalog_client import (
    CatalogGameNotFoundError,
    CatalogUnavailableError,
    catalog_client,
)

from services.order_service.app.database import (
    get_db,
)

from services.order_service.app.messaging import (
    publish_order_completed,
)

from services.order_service.app.repository import (
    OrderRepository,
)

from services.order_service.app.schemas import (
    OrderCreate,
    OrderResponse,
)

from shared.logging.setup import get_logger

from shared.security.dependencies import (
    get_current_identity,
)

from shared.security.jwt import AuthIdentity


SERVICE_NAME = "order-service"


router = APIRouter(
    prefix="/api/orders",
    tags=[
        "Orders",
    ],
)


def _logger():
    return get_logger(
        SERVICE_NAME
    )


@router.post(
    "",
    response_model=OrderResponse,
    status_code=(
        status.HTTP_201_CREATED
    ),
    summary="Purchase a game",
)
async def create_order(
    payload: OrderCreate,
    request: Request,

    identity: Annotated[
        AuthIdentity,
        Depends(
            get_current_identity
        ),
    ],

    db: Annotated[
        Session,
        Depends(get_db),
    ],
):

    repository = OrderRepository(
        db
    )

    existing = (
        repository
        .get_existing_purchase(
            user_id=(
                identity.user_id
            ),
            game_id=(
                payload.game_id
            ),
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "This game has already "
                "been purchased."
            ),
        )

    try:
        game = await catalog_client.get_game(
            game_id=payload.game_id,
            request_id=(
                request.state.request_id
            ),
            correlation_id=(
                request.state
                .correlation_id
            ),
        )

    except CatalogGameNotFoundError:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Game not found.",
        )

    except CatalogUnavailableError:
        raise HTTPException(
            status_code=(
                status
                .HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Catalog Service "
                "is unavailable."
            ),
        )

    if not game.is_published:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "Game is not currently "
                "available for purchase."
            ),
        )

    try:
        order = repository.create_order(
            user_id=identity.user_id,
            game_id=game.id,
            game_title=game.title,
            total_price=game.price,
        )

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "This game has already "
                "been purchased."
            ),
        )

    await publish_order_completed(
        order=order,
        correlation_id=(
            request.state
            .correlation_id
        ),
    )

    _logger().info(
        "order_completed",
        order_id=order.id,
        user_id=order.user_id,
        game_id=order.game_id,
        total_price=str(
            order.total_price
        ),
        correlation_id=(
            request.state
            .correlation_id
        ),
    )

    return (
        OrderResponse
        .model_validate(
            order
        )
    )


@router.get(
    "",
    response_model=list[
        OrderResponse
    ],
    summary="Get purchase history",
)
def list_orders(
    identity: Annotated[
        AuthIdentity,
        Depends(
            get_current_identity
        ),
    ],

    db: Annotated[
        Session,
        Depends(get_db),
    ],
):

    repository = OrderRepository(
        db
    )

    return [
        OrderResponse.model_validate(
            order
        )
        for order
        in repository.list_user_orders(
            user_id=(
                identity.user_id
            )
        )
    ]


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get an order",
)
def get_order(
    order_id: int,

    identity: Annotated[
        AuthIdentity,
        Depends(
            get_current_identity
        ),
    ],

    db: Annotated[
        Session,
        Depends(get_db),
    ],
):

    repository = OrderRepository(
        db
    )

    order = repository.get_user_order(
        order_id=order_id,
        user_id=(
            identity.user_id
        ),
    )

    if order is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Order not found.",
        )

    return (
        OrderResponse
        .model_validate(
            order
        )
    )