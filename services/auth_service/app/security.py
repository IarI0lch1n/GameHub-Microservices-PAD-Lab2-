from datetime import (
    datetime,
    timedelta,
    timezone,
)

from uuid import uuid4

import jwt

from jwt.exceptions import (
    InvalidTokenError,
)

from pwdlib import (
    PasswordHash,
)

from shared.config.settings import (
    settings,
)


password_hasher = (
    PasswordHash.recommended()
)


#
# Dummy hash makes login timing more similar
# for existing and non-existing accounts.
#

DUMMY_PASSWORD_HASH = (
    password_hasher.hash(
        "gamehub-dummy-password"
    )
)


class TokenValidationError(
    ValueError
):
    pass


def validate_security_configuration(
) -> None:

    if (
        not settings.jwt_secret_key
        or settings.jwt_secret_key
        == "change-me-in-local-env"
    ):

        raise RuntimeError(
            (
                "JWT_SECRET_KEY is not "
                "configured. Generate a "
                "secret and place it in "
                "the local .env file."
            )
        )


def hash_password(
    password: str,
) -> str:

    return (
        password_hasher.hash(
            password
        )
    )


def verify_password(
    password: str,
    password_hash: str,
) -> bool:

    try:

        return (
            password_hasher.verify(
                password,
                password_hash,
            )
        )

    except Exception:

        return False


def verify_dummy_password(
    password: str,
) -> None:
    """
    Used when an account does not exist,
    reducing trivial timing differences
    during login.
    """

    try:

        password_hasher.verify(
            password,
            DUMMY_PASSWORD_HASH,
        )

    except Exception:

        pass


def _create_token(
    *,
    user_id: int,
    role: str,
    token_type: str,
    expires_delta: timedelta,
) -> str:

    now = datetime.now(
        timezone.utc
    )

    expires_at = (
        now
        + expires_delta
    )

    payload = {
        #
        # JWT subject should be a string.
        #
        "sub": str(
            user_id
        ),

        "role": role,

        "type": (
            token_type
        ),

        "jti": str(
            uuid4()
        ),

        "iat": now,

        "exp": (
            expires_at
        ),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=(
            settings.jwt_algorithm
        ),
    )


def create_access_token(
    *,
    user_id: int,
    role: str,
) -> str:

    return _create_token(
        user_id=user_id,
        role=role,
        token_type="access",
        expires_delta=timedelta(
            minutes=(
                settings
                .access_token_expire_minutes
            )
        ),
    )


def create_refresh_token(
    *,
    user_id: int,
    role: str,
) -> str:

    return _create_token(
        user_id=user_id,
        role=role,
        token_type="refresh",
        expires_delta=timedelta(
            days=(
                settings
                .refresh_token_expire_days
            )
        ),
    )


def create_token_pair(
    *,
    user_id: int,
    role: str,
) -> dict:

    return {
        "access_token": (
            create_access_token(
                user_id=user_id,
                role=role,
            )
        ),

        "refresh_token": (
            create_refresh_token(
                user_id=user_id,
                role=role,
            )
        ),

        "token_type": "bearer",

        "expires_in": (
            settings
            .access_token_expire_minutes
            * 60
        ),
    }


def decode_token(
    token: str,
    *,
    expected_type: str,
) -> dict:

    try:

        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[
                settings.jwt_algorithm
            ],
        )

    except InvalidTokenError as exc:

        raise TokenValidationError(
            "Invalid or expired token."
        ) from exc

    token_type = payload.get(
        "type"
    )

    if (
        token_type
        != expected_type
    ):

        raise TokenValidationError(
            (
                "Unexpected token type. "
                f"Expected "
                f"'{expected_type}'."
            )
        )

    subject = payload.get(
        "sub"
    )

    if not subject:

        raise TokenValidationError(
            (
                "Token does not contain "
                "a subject."
            )
        )

    try:

        user_id = int(
            subject
        )

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise TokenValidationError(
            (
                "Token subject is invalid."
            )
        ) from exc

    payload[
        "user_id"
    ] = user_id

    return payload