from datetime import (
    datetime,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
)


class UserProfileResponse(
    BaseModel
):
    id: int

    auth_user_id: int

    email: EmailStr

    display_name: (
        str
        | None
    )

    role: str

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )