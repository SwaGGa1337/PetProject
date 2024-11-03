from typing import Dict, Optional, Callable
import bcrypt
import uuid
from datetime import timedelta, datetime, timezone
from jose import jwt

from fastapi import Request, Response
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param

from src.app_config.app_settings import app_settings
from src.app.repositories.exceptions import (
    InvalidTokenException,
    UserNotAuthorizedException,
    UserPrivilegesException,
    UserNotActiveException,
)
from src.app.schemas.auth import (
    DependentToken,
    AuthTokenORMSchema,
    TokenAccessRefreshCreate,
    UserRole,
)
import functools


def role_access(allowed_roles: set):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            user_access_cookie = await TokenUtils.token_user_dependency(
                request
            )
            if user_access_cookie.role not in allowed_roles:
                raise UserPrivilegesException()

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def role_active_access(allowed_roles: set):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            user_access_cookie = await TokenUtils.token_user_dependency(
                request
            )
            if user_access_cookie.role not in allowed_roles:
                raise UserPrivilegesException()
            if not bool(user_access_cookie.is_active):
                raise UserNotActiveException

            return await func(*args, **kwargs)

        return wrapper

    return decorator


class CryptoUserStatic(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(
            password={"tokenUrl": tokenUrl, "scopes": scopes}
        )
        super().__init__(
            flows=flows, scheme_name=scheme_name, auto_error=auto_error
        )

    async def __call__(self, request: Request) -> Optional[str]:
        authorization: str = request.cookies.get("access_token")
        scheme, param = get_authorization_scheme_param(authorization)

        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                return False
            else:
                return None
        return param


class PasswordStatic:
    @staticmethod
    def is_valid_password(plain_password: str, hashed_password: str) -> bool:
        return PasswordStatic._verify_password(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return PasswordStatic._hash_password(password)

    @staticmethod
    def _verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    @staticmethod
    def _hash_password(password: str) -> str:
        return bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")


class TokenUtils:
    @staticmethod
    def create_access_token(
        user_id: uuid.UUID, user_role: UserRole, is_active: bool
    ) -> str:
        to_encode = {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=app_settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            "role": str(user_role.value),
            "is_active": is_active,
        }
        encoded_jwt = jwt.encode(
            to_encode,
            app_settings.SECRET_KEY,
            algorithm=app_settings.ALGORITHM,
        )
        return f"Bearer {encoded_jwt}"

    @staticmethod
    def is_auth_session_expired(access_session: AuthTokenORMSchema):
        return datetime.now(
            timezone.utc
        ) >= access_session.created_at + timedelta(
            seconds=access_session.expires_in
        )

    @staticmethod
    def create_refresh_token() -> str:
        return uuid.uuid4()

    @staticmethod
    def token_expire_time():
        return timedelta(days=app_settings.REFRESH_TOKEN_EXPIRE_DAYS)

    @staticmethod
    async def token_user_dependency(
        request: Request,
    ) -> DependentToken:
        token = await oauth2_scheme(request)
        if token == False:
            raise UserNotAuthorizedException

        payload = jwt.decode(
            token, app_settings.SECRET_KEY, algorithms=[app_settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        role = payload.get("role")
        is_active = payload.get("is_active")
        if user_id is None or role is None or is_active is None:
            raise InvalidTokenException

        return DependentToken(
            token=token,
            user_id=user_id,
            role=UserRole(role),
            is_active=is_active,
        )

    @staticmethod
    async def access_refresh_tokens_creator(
        user_id: uuid.UUID, user_role: UserRole, is_active: bool
    ):
        return TokenAccessRefreshCreate(
            access_token=TokenUtils.create_access_token(
                user_id, user_role, is_active
            ),
            refresh_token_expires=TokenUtils.token_expire_time(),
            refresh_token=TokenUtils.create_refresh_token(),
        )


class CookieUtils:
    @staticmethod
    def cookie_setter(response: Response, token: str, name: str):
        """
        Sets refresh cookie to fastapi response
        """
        match name:
            case "refresh_token":
                response.set_cookie(
                    "refresh_token",
                    token,
                    max_age=app_settings.REFRESH_TOKEN_EXPIRE_DAYS
                    * 30
                    * 24
                    * 60,
                    httponly=True,
                    samesite="none",
                    secure=True,
                )
            case "access_token":
                response.set_cookie(
                    "access_token",
                    token,
                    max_age=app_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                    httponly=True,
                    samesite="none",
                    secure=True,
                )

    @staticmethod
    def access_refresh_cookies_deleter(response: Response):
        response.delete_cookie("refresh_token")
        response.delete_cookie("access_token")

    @staticmethod
    def access_refresh_cookies_setter(
        response: Response, access: str, refresh: uuid.UUID
    ):
        CookieUtils.cookie_setter(response, access, "access_token")
        CookieUtils.cookie_setter(response, refresh, "refresh_token")


oauth2_scheme = CryptoUserStatic(tokenUrl="/api/auth/login")