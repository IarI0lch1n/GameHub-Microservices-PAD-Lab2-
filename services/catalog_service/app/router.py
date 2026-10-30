from typing import (
    Annotated,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)

from sqlalchemy.exc import (
    IntegrityError,
)

from sqlalchemy.orm import (
    Session,
)

from services.catalog_service.app.auth import (
    require_admin,
)

from services.catalog_service.app.database import (
    get_db,
)

from services.catalog_service.app.repository import (
    CatalogRepository,
)

from services.catalog_service.app.schemas import (
    GameCreate,
    GameResponse,
    GameUpdate,
    GenreCreate,
    GenreResponse,
    InternalGameResponse,
)

from shared.security.jwt import (
    AuthIdentity,
)


router = APIRouter(
    prefix="/api",
)


internal_router = APIRouter(
    prefix="/internal",
    tags=[
        "Internal",
    ],
)


def _resolve_genres(
    repository: CatalogRepository,
    genre_ids: list[int],
):
    unique_ids = list(
        dict.fromkeys(
            genre_ids
        )
    )

    genres = (
        repository
        .get_genres_by_ids(
            unique_ids
        )
    )

    found_ids = {
        genre.id
        for genre in genres
    }

    missing_ids = [
        genre_id
        for genre_id
        in unique_ids
        if genre_id
        not in found_ids
    ]

    if missing_ids:
        raise HTTPException(
            status_code=(
                status
                .HTTP_400_BAD_REQUEST
            ),
            detail={
                "message": (
                    "One or more genres "
                    "do not exist."
                ),
                "missing_genre_ids": (
                    missing_ids
                ),
            },
        )

    return genres


#
# Genres
#

@router.get(
    "/genres",
    response_model=list[
        GenreResponse
    ],
    tags=[
        "Genres",
    ],
    summary="List game genres",
)
def list_genres(
    db: Annotated[
        Session,
        Depends(
            get_db
        ),
    ],
):
    repository = (
        CatalogRepository(
            db
        )
    )

    return [
        GenreResponse.model_validate(
            genre
        )
        for genre
        in repository.list_genres()
    ]


@router.post(
    "/genres",
    response_model=(
        GenreResponse
    ),
    status_code=(
        status.HTTP_201_CREATED
    ),
    tags=[
        "Genres",
    ],
    summary="Create a genre",
)
def create_genre(
    payload: GenreCreate,

    db: Annotated[
        Session,
        Depends(
            get_db
        ),
    ],

    admin: Annotated[
        AuthIdentity,
        Depends(
            require_admin
        ),
    ],
):
    repository = (
        CatalogRepository(
            db
        )
    )

    existing = (
        repository
        .get_genre_by_name(
            payload.name
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "Genre already exists."
            ),
        )

    try:
        genre = (
            repository
            .create_genre(
                name=payload.name
            )
        )

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "Genre already exists."
            ),
        )

    return (
        GenreResponse
        .model_validate(
            genre
        )
    )


#
# Games
#

@router.get(
    "/games",
    response_model=list[
        GameResponse
    ],
    tags=[
        "Games",
    ],
    summary="Browse the game catalog",
)
def list_games(
    db: Annotated[
        Session,
        Depends(
            get_db
        ),
    ],

    search: (
        str
        | None
    ) = Query(
        default=None,
    ),

    genre: (
        str
        | None
    ) = Query(
        default=None,
    ),

    min_price: (
        float
        | None
    ) = Query(
        default=None,
        ge=0,
    ),

    max_price: (
        float
        | None
    ) = Query(
        default=None,
        ge=0,
    ),

    published: (
        bool
        | None
    ) = Query(
        default=None,
    ),

    skip: int = Query(
        default=0,
        ge=0,
    ),

    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
):
    if (
        min_price is not None
        and max_price is not None
        and min_price > max_price
    ):
        raise HTTPException(
            status_code=(
                status
                .HTTP_400_BAD_REQUEST
            ),
            detail=(
                "min_price cannot be "
                "greater than max_price."
            ),
        )

    repository = (
        CatalogRepository(
            db
        )
    )

    games = repository.list_games(
        search=search,
        genre=genre,
        min_price=min_price,
        max_price=max_price,
        published=published,
        skip=skip,
        limit=limit,
    )

    return [
        GameResponse.model_validate(
            game
        )
        for game
        in games
    ]


@router.get(
    "/games/{game_id}",
    response_model=(
        GameResponse
    ),
    tags=[
        "Games",
    ],
    summary="Get a game",
)
def get_game(
    game_id: int,

    db: Annotated[
        Session,
        Depends(
            get_db
        ),
    ],
):
    repository = (
        CatalogRepository(
            db
        )
    )

    game = repository.get_game(
        game_id
    )

    if game is None:
        raise HTTPException(
            status_code=(
                status
                .HTTP_404_NOT_FOUND
            ),
            detail="Game not found.",
        )

    return (
        GameResponse
        .model_validate(
            game
        )
    )


@router.post(
    "/games",
    response_model=(
        GameResponse
    ),
    status_code=(
        status.HTTP_201_CREATED
    ),
    tags=[
        "Games",
    ],
    summary="Create a game",
)
def create_game(
    payload: GameCreate,

    db: Annotated[
        Session,
        Depends(
            get_db
        ),
    ],

    admin: Annotated[
        AuthIdentity,
        Depends(
            require_admin
        ),
    ],
):
    repository = (
        CatalogRepository(
            db
        )
    )

    genres = _resolve_genres(
        repository,
        payload.genre_ids,
    )

    game = repository.create_game(
        title=payload.title,
        description=(
            payload.description
        ),
        price=payload.price,
        release_date=(
            payload.release_date
        ),
        developer=(
            payload.developer
        ),
        publisher=(
            payload.publisher
        ),
        is_published=(
            payload.is_published
        ),
        genres=genres,
    )

    return (
        GameResponse
        .model_validate(
            game
        )
    )


@router.patch(
    "/games/{game_id}",
    response_model=(
        GameResponse
    ),
    tags=[
        "Games",
    ],
    summary="Update a game",
)
def update_game(
    game_id: int,

    payload: GameUpdate,

    db: Annotated[
        Session,
        Depends(
            get_db
        ),
    ],

    admin: Annotated[
        AuthIdentity,
        Depends(
            require_admin
        ),
    ],
):
    repository = (
        CatalogRepository(
            db
        )
    )

    game = repository.get_game(
        game_id
    )

    if game is None:
        raise HTTPException(
            status_code=(
                status
                .HTTP_404_NOT_FOUND
            ),
            detail="Game not found.",
        )

    data = payload.model_dump(
        exclude_unset=True
    )

    genres = None

    if "genre_ids" in data:
        genre_ids = (
            data.pop(
                "genre_ids"
            )
        )

        genres = _resolve_genres(
            repository,
            genre_ids or [],
        )

    updated_game = (
        repository.update_game(
            game=game,
            data=data,
            genres=genres,
        )
    )

    return (
        GameResponse
        .model_validate(
            updated_game
        )
    )


@router.delete(
    "/games/{game_id}",
    status_code=(
        status.HTTP_204_NO_CONTENT
    ),
    tags=[
        "Games",
    ],
    summary="Delete a game",
)
def delete_game(
    game_id: int,

    db: Annotated[
        Session,
        Depends(
            get_db
        ),
    ],

    admin: Annotated[
        AuthIdentity,
        Depends(
            require_admin
        ),
    ],
):
    repository = (
        CatalogRepository(
            db
        )
    )

    game = repository.get_game(
        game_id
    )

    if game is None:
        raise HTTPException(
            status_code=(
                status
                .HTTP_404_NOT_FOUND
            ),
            detail="Game not found.",
        )

    repository.delete_game(
        game
    )

    return Response(
        status_code=(
            status
            .HTTP_204_NO_CONTENT
        )
    )


#
# Internal service-to-service endpoint.
#
# Order Service will use this later.
#

@internal_router.get(
    "/games/{game_id}",
    response_model=(
        InternalGameResponse
    ),
    summary=(
        "Get game information "
        "for another microservice"
    ),
)
def get_internal_game(
    game_id: int,

    db: Annotated[
        Session,
        Depends(
            get_db
        ),
    ],
):
    repository = (
        CatalogRepository(
            db
        )
    )

    game = repository.get_game(
        game_id
    )

    if game is None:
        raise HTTPException(
            status_code=(
                status
                .HTTP_404_NOT_FOUND
            ),
            detail="Game not found.",
        )

    return (
        InternalGameResponse
        .model_validate(
            game
        )
    )