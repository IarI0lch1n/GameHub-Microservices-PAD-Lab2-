from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from services.library_service.app.database import (
    get_db,
)

from services.library_service.app.repository import (
    LibraryRepository,
)

from services.library_service.app.schemas import (
    LibraryItemResponse,
)

from shared.security.dependencies import (
    get_current_identity,
)

from shared.security.jwt import (
    AuthIdentity,
)


router = APIRouter(
    prefix="/api/library",
    tags=[
        "Library",
    ],
)


@router.get(
    "",
    response_model=list[
        LibraryItemResponse
    ],
    summary="Get my game library",
)
def get_library(
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

    repository = LibraryRepository(
        db
    )

    return [
        LibraryItemResponse
        .model_validate(
            item
        )
        for item
        in repository.list_user_library(
            user_id=(
                identity.user_id
            )
        )
    ]


@router.get(
    "/{game_id}",
    response_model=(
        LibraryItemResponse
    ),
    summary="Get a game from my library",
)
def get_library_game(
    game_id: int,

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

    repository = LibraryRepository(
        db
    )

    item = repository.get_user_game(
        user_id=(
            identity.user_id
        ),
        game_id=game_id,
    )

    if item is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Game is not in "
                "your library."
            ),
        )

    return (
        LibraryItemResponse
        .model_validate(
            item
        )
    )