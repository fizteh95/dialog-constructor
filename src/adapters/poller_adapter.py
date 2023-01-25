import typing as tp
from abc import ABC
from abc import abstractmethod

from src.adapters.repository import AbstractRepo
from src.domain.model import InEvent
from src.domain.model import User
from src.service_layer.message_bus import MessageBus


class AbstractPollerAdapter(ABC):
    def __init__(self, bus: MessageBus, repo: AbstractRepo) -> None:
        self.bus = bus
        self.repo = repo

    @abstractmethod
    async def message_handler(self, event: InEvent) -> None:
        """Process income message from poller"""

    @abstractmethod
    async def user_finder(self, user_dict: tp.Dict[str, str]) -> User:
        """Get from outer_id or create from dict user"""


class PollerAdapter(AbstractPollerAdapter):
    def __init__(self, bus: MessageBus, repo: AbstractRepo) -> None:
        super().__init__(bus, repo)

    async def message_handler(self, event: InEvent) -> None:
        """Process income message from poller"""
        await self.bus.public_message(event)

    async def user_finder(self, user_dict: tp.Dict[str, str]) -> User:
        """Get from outer_id or create from dict user"""
        user = await self.repo.get_or_create_user(**user_dict)
        return user
