from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, Response, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from src.app.schemas.auth import User, UserUpdate, UsersFindRequest, UserRole
from src.app.services.user import UserService
from src.app.utils.static.auth_crypto import role_active_access


router = APIRouter(prefix="/user", tags=["Users"])


@router.post("/list")
@role_active_access({UserRole.SuperUserRole})
async def get_users_list(
    request: Request,
    find_: UsersFindRequest,
) -> list[User]:
    return await UserService.get_users_list(request, find_)


@router.get("/me")
async def get_current_user(request: Request) -> User:
    return await UserService.get_current_user(request)


@router.put("/me")
@role_active_access({UserRole.SuperUserRole})
async def update_current_user(
    user: UserUpdate,
    request: Request,
) -> User:
    return await UserService.update_user(user, request)


@router.delete("/me")
@role_active_access({UserRole.SuperUserRole})
async def delete_current_user(
    request: Request,
    response: Response,
):
    await UserService.delete_current_user(response, request)
    return {"message": "User status is not active already"}


@router.get("/{user_id}")
@role_active_access({UserRole.SuperUserRole})
async def get_user(
    request: Request,
    user_id: str,
) -> User:
    return await UserService.get_user_by_id(request, user_id)


@router.put("/{user_id}")
@role_active_access({UserRole.SuperUserRole})
async def update_user(
    request: Request,
    user_id: str,
    user_data: UserUpdate,
) -> User:
    return await UserService.update_user_by_id(user_id, user_data, request)


@router.delete("/{user_id}")
@role_active_access({UserRole.SuperUserRole})
async def delete_user_by_id(
    request: Request,
    user_id_to_delete: uuid.UUID,
) -> User:
    return await UserService.delete_user_by_id(request, user_id_to_delete)