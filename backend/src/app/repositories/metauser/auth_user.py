# from src.app.models.user import User
from ...utils.repository import SQLAlchemyRepository
from src.app.models.users.auth_auth import UserORM
from sqlalchemy import insert, select, update
from src.app.schemas.auth import (
    UserCreateDB,
    User,
    UserUpdate,
    UsersFindRequest,
)
import uuid


class AuthRepository(SQLAlchemyRepository):
    model = UserORM

    async def find_one_or_none_user(self, *filter, **filter_by) -> User | None:
        stmt = select(self.model).filter(*filter).filter_by(**filter_by)
        result = (await self.session.execute(stmt)).scalars().one_or_none()
        if result:
            return result.get_schema()
        return None

    async def add_one_user(self, user: UserCreateDB) -> User:
        stmt = insert(self.model).values(dict(user)).returning(self.model)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update_user(
        self, cur_user_id: uuid.UUID, user_update: UserUpdate
    ) -> User:
        stmt = (
            update(self.model)
            .where(self.model.id == cur_user_id)
            .values(dict(user_update))
            .returning(self.model)
        )
        return (await self.session.execute(stmt)).scalars().one()

    async def activeness_switcher(
        self, cur_user_id: uuid.UUID, activeness: bool
    ) -> User:
        stmt = (
            update(self.model)
            .where(self.model.id == cur_user_id)
            .values(is_active=activeness)
            .returning(self.model)
        )
        return (await self.session.execute(stmt)).scalars().one()

    async def find_all_users(self, find_request: UsersFindRequest | None) -> list[User]:
        stmt = (
            select(self.model)
            .offset(find_request.paginate.offset)
            .limit(find_request.paginate.limit)
            .filter_by(
                **{
                    k: v
                    for k, v in (dict(find_request.filters).items())
                    if v is not None
                }
            )
        )
        result = (await self.session.execute(stmt)).scalars().all()
        return [i.get_schema() for i in result]