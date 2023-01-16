import asyncio
import typing as tp
from collections import defaultdict

from aiogram import Bot

from src.dialogues.scenario_loader import XMLParser
from src.domain.events import EventProcessor
from src.domain.model import Scenario
from src.entrypoints.poller import TgPoller
from src.repository.repository import InMemoryRepo
from src.service_layer.context import InMemoryContext
from src.service_layer.history import InMemoryHistory
from src.service_layer.message_bus import ConcreteMessageBus
from src.service_layer.sender import TgSender


async def main() -> None:
    xml_src_path = "./src/resources/weather-demo.xml"
    parser = XMLParser()
    root_id, nodes = parser.parse(src_path=xml_src_path)
    parsed_nodes = {x.element_id: x for x in nodes}
    scenario = Scenario(name="weather-demo", root_id=root_id, nodes=parsed_nodes)

    ctx: tp.Dict[str, tp.Dict[str, str]] = defaultdict(dict)

    ep = EventProcessor([scenario], scenario.name)
    wrapped_ep = InMemoryContext(event_processor=ep, users_ctx=ctx)  # сюда репозиторий

    bot = Bot(token="5023614422:AAEIwysH_RgMug_GpVV8b3ZpEw4kVnRL3IU")

    sender = TgSender(bot=bot)
    wrapped_sender = InMemoryHistory(sender=sender, users_ctx=ctx)  # сюда репозиторий

    bus = ConcreteMessageBus()
    bus.register(wrapped_ep)
    bus.register(wrapped_sender)

    # TODO:

    repo = InMemoryRepo()

    poller = TgPoller(bus=bus, repo=repo, bot=bot)  # сюда репозиторий

    await poller.poll()


if __name__ == "__main__":
    asyncio.run(main())
