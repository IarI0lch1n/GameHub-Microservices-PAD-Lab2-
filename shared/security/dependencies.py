from typing import Annotated

from fastapi import (
    Depends,
    HTTPException,
    status,
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from shared.security.jwt import (
    AccessTokenError,
    AuthIdentity,
    decode_access_token,
)


bearer_scheme = HTTPBearer(
    auto_error=False
)


def get_current_identity(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> AuthIdentity:

    if (
        credentials is None
        or credentials.scheme.lower()
        != "bearer"
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Authentication required.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    try:
        return decode_access_token(
            credentials.credentials
        )

    except AccessTokenError:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid or expired "
                "access token."
            ),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )


def require_admin(
    identity: Annotated[
        AuthIdentity,
        Depends(get_current_identity),
    ],
) -> AuthIdentity:

    if identity.role != "admin":
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Administrator role required."
            ),
        )

    return identity