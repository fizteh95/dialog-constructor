import typing as tp

import pytest
from sqlalchemy import func, select

from src.adapters.alchemy.repository import SQLAlchemyRepo, users
from src.domain.model import User


@pytest.mark.asyncio
async def test_users_created(alchemy_repo: tp.Awaitable[SQLAlchemyRepo]) -> None:
    repo = await alchemy_repo
    async_session = repo.session()
    async with async_session() as session:
        user = await repo.get_or_create_user(outer_id="1", session=session)
        assert user == User(outer_id="1")
        user = await repo.get_or_create_user(outer_id="1_2", name="test", session=session)
        assert user == User(outer_id="1_2", name="test")
        user = await repo.get_or_create_user(outer_id="1", name="test2", session=session)
        assert user == User(outer_id="1")

        result = await session.execute(select(func.count()).select_from(select(users).subquery()))
        assert result.scalar_one() == 2
