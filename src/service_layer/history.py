import typing as tp
from abc import ABC
from abc import abstractmethod
from collections import defaultdict

from src.domain.model import Event
from src.domain.model import OutEvent
from src.service_layer.sender import Sender


class HistoryWrapper(ABC):
    """Хранит в себе историю отправленных сообщений пользователю"""

    def __init__(
        self, sender: Sender, users_ctx: tp.Dict[str, tp.Dict[str, str]]
    ) -> None:
        self.sender = sender
        self.users_ctx = users_ctx

    @abstractmethod
    async def process_event(self, event: Event) -> None:
        """Подмешивает историю сообщений"""

    @abstractmethod
    async def handle_message(self, message: Event) -> tp.List[Event]:
        """Интерфейс для взаимодействия с шиной"""


class InMemoryHistory(HistoryWrapper):
    def __init__(
        self, sender: Sender, users_ctx: tp.Dict[str, tp.Dict[str, str]]
    ) -> None:
        super().__init__(sender=sender, users_ctx=users_ctx)
        self.users_history: tp.Dict[str, tp.List[tp.Dict[str, str]]] = defaultdict(
            list
        )  # {user_outer_id : [{node_id: outer_id}, {...}, ...]}

    async def process_event(self, event: Event) -> None:
        """Подмешивает историю для изменения сообщений"""
        if isinstance(event, OutEvent):
            history = self.users_history[event.user.outer_id]
            outer_message_id = await self.sender.send(
                event=event, history=history, ctx=self.users_ctx
            )
            self.users_history[event.user.outer_id].append(
                {event.linked_node_id: outer_message_id}
            )

    async def handle_message(self, message: Event) -> tp.List[Event]:
        """Интерфейс для взаимодействия с шиной"""
        await self.process_event(message)
        return []
