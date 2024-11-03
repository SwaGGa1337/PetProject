from typing import Optional

from fastapi import HTTPException, status, Request, Response

import uuid

from sqlalchemy.exc import IntegrityError

from src.app.utils.unitofwork import IUnitOfWork, UnitOfWork
from src.app.schemas.auth import (
    UserCreate,
    UserCreateDB,
    User,
    Token,
    RefreshSessionCreate,
    AuthTokenORMSchema,
    UserUpdate,
    UserRole,
    UsersFindRequest,
)
from src.app.utils.static.auth_crypto import (
    TokenUtils,
    PasswordStatic,
    CookieUtils,
)
from src.app.repositories.exceptions import (
    InvalidCredentialsException,
    UserNotActiveException,
    InvalidTokenException,
    TokenExpiredException,
    UserPrivilegesException,
    UserNotFoundException,
    UnavailableLoginException,
)
from src.app.schemas.auth import TokenAccessRefreshCreate


class UserService:
    @classmethod
    async def register_new_user(
        cls, user: UserCreate, uow: IUnitOfWork = UnitOfWork()
    ) -> User:
        async with uow:
            user_exist = await uow.auth.find_one_or_none_user(login=user.login)
            if user_exist:
                raise UnavailableLoginException
            
            if user.role == "SuperUserRole":
                raise HTTPException(
                    status_code=400,
                    detail="SuperUser not approved"
                )
            
            try:
                db_user = await uow.auth.add_one_user(
                    user=UserCreateDB(
                        **user.model_dump(),
                        hashed_password=PasswordStatic.get_password_hash(
                            user.password
                        )
                    )
                )
            except IntegrityError:
                raise UnavailableLoginException
            
            await uow.commit()
            return db_user  # Не забудьте вернуть созданного пользователя

    @classmethod
    async def authenticate_user(
        cls, login: str, password: str, uow: IUnitOfWork = UnitOfWork()
    ) -> Optional[User]:
        async with uow:
            db_user = await uow.auth.find_one_or_none_user(login=login)
            if db_user and PasswordStatic.is_valid_password(
                password, db_user.hashed_password
            ):
                return db_user
            return None

    @classmethod
    async def login_user(
        cls,
        response: Response,
        login: str,
        password: str,
        uow: IUnitOfWork = UnitOfWork(),
    ) -> Optional[Token]:
        async with uow:
            db_user = await uow.auth.find_one_or_none_user(login=login)
            if not (
                db_user
                and PasswordStatic.is_valid_password(
                    password, db_user.hashed_password
                )
            ):
                raise InvalidCredentialsException

            token_create: TokenAccessRefreshCreate = (
                await TokenUtils.access_refresh_tokens_creator(
                    user_id=db_user.id,
                    user_role=db_user.role,
                    is_active=db_user.is_active,
                )
            )

            await uow.token.add_token(
                RefreshSessionCreate(
                    user_id=db_user.id,
                    refresh_token=token_create.refresh_token,
                    expires_in=token_create.refresh_token_expires.total_seconds(),
                )
            )

            CookieUtils.access_refresh_cookies_setter(
                response, token_create.access_token, token_create.refresh_token
            )
            await uow.commit()
            return Token(
                access_token=token_create.access_token,
                refresh_token=token_create.refresh_token,
                token_type="bearer",
            )

    @classmethod
    async def logout(
        cls,
        response: Response,
        request: Request,
        uow: IUnitOfWork = UnitOfWork(),
    ) -> bool:
        """
        1)get current token
        2)get decoded user_id from token
        3)get user by user_id
        4)delete users token from TokenDB
        """
        async with uow:
            token_dependency = await TokenUtils.token_user_dependency(request)
            if token_dependency.is_active == False:
                raise UserNotActiveException

            refresh_session = await uow.token.find_one_or_none_token(
                refresh_token=request.cookies.get("refresh_token")
            )
            if refresh_session:
                await uow.token.logout_delete_token(refresh_session.id)
                await uow.commit()
                CookieUtils.access_refresh_cookies_deleter(response)
                return True
            return False

    @classmethod
    async def delete_current_user(
        cls,
        response: Response,
        request: Request,
        uow: IUnitOfWork = UnitOfWork(),
    ) -> bool:
        """
        1)get current token
        2)get decoded user_id from token
        3)get user by user_id
        4)delete users token from TokenDB
        5)deactivate user
        """
        async with uow:
            token_dependency = await TokenUtils.token_user_dependency(request)

            current_user = await uow.auth.find_one_or_none_user(
                id=token_dependency.user_id
            )
            if current_user.is_active == False:
                raise UserNotActiveException

            refresh_session = await uow.token.find_one_or_none_token(
                refresh_token=request.cookies.get("refresh_token")
            )
            await uow.token.logout_delete_token(refresh_session.id)
            deleted_user = await uow.auth.activeness_switcher(
                current_user.id, False
            )
            CookieUtils.access_refresh_cookies_deleter(response)
            await uow.commit()
            return deleted_user

    @classmethod
    async def delete_user_by_id(
        cls,
        request: Request,
        user_id_to_delete: uuid.UUID,
        uow: IUnitOfWork = UnitOfWork(),
    ) -> bool:
        """
        1)get current token
        2)get decoded cur_user_id from token
        3)check cur_user privelegies
        4)delete del_users token from TokenDB
        5)deactivate del_user
        """
        async with uow:
            token_dependency = await TokenUtils.token_user_dependency(request)

            current_user = await uow.auth.find_one_or_none_user(
                id=token_dependency.user_id
            )
            if current_user.is_active == False:
                raise UserNotActiveException
            if current_user.role != UserRole.SuperUserRole:
                raise UserPrivilegesException

            refresh_session = await uow.token.find_one_or_none_token(
                user_id=user_id_to_delete
            )
            if refresh_session:
                await uow.token.logout_delete_token(refresh_session.id)
                deleted_user = await uow.auth.activeness_switcher(
                    user_id_to_delete, False
                )
                await uow.commit()
                return deleted_user

    @classmethod
    async def refresh_token(
        cls,
        response: Response,
        request: Request,
        uow: IUnitOfWork = UnitOfWork(),
    ) -> Token:
        """
        get current refresh token
        get session by refresh token
            if session None:
                raise InToEx
            if time expired:
                raise
        get user by session.user_id
            if user is None:
                raise
        create acctoken
        create refresh token
        update tokenDB
        return Token
        """
        async with uow:
            refresh_token = request.cookies.get("refresh_token")

            refresh_session = await uow.token.find_one_or_none_token(
                refresh_token=refresh_token
            )
            if refresh_session is None:
                raise InvalidTokenException
            if TokenUtils.is_auth_session_expired(refresh_session):
                await uow.token.logout_delete_token(id=refresh_session.id)
                raise TokenExpiredException

            user = await uow.auth.find_one_or_none_user(
                id=refresh_session.user_id
            )
            if user is None:
                raise InvalidTokenException

            token_creator: TokenAccessRefreshCreate = (
                await TokenUtils.access_refresh_tokens_creator(
                    user_id=user.id,
                    user_role=user.role,
                    is_active=user.is_active,
                )
            )

            updater = await uow.token.update_token(
                token_id=refresh_session.id,
                refresh_token=token_creator.refresh_token,
                expires_in_seconds=token_creator.refresh_token_expires.total_seconds(),
            )

            CookieUtils.access_refresh_cookies_setter(
                response,
                token_creator.access_token,
                token_creator.refresh_token,
            )
            await uow.commit()
            return Token(
                access_token=token_creator.access_token,
                refresh_token=token_creator.refresh_token,
                token_type="bearer",
            )

    @classmethod
    async def abort_all_sessions(
        cls,
        response: Response,
        request: Request,
        uow: IUnitOfWork = UnitOfWork(),
    ) -> list[AuthTokenORMSchema]:
        async with uow:
            token_dependency = await TokenUtils.token_user_dependency(request)
            aborted_sessions = await uow.token.delete_all_tokens_by_user_id(
                user_id=token_dependency.user_id
            )
            await uow.commit()

            CookieUtils.access_refresh_cookies_deleter(response)
            return aborted_sessions

    @classmethod
    async def get_current_user(
        cls, request: Request, uow: IUnitOfWork = UnitOfWork()
    ) -> User:
        """
        1)get current token
        2)get decoded user_id from token
        3)get user by current_user_id
        """
        async with uow:
            token_dependency = await TokenUtils.token_user_dependency(request)
            current_user = await uow.auth.find_one_or_none_user(
                id=token_dependency.user_id
            )
            if current_user.is_active == False:
                raise UserNotActiveException
            return current_user

    @classmethod
    async def get_user_by_id(
        cls, request: Request, user_id: int, uow: IUnitOfWork = UnitOfWork()
    ) -> User:
        """
        1)get current token
        2)get decoded user_id from token, check
        3)get another user by user_id
        """
        async with uow:
            token_dependency = await TokenUtils.token_user_dependency(request)
            current_user = await uow.auth.find_one_or_none_user(
                id=token_dependency.user_id
            )
            if current_user.is_active == False:
                raise UserNotActiveException
            if current_user.role != UserRole.SuperUserRole:
                raise UserPrivilegesException

            user = await uow.auth.find_one_or_none_user(id=user_id)
            if user is None:
                raise UserNotFoundException
            return user

    @classmethod
    async def update_user(
        self,
        user_update: UserUpdate,
        request: Request,
        uow: IUnitOfWork = UnitOfWork(),
    ) -> User:
        """
        0)check superuser
        1)get current token
        2)get decoded user_id from token
        3)get user by user_id
        4)update user data (returning)
        """
        async with uow:
            token_dependency = await TokenUtils.token_user_dependency(request)
            current_user = await uow.auth.find_one_or_none_user(
                id=token_dependency.user_id
            )

            if current_user.is_active == False:
                raise UserNotActiveException
            if current_user.role != UserRole.SuperUserRole:
                raise UserPrivilegesException

            user_update = await uow.auth.update_user(
                current_user.id, user_update
            )
            return user_update

    @classmethod
    async def update_user_by_id(
        self,
        user_id: uuid.UUID,
        user_update: UserUpdate,
        request: Request,
        uow: IUnitOfWork = UnitOfWork(),
    ) -> User:
        """
        0)check superuser
        1)get current token
        2)get decoded user_id from token
        3)get user by user_id
        4)update user data (returning)
        """
        async with uow:
            token_dependency = await TokenUtils.token_user_dependency(request)
            current_user = await uow.auth.find_one_or_none_user(
                id=token_dependency.user_id
            )

            if current_user.is_active == False:
                raise UserNotActiveException
            if current_user.role != UserRole.SuperUserRole:
                raise UserPrivilegesException

            user_update = await uow.auth.update_user(user_id, user_update)
            return user_update

    @classmethod
    async def get_users_list(
        self,
        request: Request,
        find_request: UsersFindRequest,
        uow: IUnitOfWork = UnitOfWork(),
    ) -> list[User]:
        async with uow:
            token_dependency = await TokenUtils.token_user_dependency(request)
            current_user = await uow.auth.find_one_or_none_user(
                id=token_dependency.user_id
            )

            if current_user.is_active == False:
                raise UserNotActiveException
            if current_user.role != UserRole.SuperUserRole:
                raise UserPrivilegesException

            users = await uow.auth.find_all_users(find_request)
            if not users:
                raise UserNotFoundException
            return users

    @classmethod
    async def register_new_admin_user(
        cls, user: UserCreate, uow: IUnitOfWork = UnitOfWork()
    ) -> User:
        async with uow:
            user_exist = await uow.auth.find_one_or_none_user(login=user.login)
            if user_exist:
                raise UnavailableLoginException
            try:
                db_user = await uow.auth.add_one_user(
                    user=UserCreateDB(
                        login=user.login,
                        hashed_password=PasswordStatic.get_password_hash(
                            user.password
                        ),
                        role=UserRole.SuperUserRole,
                    )
                )
            except IntegrityError:
                raise UnavailableLoginException
            await uow.commit()
