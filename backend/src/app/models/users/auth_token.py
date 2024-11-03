import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.database.database_metadata import Base
from src.database.types import INT_PK, UUID_C

from src.app.schemas.auth import AuthTokenORMSchema


class AuthTokenORM(Base):
    __tablename__ = "auth_refresh_session"

    id: Mapped[INT_PK]
    refresh_token: Mapped[UUID_C]
    expires_in: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("auth_user.id", ondelete="CASCADE")
    )

    def get_schema(self) -> AuthTokenORMSchema:
        return AuthTokenORMSchema(
            id=self.id,
            refresh_token=self.refresh_token,
            user_id=self.user_id,
            created_at=self.created_at,
            expires_in=self.expires_in,
        )