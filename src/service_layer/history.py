import typing as tp
from abc import ABC
from abc import abstractmethod
from collections import defaultdict

from src.domain.model import Event, OutEvent
from src.service_layer.sender import Sender


class HistoryWrapper(ABC):
    """Хранит в себе историю отправленных сообщений пользователю"""

    def __init__(self, sender: Sender) -> None:
        self.sender = sender

    @abstractmethod
    async def process_event(self, event: Event) -> None:
        """Подмешивает историю сообщений"""

    @abstractmethod
    async def handle_message(self, message: Event) -> tp.List[Event]:
        """Интерфейс для взаимодействия с шиной"""


class InMemoryHistory(HistoryWrapper):
    def __init__(self, sender: Sender) -> None:
        super().__init__(sender=sender)
        self.users_history: tp.Dict[str, tp.List[tp.Dict[str, str]]] = defaultdict(
            list
        )  # {user_outer_id : [{node_id: outer_id}, {...}, ...]}

    async def process_event(self, event: Event) -> None:
        """Подмешивает контекст для исполнения сценария"""
        if isinstance(event, OutEvent):
            history = self.users_history[event.user.outer_id]
            outer_message_id = await self.sender.send(event=event, history=history)
            self.users_history[event.user.outer_id].append({event.linked_node_id: outer_message_id})

    async def handle_message(self, message: Event) -> tp.List[Event]:
        """Интерфейс для взаимодействия с шиной"""
        await self.process_event(message)
        return []
