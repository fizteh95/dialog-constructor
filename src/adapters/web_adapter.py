import json
import typing as tp
from abc import ABC
from abc import abstractmethod

import jinja2 as j2

from src.adapters.ep_wrapper import AbstractEPWrapper
from src.adapters.repository import AbstractContextRepo
from src.adapters.repository import AbstractRepo
from src.domain.model import InEvent
from src.domain.model import OutEvent
from src.service_layer.message_bus import MessageBus


class AbstractWebAdapter(ABC):
    def __init__(
        self,
        repo: AbstractRepo,
        ctx_repo: AbstractContextRepo,
        bus: MessageBus,
        ep_wrapped: AbstractEPWrapper,
    ) -> None:
        self.repo = repo
        self.ctx_repo = ctx_repo
        self.bus = bus
        self.ep = ep_wrapped

    @abstractmethod
    async def message_handler(
        self, unparsed_event: tp.Dict[str, tp.Any]
    ) -> tp.Dict[str, tp.Any]:
        """Process income message from poller"""


class WebAdapter(AbstractWebAdapter):
    def __init__(
        self,
        repo: AbstractRepo,
        ctx_repo: AbstractContextRepo,
        bus: MessageBus,
        ep_wrapped: AbstractEPWrapper,
    ) -> None:
        super().__init__(repo=repo, ctx_repo=ctx_repo, bus=bus, ep_wrapped=ep_wrapped)

    async def process_templating(self, event: OutEvent) -> OutEvent:
        template_name = event.text
        scenario_name = event.scenario_name
        if event.project_name is not None:
            template = await self.repo.get_scenario_text(
                scenario_name=scenario_name,
                template_name=template_name,
                project_name=event.project_name,
            )
        else:
            template = event.text
        ctx = await self.ctx_repo.get_user_context(event.user)
        jinja_template = j2.Template(template)
        event.text = jinja_template.render(ctx)
        if event.buttons is not None:
            for b in event.buttons:
                template_name = b.text
                if event.project_name is not None:
                    template = await self.repo.get_scenario_text(
                        scenario_name=scenario_name,
                        template_name=template_name,
                        project_name=event.project_name,
                    )
                else:
                    template = b.text
                jinja_template = j2.Template(template)
                b.text = jinja_template.render(ctx)

                template_name = b.text_to_bot
                if event.project_name is not None:
                    template = await self.repo.get_scenario_text(
                        scenario_name=scenario_name,
                        template_name=template_name,
                        project_name=event.project_name,
                    )
                else:
                    template = b.text_to_bot
                jinja_template = j2.Template(template)
                b.text_to_bot = jinja_template.render(ctx)

                template_name = b.text_to_chat
                if event.project_name is not None:
                    template = await self.repo.get_scenario_text(
                        scenario_name=scenario_name,
                        template_name=template_name,
                        project_name=event.project_name,
                    )
                else:
                    template = b.text_to_chat
                jinja_template = j2.Template(template)
                b.text_to_chat = jinja_template.render(ctx)
        return event

    @staticmethod
    def _get_headers(headers: tp.List[tp.List[str]]) -> tp.Dict[str, str]:
        return {header: value for header, value in headers}

    async def message_handler(
        self, unparsed_event: tp.Dict[str, tp.Any]
    ) -> tp.Dict[str, tp.Any]:
        """Process income message from poller"""
        """
        "project_name": "WEB_UL",
        "integration_url": "https://test-delo.ru",
        #####
        "user_id": "13517462",
        "text": "Мой тариф",
        "type": "text",
        "timestamp": "2019-09-02T17:12:40.916+05:00",
        "context": {
            "first_name": "Дианна",
            "middle_name": "Маулевейна"
        },
        "security": 
        {
            "headers": 
                        [
                            ["Cookie", "JSESSIONID=8558c932-6777-46b5-9504-97a711cc9203"], 
                            [   
                                "User-Agent", 
                                "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36"
                            ]
                        ]
        }
        """
        user_outer_id = unparsed_event["user_id"]
        text = unparsed_event["text"]
        intent = unparsed_event.get("intent")
        project_name = unparsed_event["project_name"]
        headers = self._get_headers(unparsed_event["security"]["headers"])
        integration_url = unparsed_event["integration_url"]
        user = await self.repo.get_or_create_user(outer_id=user_outer_id)
        await self.ctx_repo.update_user_context(
            user,
            {
                "__headers__": json.dumps(headers),
                "__integration_url__": integration_url,
            },
        )
        message = InEvent(
            user=user,
            text=text,
            intent=intent,
            to_process=False,
            project_name=project_name,
        )
        await self.bus.public_message(message=message)
        events: tp.List[OutEvent] = await self.ep.process_event(message)  # type: ignore
        new_events = []
        for e in events:
            templated_event = await self.process_templating(e)
            e.to_process = False
            await self.bus.public_message(message=e)
            new_events.append(templated_event)
        results = []
        for i in new_events:
            results.append(
                {
                    "type": "text",
                    "project_name": project_name,
                    "intent_name": [i.scenario_name],
                    "text": i.text,
                }
            )
            if i.buttons:
                for b in i.buttons:
                    results.append(
                        {
                            "project_name": project_name,
                            "intent_name": i.scenario_name,
                            "function": "button",
                            "params": {
                                "text_button": b.text,
                                "text_to_chat": b.text_to_chat,
                                "text_to_bot": b.text_to_bot,
                            },
                            "type": "function",
                        }
                    )
        transformed_events = {"user_id": user.outer_id, "events": results}
        return transformed_events
