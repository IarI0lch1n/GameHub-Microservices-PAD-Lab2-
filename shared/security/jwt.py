from dataclasses import (
    dataclass,
)

import jwt

from jwt.exceptions import (
    InvalidTokenError,
)

from shared.config.settings import (
    settings,
)


@dataclass(frozen=True)
class AuthIdentity:
    user_id: int
    role: str


class AccessTokenError(
    ValueError
):
    pass


def decode_access_token(
    token: str,
) -> AuthIdentity:
    """
    Validate a GameHub access token.

    Services may validate JWTs locally
    without querying the Auth Service.
    """

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[
                settings.jwt_algorithm
            ],
        )

    except InvalidTokenError as exc:
        raise AccessTokenError(
            "Invalid or expired access token."
        ) from exc

    if (
        payload.get("type")
        != "access"
    ):
        raise AccessTokenError(
            "The supplied token is not an access token."
        )

    subject = payload.get(
        "sub"
    )

    if subject is None:
        raise AccessTokenError(
            "Access token has no subject."
        )

    try:
        user_id = int(
            subject
        )

    except (
        TypeError,
        ValueError,
    ) as exc:
        raise AccessTokenError(
            "Invalid access token subject."
        ) from exc

    role = str(
        payload.get(
            "role",
            "user",
        )
    )

    return AuthIdentity(
        user_id=user_id,
        role=role,
    )