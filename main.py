import asyncio

from aiogram import Bot

from src.adapters.ep_wrapper import EPWrapper
from src.adapters.poller_adapter import PollerAdapter
from src.adapters.repository import InMemoryRepo
from src.adapters.sender_wrapper import SenderWrapper
from src.domain.events import EventProcessor
from src.domain.model import Scenario
from src.domain.scenario_loader import XMLParser
from src.entrypoints.poller import TgPoller
from src.service_layer.message_bus import ConcreteMessageBus
from src.service_layer.sender import TgSender


async def main() -> None:
    xml_src_path = "./src/resources/weather-demo.xml"
    parser = XMLParser()
    root_id, nodes = parser.parse(src_path=xml_src_path)
    parsed_nodes = {x.element_id: x for x in nodes}
    scenario = Scenario(name="weather-demo", root_id=root_id, nodes=parsed_nodes)

    repo = InMemoryRepo()

    ep = EventProcessor([scenario], scenario.name)
    wrapped_ep = EPWrapper(event_processor=ep, repo=repo)

    bot = Bot(token="5023614422:AAEIwysH_RgMug_GpVV8b3ZpEw4kVnRL3IU")

    sender = TgSender(bot=bot)
    wrapped_sender = SenderWrapper(sender=sender, repo=repo)

    bus = ConcreteMessageBus()
    bus.register(wrapped_ep)
    bus.register(wrapped_sender)

    poller_adapter = PollerAdapter(bus=bus, repo=repo)
    poller = TgPoller(
        message_handler=poller_adapter.message_handler,
        user_finder=poller_adapter.user_finder,
        bot=bot,
    )

    await poller.poll()


if __name__ == "__main__":
    asyncio.run(main())
