import asyncio
import typing as tp

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import select

from alembic import command
from alembic.config import Config
from src.adapters.repository import AbstractRepo
from src.domain.model import Scenario
from src.domain.model import User

sa_metadata = sa.MetaData()

users = sa.Table(
    "users",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("outer_id", sa.String, unique=True),
    sa.Column("nickname", sa.String, nullable=True),
    sa.Column("name", sa.String, nullable=True),
    sa.Column("surname", sa.String, nullable=True),
    sa.Column("patronymic", sa.String, nullable=True),
    sa.Column("current_scenario_name", sa.String, nullable=True),
    sa.Column("current_node_id", sa.String, nullable=True),
)

user_contexts = sa.Table(
    "user_contexts",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("user", sa.ForeignKey("users.outer_id")),
    sa.Column("ctx", sa.JSON, default={}),  # TODO: переделать на отдельные колонки
)

out_messages = sa.Table(
    "out_messages",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("user", sa.ForeignKey("users.outer_id")),
    sa.Column("node_id", sa.String),
    sa.Column("message_id", sa.String),
)

projects = sa.Table(
    "projects",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("name", sa.String, unique=True),
)

scenarios = sa.Table(
    "scenarios",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("project", sa.ForeignKey("projects.name")),
    sa.Column("name", sa.String, unique=True),
    sa.Column("scenario_json", sa.JSON),
)

scenario_texts = sa.Table(
    "scenario_texts",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("scenario", sa.ForeignKey("scenarios.name")),
    sa.Column("template_name", sa.String),
    sa.Column("template_value", sa.String),
)


class SQLAlchemyRepo(AbstractRepo):
    def __init__(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")  # , echo=True
        # self.engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost/postgres", echo=True)

    async def prepare_db(self) -> None:
        await self.run_async_upgrade()

    @staticmethod
    def run_upgrade(connection, cfg) -> None:  # type: ignore
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, "head")

    async def run_async_upgrade(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(self.run_upgrade, Config("alembic.ini"))

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

    async def test(self) -> None:
        async_session = self.session()
        async with async_session() as session:
            stmt = sa.text("insert into projects (name) values ('tratata')")
            await session.execute(stmt)
            stmt = sa.text("select * from projects")
            result = await session.execute(stmt)
            res = result.fetchall()
            print(res)
            await session.commit()

    # User
    async def get_or_create_user(self, session: tp.Any = None, **kwargs: tp.Any) -> User:
        """Get by outer_id or create user"""
        if session is not None:
            if "outer_id" not in kwargs:
                raise Exception("User without outer_id is illegal")
            outer_id = kwargs["outer_id"]
            result = await session.execute(
                select(users).where(users.c.outer_id == outer_id)
            )
            user = result.first()

            if user is None:
                await session.execute(
                    users.insert(), [dict(
                        outer_id=outer_id,
                        nickname=kwargs.get("nickname"),
                        name=kwargs.get("name"),
                        surname=kwargs.get("surname"),
                        patronymic=kwargs.get("patronymic"),
                        current_scenario_name=kwargs.get("current_scenario_name"),
                        current_node_id=kwargs.get("current_node_id"),
                    )]
                )
                result = await session.execute(
                    select(users).where(users.c.outer_id == outer_id)
                )
                user = result.first()
                print(user)

            return User(
                outer_id=outer_id,
                nickname=user.nickname,
                name=user.name,
                surname=user.surname,
                patronymic=user.patronymic,
                current_scenario_name=user.current_scenario_name,
                current_node_id=user.current_node_id,
            )
        else:
            async_session = self.session()
            async with async_session() as session:
                if "outer_id" not in kwargs:
                    raise Exception("User without outer_id is illegal")
                outer_id = kwargs["outer_id"]
                result = await session.execute(
                    select(users).where(users.c.outer_id == outer_id)
                )
                user = result.first()

                if user is None:
                    await session.execute(
                        users.insert(), [dict(
                            outer_id=outer_id,
                            nickname=kwargs.get("nickname"),
                            name=kwargs.get("name"),
                            surname=kwargs.get("surname"),
                            patronymic=kwargs.get("patronymic"),
                            current_scenario_name=kwargs.get("current_scenario_name"),
                            current_node_id=kwargs.get("current_node_id"),
                        )]
                    )
                    result = await session.execute(
                        select(users).where(users.c.outer_id == outer_id)
                    )
                    user = result.first()
                    print(user)

                return User(
                    outer_id=outer_id,
                    nickname=user.nickname,
                    name=user.name,
                    surname=user.surname,
                    patronymic=user.patronymic,
                    current_scenario_name=user.current_scenario_name,
                    current_node_id=user.current_node_id,
                )

    async def update_user(self, user: User) -> User:
        """Update user fields"""
        ...

    # Context
    async def update_user_context(
        self, user: User, ctx_to_update: tp.Dict[str, str]
    ) -> None:
        """Update user context"""
        ...

    async def get_user_context(self, user: User) -> tp.Dict[str, str]:
        """Get user context"""
        ...

    async def get_user_history(self, user: User) -> tp.List[tp.Dict[str, str]]:
        """Get user history of out messages"""
        ...

    async def add_to_user_history(
        self, user: User, ids_pair: tp.Dict[str, str]
    ) -> None:
        """Get user history of out messages"""
        ...

    async def get_scenario_by_name(self, name: str, project_name: str) -> Scenario:
        """Get scenario by its name"""
        ...

    async def add_scenario(self, scenario: Scenario, project_name: str) -> None:
        """Add scenario in repository"""
        ...

    async def add_scenario_texts(
        self, scenario_name: str, project_name: str, texts: tp.Dict[str, str]
    ) -> None:
        """Add texts for templating scenario"""
        ...

    async def get_scenario_text(
        self, scenario_name: str, project_name: str, template_name: str
    ) -> str:
        """Return template value"""
        ...

    async def create_project(self, name: str) -> None:
        """Create project in db"""
        ...

    async def get_all_scenarios_metadata(self) -> tp.List[tp.Tuple[str, str]]:
        """Get all scenarios names and projects"""
        ...


async def main_repo():
    r = SQLAlchemyRepo()
    await r.run_async_upgrade()
    await r.test()