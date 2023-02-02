import asyncio
import typing as tp

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import orm
from sqlalchemy.future import select
from alembic import command
from alembic.config import Config
from src.adapters.repository import AbstractRepo
from src.domain.model import User, Scenario


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
    sa.Column("ctx", sa.JSON, default={})  # TODO: переделать на отдельные колонки
)

out_messages = sa.Table(
    "out_messages",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("user", sa.ForeignKey("users.outer_id")),
    sa.Column("node_id", sa.String),
    sa.Column("message_id", sa.String)
)

projects = sa.Table(
    "projects",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("name", sa.String, unique=True)
)

scenarios = sa.Table(
    "scenarios",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("project", sa.ForeignKey("projects.name")),
    sa.Column("name", sa.String, unique=True),
    sa.Column("scenario_json", sa.JSON)
)

scenario_texts = sa.Table(
    "scenario_texts",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("scenario", sa.ForeignKey("scenarios.name")),
    sa.Column("template_name", sa.String),
    sa.Column("template_value", sa.String)
)


class SQLAlchemyRepo:  # (AbstractRepo)
    def __init__(self) -> None:
        # self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)
        self.engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost/postgres", echo=True)

    @staticmethod
    def run_upgrade(connection, cfg):
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, "head")

    async def run_async_upgrade(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(self.run_upgrade, Config("alembic.ini"))

    # @staticmethod
    # def start_alembic_migrations() -> None:
    #     try:
    #         alembic_cfg = Config("alembic.ini")
    #         command.upgrade(alembic_cfg, "head")
    #     except Exception as e:
    #         raise e

    async def _recreate_db(self) -> None:
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
    async def get_or_create_user(self, **kwargs: tp.Any) -> User:
        """Get by outer_id or create user"""
        ...

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


async def main_repo() -> None:
    r = SQLAlchemyRepo()
    await r.run_async_upgrade()
    # await r.test()


# asyncio.run(main())
