import typing as tp
from abc import ABC
from abc import abstractmethod
from collections import defaultdict

from src.domain.events import EventProcessor
from src.domain.model import Event
from src.domain.model import InEvent


class ContextWrapper(ABC):
    """Хранит в себе контекст пользователей"""

    def __init__(
        self,
        event_processor: EventProcessor,
        users_ctx: tp.Dict[str, tp.Dict[str, str]],
    ) -> None:
        self.event_processor = event_processor
        self.users_ctx = users_ctx  # user_outer_id : {var_KEY: var_VALUE}

    @abstractmethod
    async def process_event(self, event: Event) -> tp.List[Event]:
        """Подмешивает контекст для исполнения сценария"""

    @abstractmethod
    async def handle_message(self, message: Event) -> tp.List[Event]:
        """Интерфейс для взаимодействия с шиной"""


class InMemoryContext(ContextWrapper):
    def __init__(
        self,
        event_processor: EventProcessor,
        users_ctx: tp.Dict[str, tp.Dict[str, str]],
    ) -> None:
        super().__init__(event_processor=event_processor, users_ctx=users_ctx)

    async def process_event(self, event: Event) -> tp.List[Event]:
        """Подмешивает контекст для исполнения сценария в EventProcessor"""
        if isinstance(event, InEvent):
            ctx = self.users_ctx[event.user.outer_id]
            out_events, new_ctx = await self.event_processor.process_event(
                event=event, ctx=ctx
            )
            print(new_ctx)
            self.users_ctx[event.user.outer_id].update(new_ctx)
            return out_events
        return []

    async def handle_message(self, message: Event) -> tp.List[Event]:
        """Интерфейс для взаимодействия с шиной"""
        return await self.process_event(message)
