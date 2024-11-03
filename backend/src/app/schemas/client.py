from src.app.schemas.types import Login, Str_20, Telephone, Password, ID
from typing import Optional
from pydantic import BaseModel, EmailStr, UUID4


class AnswerBase(BaseModel):
    message: str


class ClientFullData(BaseModel):
    id: ID
    login: Optional[Login]
    vk_id: Optional[str]
    name: Optional[Str_20]
    surname: Optional[Str_20]
    patronymic: Optional[Str_20]
    telephone: Optional[Telephone]
    email: Optional[EmailStr]
    is_active: bool

    class Config:
        from_attributes = True


class CreateClientRequest(BaseModel):
    login: Login


class CreateVKClient(BaseModel):
    vk_id: str
    name: Optional[Str_20]
    surname: Optional[Str_20]
    patronymic: Optional[Str_20]
    telephone: Optional[Telephone]


class LoginPassword(BaseModel):
    vk_id: str
    login: Login
    password: Password


class GetDataRequest(BaseModel):
    vk_id: Optional[str]
    login: Optional[Login]