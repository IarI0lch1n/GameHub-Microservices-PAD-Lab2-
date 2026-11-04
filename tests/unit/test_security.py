from datetime import (
    datetime,
    timedelta,
    timezone,
)

import jwt
import pytest

from fastapi import (
    HTTPException,
)

from services.catalog_service.app.auth import (
    require_admin as catalog_require_admin,
)

from shared.config.settings import (
    settings,
)

from shared.security.dependencies import (
    get_current_identity,
)

from shared.security.jwt import (
    AccessTokenError,
    AuthIdentity,
    decode_access_token,
)


def make_token(
    *,
    user_id: int = 10,
    role: str = "user",
    token_type: str = "access",
    expires_delta: timedelta = (
        timedelta(
            minutes=10
        )
    ),
) -> str:

    now = datetime.now(
        timezone.utc
    )

    return jwt.encode(
        {
            "sub": str(
                user_id
            ),
            "role": role,
            "type": token_type,
            "iat": now,
            "exp": (
                now
                + expires_delta
            ),
        },
        settings.jwt_secret_key,
        algorithm=(
            settings.jwt_algorithm
        ),
    )


def test_decode_valid_access_token(
) -> None:

    token = make_token(
        user_id=42,
        role="user",
    )

    identity = (
        decode_access_token(
            token
        )
    )

    assert (
        identity.user_id
        == 42
    )

    assert (
        identity.role
        == "user"
    )


def test_decode_rejects_refresh_token(
) -> None:

    token = make_token(
        token_type="refresh"
    )

    with pytest.raises(
        AccessTokenError
    ):
        decode_access_token(
            token
        )


def test_decode_rejects_expired_token(
) -> None:

    token = make_token(
        expires_delta=timedelta(
            seconds=-1
        )
    )

    with pytest.raises(
        AccessTokenError
    ):
        decode_access_token(
            token
        )


def test_protected_endpoint_requires_authentication(
) -> None:

    with pytest.raises(
        HTTPException
    ) as exc_info:

        get_current_identity(
            None
        )

    assert (
        exc_info.value.status_code
        == 401
    )

    assert (
        exc_info.value.detail
        == "Authentication required."
    )


def test_regular_user_cannot_use_admin_endpoint(
) -> None:

    identity = AuthIdentity(
        user_id=1,
        role="user",
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:

        catalog_require_admin(
            identity
        )

    assert (
        exc_info.value.status_code
        == 403
    )

    assert (
        exc_info.value.detail
        == (
            "Administrator role "
            "required."
        )
    )


def test_admin_is_authorized(
) -> None:

    identity = AuthIdentity(
        user_id=1,
        role="admin",
    )

    result = (
        catalog_require_admin(
            identity
        )
    )

    assert result == identity