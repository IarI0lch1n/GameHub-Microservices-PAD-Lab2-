from typing import (
    Annotated,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import (
    Session,
)

from services.user_service.app.database import (
    get_db,
)

from services.user_service.app.repository import (
    UserProfileRepository,
)

from services.user_service.app.schemas import (
    UserProfileResponse,
)


router = APIRouter(
    prefix="/api/users",
    tags=[
        "Users",
    ],
)


@router.get(
    "/{auth_user_id}",
    response_model=(
        UserProfileResponse
    ),
    summary=(
        "Get user profile by Auth Service ID"
    ),
)
def get_profile(
    auth_user_id: int,
    db: Annotated[
        Session,
        Depends(
            get_db
        ),
    ],
):
    repository = (
        UserProfileRepository(
            db
        )
    )

    profile = (
        repository
        .get_by_auth_user_id(
            auth_user_id
        )
    )

    if profile is None:
        raise HTTPException(
            status_code=(
                status
                .HTTP_404_NOT_FOUND
            ),
            detail=(
                "User profile "
                "not found."
            ),
        )

    return (
        UserProfileResponse
        .model_validate(
            profile
        )
    )