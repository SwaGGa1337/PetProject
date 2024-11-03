from typing import List, Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String

from src.app.models.mixin import IsActiveMixin, CreationDateMixin
from src.app.schemas.client import ClientFullData

from src.database.database_metadata import Base
from src.database.types import str_20, INT_PK


class ClientORM(Base, CreationDateMixin, IsActiveMixin):
    __tablename__ = "clients"

    id: Mapped[INT_PK]
    login: Mapped[str_20]
    password: Mapped[str_20]
    vk_id: Mapped[str_20]
    name: Mapped[str_20]
    surname: Mapped[str_20]
    telephone: Mapped[str_20]
    email: Mapped[str_20]


    metauser: Mapped["UserORM"] = relationship(
        "UserORM", back_populates="client", foreign_keys="UserORM.client_id"
    )

    def get_schema(self) -> ClientFullData:
        return ClientFullData(
            id=self.id,
            login=self.login,
            vk_id=self.vk_id,
            name=self.name,
            surname=self.surname,
            telephone=self.telephone,
            email=self.email,
            creation_date=self.creation_date,
            is_active=self.is_active,
        )

    def __str__(self):
        return f"Клиент: {self.name} {self.surname} {self.vk_id}"