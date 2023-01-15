import copy
import typing as tp
from abc import ABC
from abc import abstractmethod

from src.dialogues.domain import Dialogue
from src.domain.model import User


class AbstractRepo(ABC):
    # TODO: split repos for every model
    @abstractmethod
    async def create_user(self, user: User) -> User:
        ...

    @abstractmethod
    async def get_user(self, user_id: str) -> User:
        ...

    @abstractmethod
    async def get_or_create_user(self, user: User) -> User:
        ...

    @abstractmethod
    async def set_user_current_scenario(
        self, user: User, scenario_name: str | None
    ) -> None:
        ...

    @abstractmethod
    async def set_user_current_node(self, user: User, node_id: str | None) -> None:
        ...

    @abstractmethod
    async def create_dialogue_scenario(self, dialogue: Dialogue) -> Dialogue:
        ...

    @abstractmethod
    async def get_dialogue(self, dialogue_name: str) -> Dialogue:
        ...


class InMemoryRepo(AbstractRepo):
    def __init__(self) -> None:
        self.users: tp.Dict[str, User] = {}
        self.dialogues: tp.Dict[str, Dialogue] = {}

    async def create_user(self, user: User) -> User:
        self.users[user.outer_id] = user
        return user

    async def get_user(self, user_id: str) -> User:
        return self.users[user_id]

    async def get_or_create_user(self, user: User) -> User:
        try:
            user_from_repo = await self.get_user(user.outer_id)
        except KeyError:
            user_from_repo = await self.create_user(user)
        return user_from_repo

    async def set_user_current_scenario(
        self, user: User, scenario_name: str | None
    ) -> None:
        user_copy = copy.deepcopy(await self.get_user(user.outer_id))
        user_copy.current_scenario_name = scenario_name
        self.users[user.outer_id] = user_copy

    async def set_user_current_node(self, user: User, node_id: str | None) -> None:
        user_copy = copy.deepcopy(await self.get_user(user.outer_id))
        user_copy.current_node_id = node_id
        self.users[user.outer_id] = user_copy

    async def create_dialogue_scenario(self, dialogue: Dialogue) -> Dialogue:
        self.dialogues[dialogue.name] = dialogue
        return dialogue

    async def get_dialogue(self, dialogue_name: str) -> Dialogue:
        return self.dialogues[dialogue_name]
