import functools
import typing as tp

import asyncpg
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import select

from alembic import command
from alembic import config
from src import settings
from src.adapters.alchemy.models import out_messages
from src.adapters.alchemy.models import projects
from src.adapters.alchemy.models import sa_metadata
from src.adapters.alchemy.models import scenario_texts
from src.adapters.alchemy.models import scenarios
from src.adapters.alchemy.models import user_contexts
from src.adapters.alchemy.models import users
from src.adapters.repository import AbstractRepo
from src.domain.model import Scenario
from src.domain.model import User


class SQLAlchemyRepo(AbstractRepo):
    def __init__(self) -> None:
        self.engine = create_async_engine(settings.ENGINE_STRING)  # , echo=True

    async def prepare_db(self) -> None:
        await self.run_async_upgrade()

    @staticmethod
    def run_upgrade(connection, cfg) -> None:  # type: ignore
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, "head")

    async def run_async_upgrade(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(self.run_upgrade, config.Config("alembic.ini"))

    async def _recreate_db(self) -> None:
        """
        ONLY FOR IN_MEMORY SQLITE DB!!!
        :return:
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(sa_metadata.drop_all)
        async with self.engine.begin() as conn:
            await conn.run_sync(sa_metadata.create_all)

    def session(self) -> tp.Any:
        async_session = orm.sessionmaker(  # type: ignore
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
        return async_session

    def use_session(func):
        @functools.wraps(func)
        async def wrapper_decorator(self, *args, **kwargs):
            if "session" in kwargs:
                value = await func(self, *args, **kwargs)
                await kwargs["session"].commit()
            else:
                async_session = self.session()
                async with async_session() as session:
                    value = await func(self, *args, session=session, **kwargs)
                    await session.commit()
            return value

        return wrapper_decorator

    # User
    @use_session
    async def get_or_create_user(
        self, session: tp.Any = None, **kwargs: tp.Any
    ) -> User:
        """Get by outer_id or create user"""
        if "outer_id" not in kwargs:
            raise Exception("User without outer_id is illegal")
        outer_id = str(kwargs["outer_id"])
        result = await session.execute(
            select(users).where(users.c.outer_id == outer_id)
        )
        user = result.first()

        if user is None:
            await session.execute(
                users.insert(),
                [
                    dict(
                        outer_id=outer_id,
                        nickname=kwargs.get("nickname"),
                        name=kwargs.get("name"),
                        surname=kwargs.get("surname"),
                        patronymic=kwargs.get("patronymic"),
                        current_scenario_name=kwargs.get("current_scenario_name"),
                        current_node_id=kwargs.get("current_node_id"),
                    )
                ],
            )
            result = await session.execute(
                select(users).where(users.c.outer_id == outer_id)
            )
            user = result.first()

        return User(
            outer_id=outer_id,
            nickname=user.nickname,
            name=user.name,
            surname=user.surname,
            patronymic=user.patronymic,
            current_scenario_name=user.current_scenario_name,
            current_node_id=user.current_node_id,
        )

    @use_session
    async def update_user(self, user: User, session: tp.Any = None) -> User:
        """Update user fields"""
        await session.execute(
            sa.update(users)
            .where(users.c.outer_id == user.outer_id)
            .values(
                nickname=user.nickname,
                name=user.name,
                surname=user.surname,
                patronymic=user.patronymic,
                current_scenario_name=user.current_scenario_name,
                current_node_id=user.current_node_id,
            )
        )
        await session.commit()
        result = await session.execute(
            select(users).where(users.c.outer_id == user.outer_id)
        )
        user_from_db = result.first()
        return User(
            outer_id=user_from_db.outer_id,
            nickname=user_from_db.nickname,
            name=user_from_db.name,
            surname=user_from_db.surname,
            patronymic=user_from_db.patronymic,
            current_scenario_name=user_from_db.current_scenario_name,
            current_node_id=user_from_db.current_node_id,
        )

    # Context
    @use_session
    async def update_user_context(
        self, user: User, ctx_to_update: tp.Dict[str, str], session: tp.Any = None
    ) -> None:
        """Update user context"""
        users_from_db = await session.execute(
            select(users).where(users.c.outer_id == user.outer_id)
        )
        user_from_db = users_from_db.first()

        result_ctx = await session.execute(
            select(user_contexts).where(user_contexts.c.user == user_from_db.id)
        )
        result_ctx = result_ctx.first()
        if result_ctx is None:
            await session.execute(
                user_contexts.insert(),
                [
                    dict(
                        user=user_from_db.id,
                        ctx={},
                    )
                ],
            )
        result_ctx = await session.execute(
            select(user_contexts).where(user_contexts.c.user == user_from_db.id)
        )
        result_ctx = result_ctx.first()

        exists_context = result_ctx.ctx
        new_context = exists_context | ctx_to_update
        await session.execute(
            sa.update(user_contexts)
            .where(user_contexts.c.user == user_from_db.id)
            .values(ctx=new_context)
        )
        await session.commit()

    @use_session
    async def clear_user_context(self, user: User, session: tp.Any = None) -> None:
        """Clear user context"""
        users_from_db = await session.execute(
            select(users).where(users.c.outer_id == user.outer_id)
        )
        user_from_db = users_from_db.first()

        result_ctx = await session.execute(
            select(user_contexts).where(user_contexts.c.user == user_from_db.id)
        )
        result_ctx = result_ctx.first()
        if result_ctx is None:
            await session.execute(
                user_contexts.insert(),
                [
                    dict(
                        user=user_from_db.id,
                        ctx={},
                    )
                ],
            )
        result_ctx = await session.execute(
            select(user_contexts).where(user_contexts.c.user == user_from_db.id)
        )
        result_ctx = result_ctx.first()

        exists_context = result_ctx.ctx

        new_context = {}
        for k in list(exists_context.keys()):
            if "_loopCount" in k:
                continue
            new_context[k] = exists_context[k]

        await session.execute(
            sa.update(user_contexts)
            .where(user_contexts.c.user == user_from_db.id)
            .values(ctx=new_context)
        )
        await session.commit()

    @use_session
    async def get_user_context(
        self, user: User, session: tp.Any = None
    ) -> tp.Dict[str, str]:
        """Get user context"""
        users_from_db = await session.execute(
            select(users).where(users.c.outer_id == user.outer_id)
        )
        user_from_db = users_from_db.first()

        result_ctx = await session.execute(
            select(user_contexts).where(user_contexts.c.user == user_from_db.id)
        )
        result_ctx = result_ctx.first()
        if result_ctx is None:
            return {}
        user_context: tp.Dict[str, str] = result_ctx.ctx
        return user_context

    @use_session
    async def get_user_history(
        self, user: User, session: tp.Any = None
    ) -> tp.List[tp.Dict[str, str]]:
        """Get user history of out messages"""
        users_from_db = await session.execute(
            select(users).where(users.c.outer_id == user.outer_id)
        )
        user_from_db = users_from_db.first()
        history_rows = await session.execute(
            select(out_messages).where(out_messages.c.user == user_from_db.id)
        )
        # TODO: optimize
        result = []
        for row in history_rows:
            result.append({row.node_id: row.message_id})
        return result

    @use_session
    async def add_to_user_history(
        self, user: User, ids_pair: tp.Dict[str, str], session: tp.Any = None
    ) -> None:
        """Get user history of out messages"""
        users_from_db = await session.execute(
            select(users).where(users.c.outer_id == user.outer_id)
        )
        user_from_db = users_from_db.first()

        if len(ids_pair) != 1:
            raise Exception("History dict must be with length = 1")
        await session.execute(
            out_messages.insert(),
            [
                dict(
                    user=user_from_db.id,
                    node_id=list(ids_pair.keys())[0],
                    message_id=list(ids_pair.values())[0],
                )
            ],
        )
        await session.commit()

    @use_session
    async def get_scenario_by_name(
        self, name: str, project_name: str, session: tp.Any = None
    ) -> Scenario:
        """Get scenario by its name"""
        projects_from_db = await session.execute(
            select(projects).where(projects.c.name == project_name)
        )
        project_from_db = projects_from_db.first()
        if project_from_db is None:
            raise Exception(f"Project with name {project_name} not found")

        scenarios_from_db = await session.execute(
            select(scenarios).where(
                scenarios.c.name == name, scenarios.c.project == project_from_db.name
            )
        )
        scenario_from_db = scenarios_from_db.first()
        if scenario_from_db is None:
            raise Exception(
                f"Scenario with name {name} from project {project_name} not found"
            )

        need_scenario: Scenario = Scenario.from_dict(scenario_from_db.scenario_json)
        return need_scenario

    @use_session
    async def add_scenario(
        self, scenario: Scenario, project_name: str, session: tp.Any = None
    ) -> None:
        """Add scenario in repository"""
        try:
            await self.get_scenario_by_name(
                name=scenario.name, project_name=project_name, session=session
            )
            await session.execute(
                scenarios.delete().where(
                    scenarios.c.name == scenario.name,
                    scenarios.c.project == project_name,
                )
            )
        except Exception as e:
            print(e)
        await session.execute(
            scenarios.insert(),
            [
                dict(
                    name=scenario.name,
                    project=project_name,
                    scenario_json=scenario.to_dict(),
                )
            ],
        )
        await session.commit()

    @use_session
    async def add_scenario_texts(
        self,
        scenario_name: str,
        project_name: str,
        texts: tp.Dict[str, str],
        session: tp.Any = None,
    ) -> None:
        """Add texts for templating scenario"""
        scenarios_from_db = await session.execute(
            select(scenarios).where(
                scenarios.c.name == scenario_name, scenarios.c.project == project_name
            )
        )
        scenario_from_db = scenarios_from_db.first()
        if scenario_from_db is None:
            raise Exception(
                f"Scenario with name {scenario_name} from project {project_name} not found"
            )

        await session.execute(
            scenario_texts.delete().where(
                scenario_texts.c.scenario == scenario_from_db.id,
                scenario_texts.c.project == project_name,
                scenario_texts.c.template_name.in_(list(texts.keys())),
            )
        )

        await session.execute(
            scenario_texts.insert(),
            [
                dict(
                    scenario=scenario_from_db.id,
                    project=project_name,
                    template_name=k,
                    template_value=v,
                )
                for k, v in texts.items()
            ],
        )

    @use_session
    async def get_scenario_text(
        self,
        scenario_name: str,
        project_name: str,
        template_name: str,
        session: tp.Any = None,
    ) -> str:
        """Return template value"""
        scenarios_from_db = await session.execute(
            select(scenarios).where(
                scenarios.c.name == scenario_name, scenarios.c.project == project_name
            )
        )
        scenario_from_db = scenarios_from_db.first()
        if scenario_from_db is None:
            raise Exception(
                f"Scenario with name {scenario_name} from project {project_name} not found"
            )

        text_from_db = await session.execute(
            select(scenario_texts).where(
                scenario_texts.c.scenario == scenario_from_db.id,
                scenario_texts.c.project == project_name,
                scenario_texts.c.template_name == template_name,
            )
        )
        text = text_from_db.first()
        if text is None:
            return template_name
        template_value: str = text.template_value
        return template_value

    @use_session
    async def create_project(self, name: str, session: tp.Any = None) -> None:
        """Create project in db"""
        try:
            await session.execute(
                projects.insert(),
                [dict(name=name)],
            )
        except Exception as e:  # если есть
            print(e)
            pass

    @use_session
    async def get_all_scenarios_metadata(
        self, session: tp.Any = None
    ) -> tp.List[tp.Tuple[str, str]]:
        """Get all scenarios names and projects"""
        scenarios_from_db = await session.execute(select(scenarios))
        result: tp.List[tp.Tuple[str, str]] = []
        for scenario in scenarios_from_db:
            result.append(
                (
                    scenario.project,
                    scenario.name,
                )
            )
        return result
