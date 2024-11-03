from ...utils.repository import SQLAlchemyRepository

import uuid

from typing import Optional
from src.app.models.users.auth_token import AuthTokenORM
from sqlalchemy import delete, insert, select, update
from src.app.schemas.auth import RefreshSessionCreate, AuthTokenORMSchema


class AuthTokenRepository(SQLAlchemyRepository):
    model = AuthTokenORM

    async def add_token(
        self, token_refresh: RefreshSessionCreate
    ) -> Optional[AuthTokenORMSchema]:
        stmt = insert(self.model).values(dict(token_refresh)).returning(self.model)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def find_one_or_none_token(
        self, *filter, **filter_by
    ) -> AuthTokenORMSchema | None:
        stmt = select(self.model).filter(*filter).filter_by(**filter_by)
        result = await self.session.execute(stmt)
        return result.scalars().one_or_none()

    async def logout_delete_token(self, token_id: int):
        stmt = delete(self.model).where(self.model.id == token_id)
        result = await self.session.execute(stmt)

    async def update_token(
        self, token_id: int, refresh_token: str, expires_in_seconds: float
    ) -> AuthTokenORMSchema:
        stmt = (
            update(self.model)
            .where(self.model.id == token_id)
            .values(refresh_token=refresh_token, expires_in=expires_in_seconds)
            .returning(self.model)
        )
        await self.session.commit()
        return (await self.session.execute(stmt)).scalars().one()

    async def delete_all_tokens_by_user_id(
        self,
        user_id: uuid.UUID,
    ) -> list[AuthTokenORMSchema]:
        stmt = (
            delete(self.model)
            .where(self.model.user_id == user_id)
            .returning(self.model)
        )
        result = (await self.session.execute(stmt)).scalars().all()
        return [i.get_schema() for i in result]