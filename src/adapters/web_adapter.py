import typing as tp
from abc import ABC
from abc import abstractmethod

import jinja2 as j2

from src.adapters.ep_wrapper import AbstractEPWrapper
from src.adapters.repository import AbstractRepo
from src.domain.model import InEvent
from src.domain.model import OutEvent
from src.service_layer.message_bus import MessageBus


class AbstractWebAdapter(ABC):
    def __init__(
        self, repo: AbstractRepo, bus: MessageBus, ep_wrapped: AbstractEPWrapper
    ) -> None:
        self.repo = repo
        self.bus = bus
        self.ep = ep_wrapped

    @abstractmethod
    async def message_handler(
        self, unparsed_event: tp.Dict[str, tp.Any]
    ) -> tp.List[tp.Dict[str, tp.Any]]:
        """Process income message from poller"""


class WebAdapter(AbstractWebAdapter):
    def __init__(
        self, repo: AbstractRepo, bus: MessageBus, ep_wrapped: AbstractEPWrapper
    ) -> None:
        super().__init__(repo=repo, bus=bus, ep_wrapped=ep_wrapped)

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

    async def message_handler(
        self, unparsed_event: tp.Dict[str, tp.Any]
    ) -> tp.List[tp.Dict[str, tp.Any]]:
        """Process income message from poller"""
        user_outer_id = unparsed_event["user_id"]
        text = unparsed_event["text"]
        user = await self.repo.get_or_create_user(outer_id=user_outer_id)
        message = InEvent(user=user, text=text, to_process=False)
        await self.bus.public_message(message=message)
        events: tp.List[OutEvent] = await self.ep.process_event(message)  # type: ignore
        new_events = []
        for e in events:
            templated_event = await self.process_templating(e)
            e.to_process = False
            await self.bus.public_message(message=e)
            new_events.append(templated_event)
        transformed_events = [x.__dict__ for x in new_events]
        return transformed_events