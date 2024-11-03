from fastapi import APIRouter, Depends, Response, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from src.app.schemas.auth import (
    User,
    UserCreate,
    Token,
    AuthTokenORMSchema,
    UserRole,
)
from src.app.services.user import UserService
from src.app.utils.static.auth_crypto import role_access, role_active_access


router = APIRouter(prefix="/auth", tags=["Authorisation"])


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=User
)
async def register(user: UserCreate):
    return await UserService.register_new_user(user)


@router.post("/login")
async def login(
    response: Response, credentials: OAuth2PasswordRequestForm = Depends()
):
    return await UserService.login_user(
        response, credentials.username, credentials.password
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
):
    await UserService.logout(response, request)
    return {"message": "Logged out successfully"}


@router.post("/refresh")
async def refresh_token(request: Request, response: Response) -> Token:
    return await UserService.refresh_token(response, request)


@router.post("/abort")
@role_active_access(
    allowed_roles={UserRole.SuperUserRole, UserRole.OrgLeaderRole}
)
async def abort_all_sessions(
    request: Request,
    response: Response,
) -> list[AuthTokenORMSchema]:
    return await UserService.abort_all_sessions(response, request)