import os
import typing as tp

import pytest
from sqlalchemy import func
from sqlalchemy import select

from src.adapters.alchemy.models import out_messages
from src.adapters.alchemy.models import projects
from src.adapters.alchemy.models import scenario_texts
from src.adapters.alchemy.models import scenarios
from src.adapters.alchemy.models import user_contexts
from src.adapters.alchemy.models import users
from src.adapters.alchemy.repository import SQLAlchemyRepo
from src.domain.model import Scenario
from src.domain.model import User


@pytest.mark.asyncio
async def test_users_created(alchemy_repo: tp.Awaitable[SQLAlchemyRepo]) -> None:
    repo = await alchemy_repo
    async_session = repo.session()
    async with async_session() as session:
        user = await repo.get_or_create_user(outer_id="1", session=session)
        assert user == User(outer_id="1")

        user = await repo.get_or_create_user(
            outer_id="1_2", name="test", session=session
        )
        assert user == User(outer_id="1_2", name="test")

        user = await repo.get_or_create_user(
            outer_id="1", name="test2", session=session
        )
        assert user == User(outer_id="1")

        result = await session.execute(
            select(func.count()).select_from(select(users).subquery())
        )
        assert result.scalar_one() == 2


@pytest.mark.asyncio
async def test_users_update(alchemy_repo: tp.Awaitable[SQLAlchemyRepo]) -> None:
    repo = await alchemy_repo
    async_session = repo.session()
    async with async_session() as session:
        user = await repo.get_or_create_user(outer_id="1", session=session)
        assert user == User(outer_id="1")

        new_user = await repo.get_or_create_user(
            outer_id="1_2", name="test", session=session
        )
        assert new_user == User(outer_id="1_2", name="test")

        user.nickname = "test nickname"
        await repo.update_user(user, session=session)
        user_from_db = await repo.get_or_create_user(outer_id="1", session=session)
        assert user_from_db != User(outer_id="1")
        assert user_from_db == User(outer_id="1", nickname="test nickname")

        result = await session.execute(
            select(func.count()).select_from(select(users).subquery())
        )
        assert result.scalar_one() == 2


@pytest.mark.asyncio
async def test_update_ctx(alchemy_repo: tp.Awaitable[SQLAlchemyRepo]) -> None:
    repo = await alchemy_repo
    async_session = repo.session()
    async with async_session() as session:
        user = await repo.get_or_create_user(outer_id="1", session=session)

        await repo.update_user_context(
            user=user, ctx_to_update={"first_key": "first_val"}, session=session
        )
        users_from_db = await session.execute(
            select(users).where(users.c.outer_id == user.outer_id)
        )
        user_from_db = users_from_db.first()
        result = await session.execute(
            select(user_contexts).where(user_contexts.c.user == user_from_db.id)
        )
        result = result.first()
        exists_context = result.ctx
        assert exists_context == {"first_key": "first_val"}

        await repo.update_user_context(
            user=user, ctx_to_update={"second_key": "second_val"}, session=session
        )
        users_from_db = await session.execute(
            select(users).where(users.c.outer_id == user.outer_id)
        )
        user_from_db = users_from_db.first()
        result = await session.execute(
            select(user_contexts).where(user_contexts.c.user == user_from_db.id)
        )
        result = result.first()
        exists_context = result.ctx
        assert exists_context == {"first_key": "first_val", "second_key": "second_val"}

        await repo.update_user_context(
            user=user, ctx_to_update={"first_key": "new_val"}, session=session
        )
        users_from_db = await session.execute(
            select(users).where(users.c.outer_id == user.outer_id)
        )
        user_from_db = users_from_db.first()
        result = await session.execute(
            select(user_contexts).where(user_contexts.c.user == user_from_db.id)
        )
        result = result.first()
        exists_context = result.ctx
        assert exists_context == {"first_key": "new_val", "second_key": "second_val"}


@pytest.mark.asyncio
async def test_get_user_ctx(alchemy_repo: tp.Awaitable[SQLAlchemyRepo]) -> None:
    repo = await alchemy_repo
    async_session = repo.session()
    async with async_session() as session:
        user = await repo.get_or_create_user(outer_id="1", session=session)

        old_ctx = await repo.get_user_context(user, session=session)
        assert old_ctx == {}

        await repo.update_user_context(
            user=user, ctx_to_update={"first_key": "first_val"}, session=session
        )
        new_ctx = await repo.get_user_context(user, session=session)
        assert new_ctx == {"first_key": "first_val"}


@pytest.mark.asyncio
async def test_get_user_history(alchemy_repo: tp.Awaitable[SQLAlchemyRepo]) -> None:
    repo = await alchemy_repo
    async_session = repo.session()
    async with async_session() as session:
        user = await repo.get_or_create_user(outer_id="1", session=session)

        history = await repo.get_user_history(user=user, session=session)
        assert history == []

        users_from_db = await session.execute(
            select(users).where(users.c.outer_id == user.outer_id)
        )
        user_from_db = users_from_db.first()
        await session.execute(
            out_messages.insert(),
            [
                dict(user=user_from_db.id, node_id="id_1", message_id="1010234"),
                dict(user=user_from_db.id, node_id="id_2", message_id="1010567"),
            ],
        )

        history = await repo.get_user_history(user=user, session=session)
        assert history == [{"id_1": "1010234"}, {"id_2": "1010567"}]


@pytest.mark.asyncio
async def test_update_user_history(alchemy_repo: tp.Awaitable[SQLAlchemyRepo]) -> None:
    repo = await alchemy_repo
    async_session = repo.session()
    async with async_session() as session:
        user = await repo.get_or_create_user(outer_id="1", session=session)

        history = await repo.get_user_history(user=user, session=session)
        assert history == []

        await repo.add_to_user_history(user=user, ids_pair={"id_1": "1010234"}, session=session)
        history = await repo.get_user_history(user=user, session=session)
        assert history == [{"id_1": "1010234"}]

        await repo.add_to_user_history(user=user, ids_pair={"id_2": "1010567"}, session=session)
        history = await repo.get_user_history(user=user, session=session)
        assert history == [{"id_1": "1010234"}, {"id_2": "1010567"}]


@pytest.mark.asyncio
async def test_create_project(alchemy_repo: tp.Awaitable[SQLAlchemyRepo]) -> None:
    repo = await alchemy_repo
    async_session = repo.session()
    async with async_session() as session:
        await repo.create_project("test project", session=session)

        projects_from_db = await session.execute(
            select(projects).where(projects.c.name == "test project")
        )
        project = projects_from_db.first()
        assert project.name == "test project"


@pytest.mark.asyncio
async def test_get_scenario(
    alchemy_repo: tp.Awaitable[SQLAlchemyRepo], mock_scenario: Scenario
) -> None:
    repo = await alchemy_repo
    async_session = repo.session()
    async with async_session() as session:
        await repo.create_project("test project", session=session)

        await session.execute(
            scenarios.insert(),
            [
                dict(
                    name=mock_scenario.name,
                    project="test project",
                    scenario_json=mock_scenario.to_dict(),
                )
            ],
        )

        parsed_scenario_from_db = await repo.get_scenario_by_name(
            name=mock_scenario.name, project_name="test project", session=session
        )
        assert parsed_scenario_from_db == mock_scenario


@pytest.mark.asyncio
async def test_add_scenario(
    alchemy_repo: tp.Awaitable[SQLAlchemyRepo], mock_scenario: Scenario
) -> None:
    repo = await alchemy_repo
    async_session = repo.session()
    async with async_session() as session:
        await repo.create_project("test project", session=session)
        await repo.add_scenario(
            scenario=mock_scenario, project_name="test project", session=session
        )
        parsed_scenario_from_db = await repo.get_scenario_by_name(
            name=mock_scenario.name, project_name="test project", session=session
        )
        assert parsed_scenario_from_db == mock_scenario


@pytest.mark.asyncio
async def test_add_scenario_texts(
    alchemy_repo: tp.Awaitable[SQLAlchemyRepo], mock_scenario: Scenario
) -> None:
    repo = await alchemy_repo
    async_session = repo.session()
    async with async_session() as session:
        await repo.create_project("test project", session=session)
        await repo.add_scenario(
            scenario=mock_scenario, project_name="test project", session=session
        )

        scenarios_from_db = await session.execute(
            select(scenarios).where(
                scenarios.c.name == mock_scenario.name,
                scenarios.c.project == "test project",
            )
        )
        scenario_from_db = scenarios_from_db.first()

        await repo.add_scenario_texts(
            scenario_name=mock_scenario.name,
            project_name="test project",
            texts={"TEXT_mock_scenario": "test substitution", "another": "text"},
            session=session,
        )

        texts_from_db = await session.execute(
            select(scenario_texts).where(
                scenario_texts.c.scenario == scenario_from_db.id,
                scenario_texts.c.project == "test project",
            )
        )
        texts = texts_from_db.fetchall()
        prepared_texts = {x.template_name: x.template_value for x in texts}
        assert prepared_texts == {
            "TEXT_mock_scenario": "test substitution",
            "another": "text",
        }


@pytest.mark.asyncio
async def test_get_scenario_text(
    alchemy_repo: tp.Awaitable[SQLAlchemyRepo], mock_scenario: Scenario
) -> None:
    repo = await alchemy_repo
    async_session = repo.session()
    async with async_session() as session:
        await repo.create_project("test project", session=session)
        await repo.add_scenario(
            scenario=mock_scenario, project_name="test project", session=session
        )
        await repo.add_scenario_texts(
            scenario_name=mock_scenario.name,
            project_name="test project",
            texts={"TEXT_mock_scenario": "test substitution", "another": "text"},
            session=session,
        )

        first_text = await repo.get_scenario_text(
            scenario_name=mock_scenario.name,
            project_name="test project",
            template_name="TEXT_mock_scenario",
            session=session,
        )
        second_text = await repo.get_scenario_text(
            scenario_name=mock_scenario.name,
            project_name="test project",
            template_name="another",
            session=session,
        )
        assert first_text == "test substitution"
        assert second_text == "text"


@pytest.mark.asyncio
async def test_get_scenarios_metadata(
    alchemy_repo: tp.Awaitable[SQLAlchemyRepo],
    mock_scenario: Scenario,
    intent_scenario: Scenario,
    matchtext_scenario: Scenario,
) -> None:
    repo = await alchemy_repo
    async_session = repo.session()
    async with async_session() as session:
        await repo.create_project("test_project", session=session)
        await repo.create_project("test_project2", session=session)
        await repo.add_scenario(
            scenario=mock_scenario, project_name="test_project", session=session
        )
        await repo.add_scenario(
            scenario=intent_scenario, project_name="test_project", session=session
        )
        await repo.add_scenario(
            scenario=mock_scenario, project_name="test_project2", session=session
        )
        await repo.add_scenario(
            scenario=matchtext_scenario, project_name="test_project2", session=session
        )

        metadata = await repo.get_all_scenarios_metadata(session=session)
        assert metadata == [
            (
                "test_project",
                mock_scenario.name,
            ),
            (
                "test_project",
                intent_scenario.name,
            ),
            (
                "test_project2",
                mock_scenario.name,
            ),
            (
                "test_project2",
                matchtext_scenario.name,
            ),
        ]
