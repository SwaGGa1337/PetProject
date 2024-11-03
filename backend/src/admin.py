from typing import Union
from urllib import response

import wtforms
from fastapi.openapi.models import Response

from sqladmin import Admin
from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend
from fastapi import Request, Response


from src.app.schemas.types import UserRole
from src.app.services.user import UserService
from src.database.all_models import (
    ClientORM,
    UserORM,
    AuthTokenORM,
)


class MyBackend(AuthenticationBackend):

    async def login(self, request: Request) -> Union[bool, str]:
        form = await request.form()
        username, password = form["username"], form["password"]

        token = await UserService.login_user(response, username, password)
        
        if not token:
            return "Invalid username or password"
        
        user = await UserService.get_user_by_id(token.user_id)
        
        if user.role != UserRole.SuperUserRole:
            return "User is not a Super User"

        request.session["token"] = "token.access_token"
        return True

    async def logout(self, request: Request) -> Union[bool, str]:
        request.session.clear()
        return "Logged out successfully"

    async def authenticate(self, request: Request) -> bool:
        return "token" in request.session


class BaseModelView(ModelView):
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    can_export = True
    page_size = 100


class ClientsAdmin(BaseModelView, model=ClientORM):
    name = "Клиент"
    name_plural = "Клиенты"
    #
    column_list = [
        ClientORM.id,
        ClientORM.vk_id,
        ClientORM.email,
        ClientORM.telephone,
        ClientORM.name,
    ]



class UserAdmin(BaseModelView, model=UserORM):
    name = "Пользователь"
    name_plural = "Пользователи"

    column_list = [
        UserORM.id,
        UserORM.login,
        UserORM.hashed_password,
        UserORM.role,
        UserORM.client,
    ]


class TokenAdmin(BaseModelView, model=AuthTokenORM):
    name = "Токен"
    name_plural = "Токены"

    column_list = [
        AuthTokenORM.id,
        AuthTokenORM.refresh_token,
        AuthTokenORM.expires_in,
        AuthTokenORM.created_at,
    ]





def create_admin(app, engine):
    authentication_backend = MyBackend(secret_key="...")

    admin = Admin(
        app,
        engine,
        title="KOKOS",
        authentication_backend=authentication_backend,
    )
    admin.add_view(ClientsAdmin)

    return admin