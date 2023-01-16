import copy
import typing as tp
from abc import ABC
from abc import abstractmethod
from collections import defaultdict

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
    async def update_user_context(self, user: User, ctx_to_update: tp.Dict[str, str]) -> None:
        """Update user context"""

    @abstractmethod
    async def get_user_context(self, user: User) -> tp.Dict[str, str]:
        """Get user context"""


class InMemoryRepo(AbstractRepo):
    def __init__(self) -> None:
        self.users: tp.Dict[str, User] = {}
        self.users_ctx: tp.Dict[str, tp.Dict[str, str]] = defaultdict(dict)
        self.out_messages: tp.Dict[str, tp.List[tp.Dict[str, str]]] = defaultdict(list)

    async def get_or_create_user(self, **kwargs: tp.Any) -> User:
        """Get by outer_id or create user"""
        if "outer_id" not in kwargs:
            raise Exception("User without outer_id is illegal")
        outer_id = kwargs["outer_id"]
        if outer_id in self.users:
            return self.users[outer_id]
        else:
            user = User(outer_id=outer_id,
                        nickname=kwargs.get("nickname"),
                        name=kwargs.get("name"),
                        surname=kwargs.get("surname"),
                        patronymic=kwargs.get("patronymic"),
                        current_scenario_name=kwargs.get("current_scenario_name"),
                        current_node_id=kwargs.get("current_node_id"),
                        )
            return user

    async def update_user(self, user: User) -> User:
        """Update user context"""
        self.users[user.outer_id] = user
        return self.users[user.outer_id]

    async def update_user_context(self, user: User, ctx_to_update: tp.Dict[str, str]) -> None:
        """Update user fields"""
        self.users_ctx[user.outer_id].update(ctx_to_update)

    async def get_user_context(self, user: User) -> tp.Dict[str, str]:
        """Get user context"""
        return self.users_ctx[user.outer_id]
