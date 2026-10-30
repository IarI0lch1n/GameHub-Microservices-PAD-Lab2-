from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)

from sqlalchemy.exc import (
    IntegrityError,
)

from sqlalchemy.orm import Session

from services.review_service.app.catalog_client import (
    CatalogGameNotFoundError,
    CatalogUnavailableError,
    catalog_client,
)

from services.review_service.app.database import (
    get_db,
)

from services.review_service.app.messaging import (
    publish_review_created,
)

from services.review_service.app.repository import (
    ReviewRepository,
)

from services.review_service.app.schemas import (
    ReviewCreate,
    ReviewResponse,
    ReviewUpdate,
)

from shared.logging.setup import get_logger

from shared.security.dependencies import (
    get_current_identity,
)

from shared.security.jwt import AuthIdentity


SERVICE_NAME = "review-service"


router = APIRouter()


def _logger():
    return get_logger(
        SERVICE_NAME
    )


@router.get(
    "/api/games/{game_id}/reviews",
    response_model=list[
        ReviewResponse
    ],
    tags=[
        "Reviews",
    ],
    summary="List reviews for a game",
)
def list_reviews(
    game_id: int,

    db: Annotated[
        Session,
        Depends(get_db),
    ],
):

    repository = ReviewRepository(
        db
    )

    return [
        ReviewResponse.model_validate(
            review
        )
        for review
        in repository.list_game_reviews(
            game_id=game_id
        )
    ]


@router.post(
    "/api/games/{game_id}/reviews",
    response_model=ReviewResponse,
    status_code=(
        status.HTTP_201_CREATED
    ),
    tags=[
        "Reviews",
    ],
    summary="Create a game review",
)
async def create_review(
    game_id: int,
    payload: ReviewCreate,
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

    repository = ReviewRepository(
        db
    )

    existing = (
        repository
        .get_user_game_review(
            user_id=(
                identity.user_id
            ),
            game_id=game_id,
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "You have already "
                "reviewed this game."
            ),
        )

    try:
        game = await catalog_client.get_game(
            game_id=game_id,
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
                "Game is not published."
            ),
        )

    try:
        review = repository.create_review(
            user_id=(
                identity.user_id
            ),
            game_id=game.id,
            game_title=game.title,
            rating=payload.rating,
            content=payload.content,
        )

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "You have already "
                "reviewed this game."
            ),
        )

    await publish_review_created(
        review=review,
        correlation_id=(
            request.state
            .correlation_id
        ),
    )

    _logger().info(
        "review_created",
        review_id=review.id,
        user_id=review.user_id,
        game_id=review.game_id,
        rating=review.rating,
        correlation_id=(
            request.state
            .correlation_id
        ),
    )

    return (
        ReviewResponse
        .model_validate(
            review
        )
    )


@router.patch(
    "/api/reviews/{review_id}",
    response_model=ReviewResponse,
    tags=[
        "Reviews",
    ],
    summary="Update my review",
)
def update_review(
    review_id: int,
    payload: ReviewUpdate,

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

    repository = ReviewRepository(
        db
    )

    review = repository.get_review(
        review_id
    )

    if review is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Review not found.",
        )

    if (
        review.user_id
        != identity.user_id
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "You cannot modify "
                "another user's review."
            ),
        )

    data = payload.model_dump(
        exclude_unset=True
    )

    updated = repository.update_review(
        review=review,
        data=data,
    )

    return (
        ReviewResponse
        .model_validate(
            updated
        )
    )


@router.delete(
    "/api/reviews/{review_id}",
    status_code=(
        status.HTTP_204_NO_CONTENT
    ),
    tags=[
        "Reviews",
    ],
    summary="Delete my review",
)
def delete_review(
    review_id: int,

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

    repository = ReviewRepository(
        db
    )

    review = repository.get_review(
        review_id
    )

    if review is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Review not found.",
        )

    if (
        review.user_id
        != identity.user_id
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "You cannot delete "
                "another user's review."
            ),
        )

    repository.delete_review(
        review
    )

    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        )
    )