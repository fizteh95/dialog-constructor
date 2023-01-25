import copy
import typing as tp
from abc import ABC
from abc import abstractmethod

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
    async def process_templating(self, event: OutEvent) -> OutEvent:
        """Подставляет значение текста по шаблону"""

    @abstractmethod
    async def process_event(self, event: Event) -> None:
        """Подмешивает историю сообщений и контекст"""

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

    @staticmethod
    def insert_text(template: str, ctx: tp.Dict[str, str]) -> str:
        new_text = copy.deepcopy(template)
        if "$" in template:
            splits = new_text.split("$")
            new_text = ""
            for s in splits:
                if s in ctx:
                    new_text += str(ctx[s])
                else:
                    new_text += s
        return new_text

    async def process_templating(self, event: OutEvent) -> OutEvent:
        template_name = event.text
        scenario_name = event.scenario_name
        template = await self.repo.get_scenario_text(
            scenario_name=scenario_name, template_name=template_name
        )
        ctx = await self.repo.get_user_context(event.user)
        new_text = self.insert_text(template, ctx)
        event.text = new_text
        if event.buttons is not None:
            for b in event.buttons:
                template_name = b.text
                template = await self.repo.get_scenario_text(
                    scenario_name=scenario_name, template_name=template_name
                )
                new_text = self.insert_text(template, ctx)
                b.text = new_text
        return event

    async def process_event(self, event: Event) -> None:
        """Подмешивает историю и контекст для изменения сообщений"""
        if isinstance(event, OutEvent):
            history = await self.repo.get_user_history(event.user)
            user_ctx = await self.repo.get_user_context(event.user)
            templated_event = await self.process_templating(event)
            outer_message_id = await self.sender.send(
                event=templated_event, history=history, ctx=user_ctx
            )
            await self.repo.add_to_user_history(
                event.user, {event.linked_node_id: outer_message_id}
            )

    async def handle_message(self, message: Event) -> tp.List[Event]:
        """Интерфейс для взаимодействия с шиной"""
        await self.process_event(message)
        return []
