from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from sqlalchemy.orm import Session

from services.notification_service.app.database import (
    get_db,
)

from services.notification_service.app.repository import (
    NotificationRepository,
)

from services.notification_service.app.schemas import (
    NotificationResponse,
)

from shared.security.dependencies import (
    get_current_identity,
)

from shared.security.jwt import AuthIdentity


router = APIRouter(
    prefix="/api/notifications",
    tags=[
        "Notifications",
    ],
)


@router.get(
    "",
    response_model=list[
        NotificationResponse
    ],
    summary="Get my notifications",
)
def list_notifications(
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

    unread_only: bool = Query(
        default=False
    ),
):

    repository = (
        NotificationRepository(
            db
        )
    )

    return [
        NotificationResponse
        .model_validate(
            notification
        )
        for notification
        in repository
        .list_user_notifications(
            user_id=(
                identity.user_id
            ),
            unread_only=(
                unread_only
            ),
        )
    ]


@router.patch(
    "/{notification_id}/read",
    response_model=(
        NotificationResponse
    ),
    summary="Mark notification as read",
)
def mark_notification_read(
    notification_id: int,

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

    repository = (
        NotificationRepository(
            db
        )
    )

    notification = (
        repository
        .get_user_notification(
            notification_id=(
                notification_id
            ),
            user_id=(
                identity.user_id
            ),
        )
    )

    if notification is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Notification not found."
            ),
        )

    return (
        NotificationResponse
        .model_validate(
            repository.mark_read(
                notification
            )
        )
    )