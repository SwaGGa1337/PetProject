from typing import Any, Dict
from typing_extensions import Annotated, Doc
from fastapi import HTTPException, status


class DataBase404Exception(HTTPException):
    def __init__(self, base: Any, value: Any) -> None:
        detail = f"Not found in {base} data with primary key = {value}"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class SmileRoomNotPromoException(HTTPException):
    def __init__(self, id: int, promo: str) -> None:
        detail = f"Product with id:{id} is not in promo '{promo}'"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class DataBase409Exception(HTTPException):
    def __init__(self, message: Any) -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=message)


class DataBaseException(HTTPException):
    def __init__(self, message: Any) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=message)


class UnavailableLoginException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Login is not available",
        )


class InvalidTokenException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


class TokenExpiredException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )


class InvalidCredentialsException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invalid username or password",
        )



class UserNotActiveException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN, detail="User is not active"
        )


class UserNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


class UserNotAuthorizedException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )


class UserPrivilegesException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
        )


class EnumExistenceException(HTTPException):
    def __init__(self, invalid_enum: str, enum_schema_name: str):
        detail = f"Enum {invalid_enum} doesn`t exist in {enum_schema_name}"
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail
        )


class StoriesContentError(HTTPException):
    def __init__(self, story_id: int, msg: str):
        detail = f"Story ({story_id}) error with content:{msg}"
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail
        )