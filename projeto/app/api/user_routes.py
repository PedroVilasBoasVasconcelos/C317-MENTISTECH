from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, get_current_user_bearer
from app.db.models.user import User
from app.schemas.auth_schemas import AuthUserResponse

user_router = APIRouter(prefix="/usuarios", tags=["usuarios"])


from fastapi import Security


@user_router.get("/me", response_model=AuthUserResponse)
def get_me(
    current_user: User = Security(get_current_user, scopes=[]),
    current_user_bearer: User = Security(get_current_user_bearer, scopes=[]),
):
    user = current_user or current_user_bearer
    return AuthUserResponse(
        id=user.id,
        name=user.full_name,
        email=user.corporate_email,
        role=user.role,
        team=user.team.name if user.team else None,
    )
