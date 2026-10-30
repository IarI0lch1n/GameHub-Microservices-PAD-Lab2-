from typing import (
    Annotated,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from sqlalchemy.exc import (
    IntegrityError,
)

from sqlalchemy.orm import (
    Session,
)

from services.auth_service.app.database import (
    get_db,
)

from services.auth_service.app.messaging import (
    publish_user_registered,
)

from services.auth_service.app.repository import (
    UserRepository,
)

from services.auth_service.app.schemas import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
    UserResponse,
)

from services.auth_service.app.security import (
    TokenValidationError,
    create_token_pair,
    decode_token,
    hash_password,
    verify_dummy_password,
    verify_password,
)

from shared.logging.setup import (
    get_logger,
)


SERVICE_NAME = "auth-service"


router = APIRouter(
    prefix="/api/auth",
    tags=[
        "Authentication",
    ],
)


bearer_scheme = HTTPBearer(
    auto_error=False
)


def _logger():
    return get_logger(
        SERVICE_NAME
    )


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials
        | None,
        Depends(
            bearer_scheme
        ),
    ],
    db: Annotated[
        Session,
        Depends(
            get_db
        ),
    ],
):
    if (
        credentials is None
        or credentials.scheme.lower()
        != "bearer"
    ):
        raise HTTPException(
            status_code=(
                status
                .HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Authentication required."
            ),
            headers={
                "WWW-Authenticate": (
                    "Bearer"
                )
            },
        )

    try:
        payload = decode_token(
            credentials.credentials,
            expected_type="access",
        )

    except TokenValidationError:
        raise HTTPException(
            status_code=(
                status
                .HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid or expired "
                "access token."
            ),
            headers={
                "WWW-Authenticate": (
                    "Bearer"
                )
            },
        )

    repository = UserRepository(
        db
    )

    user = repository.get_by_id(
        payload[
            "user_id"
        ]
    )

    if (
        user is None
        or not user.is_active
    ):
        raise HTTPException(
            status_code=(
                status
                .HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "User account is "
                "not available."
            ),
        )

    return user


@router.post(
    "/register",
    response_model=(
        AuthResponse
    ),
    status_code=(
        status.HTTP_201_CREATED
    ),
    summary="Register a new account",
)
async def register(
    payload: RegisterRequest,
    request: Request,
    db: Annotated[
        Session,
        Depends(
            get_db
        ),
    ],
):
    repository = UserRepository(
        db
    )

    existing_user = (
        repository.get_by_email(
            str(
                payload.email
            )
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "An account with this "
                "email already exists."
            ),
        )

    password_hash = (
        hash_password(
            payload.password
        )
    )

    try:
        user = repository.create(
            email=str(
                payload.email
            ),
            password_hash=(
                password_hash
            ),
            role="user",
        )

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "An account with this "
                "email already exists."
            ),
        )

    tokens = create_token_pair(
        user_id=user.id,
        role=user.role,
    )

    #
    # Publish asynchronous integration event.
    #

    await publish_user_registered(
        user=user,
        correlation_id=(
            request.state
            .correlation_id
        ),
    )

    _logger().info(
        "user_registered",
        user_id=user.id,
        email=user.email,
        request_id=getattr(
            request.state,
            "request_id",
            None,
        ),
        correlation_id=getattr(
            request.state,
            "correlation_id",
            None,
        ),
    )

    return AuthResponse(
        user=UserResponse.model_validate(
            user
        ),
        tokens=TokenPairResponse(
            **tokens
        ),
    )


@router.post(
    "/login",
    response_model=(
        AuthResponse
    ),
    summary=(
        "Login with email and password"
    ),
)
def login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[
        Session,
        Depends(
            get_db
        ),
    ],
):
    repository = UserRepository(
        db
    )

    user = repository.get_by_email(
        str(
            payload.email
        )
    )

    if user is None:
        verify_dummy_password(
            payload.password
        )

        raise HTTPException(
            status_code=(
                status
                .HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid email or password."
            ),
        )

    if not verify_password(
        payload.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=(
                status
                .HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid email or password."
            ),
        )

    if not user.is_active:
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "User account is disabled."
            ),
        )

    tokens = create_token_pair(
        user_id=user.id,
        role=user.role,
    )

    _logger().info(
        "user_logged_in",
        user_id=user.id,
        email=user.email,
        request_id=getattr(
            request.state,
            "request_id",
            None,
        ),
    )

    return AuthResponse(
        user=UserResponse.model_validate(
            user
        ),
        tokens=TokenPairResponse(
            **tokens
        ),
    )


@router.post(
    "/refresh",
    response_model=(
        TokenPairResponse
    ),
    summary=(
        "Refresh authentication tokens"
    ),
)
def refresh(
    payload: RefreshRequest,
    db: Annotated[
        Session,
        Depends(
            get_db
        ),
    ],
):
    try:
        token_payload = (
            decode_token(
                payload.refresh_token,
                expected_type=(
                    "refresh"
                ),
            )
        )

    except TokenValidationError:
        raise HTTPException(
            status_code=(
                status
                .HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid or expired "
                "refresh token."
            ),
        )

    repository = UserRepository(
        db
    )

    user = repository.get_by_id(
        token_payload[
            "user_id"
        ]
    )

    if (
        user is None
        or not user.is_active
    ):
        raise HTTPException(
            status_code=(
                status
                .HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "User account is "
                "not available."
            ),
        )

    tokens = create_token_pair(
        user_id=user.id,
        role=user.role,
    )

    return TokenPairResponse(
        **tokens
    )


@router.get(
    "/me",
    response_model=(
        UserResponse
    ),
    summary=(
        "Get authenticated identity"
    ),
)
def me(
    current_user=Depends(
        get_current_user
    ),
):
    return UserResponse.model_validate(
        current_user
    )