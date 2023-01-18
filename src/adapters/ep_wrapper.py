import typing as tp
from abc import ABC
from abc import abstractmethod

from src.adapters.repository import AbstractRepo
from src.domain.events import EventProcessor
from src.domain.model import Event
from src.domain.model import InEvent


class AbstractEPWrapper(ABC):
    """Хранит в себе контекст пользователей"""

    def __init__(
        self,
        event_processor: EventProcessor,
        repo: AbstractRepo,
    ) -> None:
        self.event_processor = event_processor
        self.repo = repo

    @abstractmethod
    async def process_event(self, event: Event) -> tp.List[Event]:
        """Подмешивает контекст для исполнения сценария"""

    @abstractmethod
    async def handle_message(self, message: Event) -> tp.List[Event]:
        """Интерфейс для взаимодействия с шиной"""


class EPWrapper(AbstractEPWrapper):
    def __init__(
        self,
        event_processor: EventProcessor,
        repo: AbstractRepo,
    ) -> None:
        super().__init__(event_processor=event_processor, repo=repo)

    async def process_event(self, event: Event) -> tp.List[Event]:
        """Подмешивает контекст для исполнения сценария в EventProcessor"""
        if isinstance(event, InEvent):
            ctx = await self.repo.get_user_context(event.user)
            out_events, new_ctx = await self.event_processor.process_event(
                event=event, ctx=ctx
            )
            print(new_ctx)
            await self.repo.update_user_context(event.user, new_ctx)
            await self.repo.update_user(event.user)
            return out_events
        return []

    async def handle_message(self, message: Event) -> tp.List[Event]:
        """Интерфейс для взаимодействия с шиной"""
        return await self.process_event(message)
