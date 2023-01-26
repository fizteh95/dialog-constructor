import copy
import typing as tp
from abc import ABC
from abc import abstractmethod

import jinja2 as j2

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

    async def process_templating(self, event: OutEvent) -> OutEvent:
        template_name = event.text
        scenario_name = event.scenario_name
        template = await self.repo.get_scenario_text(
            scenario_name=scenario_name, template_name=template_name
        )
        ctx = await self.repo.get_user_context(event.user)
        jinja_template = j2.Template(template)
        event.text = jinja_template.render(ctx)
        if event.buttons is not None:
            for b in event.buttons:
                template_name = b.text
                template = await self.repo.get_scenario_text(
                    scenario_name=scenario_name, template_name=template_name
                )
                jinja_template = j2.Template(template)
                b.text = jinja_template.render(ctx)
        return event

    async def process_event(self, event: Event) -> None:
        """Подмешивает историю и контекст для изменения сообщений"""
        if isinstance(event, OutEvent) and event.to_process:
            history = await self.repo.get_user_history(event.user)
            templated_event = await self.process_templating(event)
            outer_message_id = await self.sender.send(
                event=templated_event, history=history
            )
            await self.repo.add_to_user_history(
                event.user, {event.linked_node_id: outer_message_id}
            )

    async def handle_message(self, message: Event) -> tp.List[Event]:
        """Интерфейс для взаимодействия с шиной"""
        await self.process_event(message)
        return []
