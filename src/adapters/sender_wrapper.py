import typing as tp
from abc import ABC
from abc import abstractmethod
from collections import defaultdict

from src.adapters.repository import AbstractRepo
from src.domain.model import Event
from src.domain.model import OutEvent
from src.service_layer.sender import Sender


class AbstractSenderWrapper(ABC):
    """Хранит в себе историю отправленных сообщений пользователю"""

    def __init__(self, sender: Sender, repo: AbstractRepo) -> None:
        self.sender = sender
        self.repo = repo

    @abstractmethod
    async def process_event(self, event: Event) -> None:
        """Подмешивает историю сообщений"""

    @abstractmethod
    async def handle_message(self, message: Event) -> tp.List[Event]:
        """Интерфейс для взаимодействия с шиной"""


class SenderWrapper(AbstractSenderWrapper):
    def __init__(
        self,
        sender: Sender,
        repo: AbstractRepo,
    ) -> None:
        super().__init__(sender=sender, repo=repo)

    async def process_event(self, event: Event) -> None:
        """Подмешивает историю для изменения сообщений"""
        if isinstance(event, OutEvent):
            history = await self.repo.get_user_history(event.user)
            user_ctx = await self.repo.get_user_context(event.user)
            outer_message_id = await self.sender.send(
                event=event, history=history, ctx=user_ctx
            )
            await self.repo.add_to_user_history(
                event.user, {event.linked_node_id: outer_message_id}
            )

    async def handle_message(self, message: Event) -> tp.List[Event]:
        """Интерфейс для взаимодействия с шиной"""
        await self.process_event(message)
        return []
