import typing as tp
from abc import ABC
from abc import abstractmethod
from collections import defaultdict

from src.domain.model import Scenario
from src.domain.model import User


class AbstractRepo(ABC):
    # TODO: split repo for every model

    # User
    @abstractmethod
    async def get_or_create_user(self, **kwargs: tp.Any) -> User:
        """Get by outer_id or create user"""

    @abstractmethod
    async def update_user(self, user: User) -> User:
        """Update user fields"""

    # Context
    @abstractmethod
    async def update_user_context(
        self, user: User, ctx_to_update: tp.Dict[str, str]
    ) -> None:
        """Update user context"""

    @abstractmethod
    async def get_user_context(self, user: User) -> tp.Dict[str, str]:
        """Get user context"""

    @abstractmethod
    async def get_user_history(self, user: User) -> tp.List[tp.Dict[str, str]]:
        """Get user history of out messages"""

    @abstractmethod
    async def add_to_user_history(
        self, user: User, ids_pair: tp.Dict[str, str]
    ) -> None:
        """Get user history of out messages"""

    @abstractmethod
    async def get_scenario_by_name(self, name: str) -> Scenario:
        """Get scenario by its name"""

    @abstractmethod
    async def add_scenario(self, scenario: Scenario) -> None:
        """Add scenario in repository"""

    @abstractmethod
    async def add_scenario_texts(
        self, scenario_name: str, texts: tp.Dict[str, str]
    ) -> None:
        """Add texts for templating scenario"""

    @abstractmethod
    async def get_scenario_text(self, scenario_name: str, template_name: str) -> str:
        """Return template value"""


class InMemoryRepo(AbstractRepo):
    def __init__(self) -> None:
        self.users: tp.Dict[str, User] = {}
        self.users_ctx: tp.Dict[str, tp.Dict[str, str]] = defaultdict(dict)
        self.out_messages: tp.Dict[str, tp.List[tp.Dict[str, str]]] = defaultdict(list)
        self.scenarios: tp.Dict[str, tp.Dict[str, tp.Any]] = {}
        self.scenario_texts: tp.Dict[str, tp.Dict[str, str]] = {}

    async def get_or_create_user(self, **kwargs: tp.Any) -> User:
        """Get by outer_id or create user"""
        if "outer_id" not in kwargs:
            raise Exception("User without outer_id is illegal")
        outer_id = kwargs["outer_id"]
        if outer_id in self.users:
            return self.users[outer_id]
        else:
            user = User(
                outer_id=outer_id,
                nickname=kwargs.get("nickname"),
                name=kwargs.get("name"),
                surname=kwargs.get("surname"),
                patronymic=kwargs.get("patronymic"),
                current_scenario_name=kwargs.get("current_scenario_name"),
                current_node_id=kwargs.get("current_node_id"),
            )
            self.users[outer_id] = user
            return user

    async def update_user(self, user: User) -> User:
        """Update user context"""
        self.users[user.outer_id] = user
        return self.users[user.outer_id]

    async def update_user_context(
        self, user: User, ctx_to_update: tp.Dict[str, str]
    ) -> None:
        """Update user fields"""
        self.users_ctx[user.outer_id].update(ctx_to_update)

    async def get_user_context(self, user: User) -> tp.Dict[str, str]:
        """Get user context"""
        return self.users_ctx[user.outer_id]

    async def get_user_history(self, user: User) -> tp.List[tp.Dict[str, str]]:
        """Get user history of out messages"""
        return self.out_messages[user.outer_id]

    async def add_to_user_history(
        self, user: User, ids_pair: tp.Dict[str, str]
    ) -> None:
        """Get user history of out messages"""
        self.out_messages[user.outer_id].append(ids_pair)

    async def get_scenario_by_name(self, name: str) -> Scenario:
        """Get scenario by its name"""
        return Scenario.from_dict(self.scenarios[name])

    async def add_scenario(self, scenario: Scenario) -> None:
        """Add scenario in repository"""
        self.scenarios[scenario.name] = scenario.to_dict()

    async def add_scenario_texts(
        self, scenario_name: str, texts: tp.Dict[str, str]
    ) -> None:
        """Add texts for templating scenario"""
        self.scenario_texts[scenario_name] = texts

    async def get_scenario_text(self, scenario_name: str, template_name: str) -> str:
        """Return template value"""
        try:
            texts = self.scenario_texts[scenario_name]
            return texts[template_name]
        except KeyError:
            print(f"Error, template {template_name} not found")
            return template_name
