import typing as tp
from abc import ABC
from abc import abstractmethod

from src.adapters.repository import AbstractContextRepo
from src.adapters.repository import AbstractRepo
from src.domain.events import EventProcessor
from src.domain.model import Event
from src.domain.model import InEvent
from src.domain.model import NodeType
from src.domain.model import Scenario


class AbstractEPWrapper(ABC):
    """Хранит в себе контекст пользователей"""

    def __init__(
        self,
        event_processor: EventProcessor,
        repo: AbstractRepo,
        ctx_repo: AbstractContextRepo,
    ) -> None:
        self.event_processor = event_processor
        self.repo = repo
        self.ctx_repo = ctx_repo

    @abstractmethod
    async def add_scenario(self, scenario_name: str, project_name: str) -> None:
        """Add scenario from repo into event processor"""

    @abstractmethod
    async def find(self, name: str, project_name: str) -> Scenario:
        """return self.scenarios[name]"""

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
        ctx_repo: AbstractContextRepo,
    ) -> None:
        super().__init__(event_processor=event_processor, repo=repo, ctx_repo=ctx_repo)

    async def add_scenario(self, scenario_name: str, project_name: str) -> None:
        """Add scenario from repo into event processor"""
        scenario = await self.repo.get_scenario_by_name(
            name=scenario_name, project_name=project_name
        )
        intents = [i.value for i in scenario.get_nodes_by_type(NodeType.inIntent)]
        phrases = [m.value for m in scenario.get_nodes_by_type(NodeType.matchText)]
        self.event_processor.add_scenario(
            scenario_name=scenario.name,
            project_name=project_name,
            intents=intents,
            phrases=phrases,
        )

    async def find(self, name: str, project_name: str) -> Scenario:
        """return self.scenarios[name]"""
        scenario = await self.repo.get_scenario_by_name(
            name=name, project_name=project_name
        )
        return scenario

    async def process_event(self, event: Event) -> tp.List[Event]:
        """Подмешивает контекст для исполнения сценария в EventProcessor"""
        if isinstance(event, InEvent):
            ctx = await self.ctx_repo.get_user_context(event.user)
            out_events, new_ctx = await self.event_processor.process_event(
                event=event,
                ctx=ctx,
                scenario_getter=self.find,
            )
            await self.repo.update_user(event.user)
            await self.ctx_repo.update_user_context(event.user, new_ctx)
            if event.user.current_scenario_name is None:
                await self.ctx_repo.clear_user_context(event.user)
            for e in out_events:
                e.project_name = event.project_name
            return out_events  # type: ignore
        return []

    async def handle_message(self, message: Event) -> tp.List[Event]:
        """Интерфейс для взаимодействия с шиной"""
        if isinstance(message, InEvent) and message.to_process:
            return await self.process_event(message)
        return []
