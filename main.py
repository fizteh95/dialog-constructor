import asyncio

from src.adapters.ep_wrapper import EPWrapper
from src.adapters.poller_adapter import PollerAdapter
from src.adapters.repository import InMemoryRepo
from src.adapters.sender_wrapper import SenderWrapper
from src.adapters.web_adapter import WebAdapter
from src.bootstrap import bootstrap
from src.domain.events import EventProcessor
from src.entrypoints.poller import TgPoller
from src.entrypoints.web import Web
from src.service_layer.message_bus import ConcreteMessageBus
from src.service_layer.sender import TgSender


async def main() -> None:
    init_app = await bootstrap(
        repo=InMemoryRepo,
        ep=EventProcessor,
        ep_wrapper=EPWrapper,
        bus=ConcreteMessageBus,
        web=Web,
        web_adapter=WebAdapter,
        poller=TgPoller,
        poller_adapter=PollerAdapter,
        sender=TgSender,
        sender_wrapper=SenderWrapper,
    )
    await init_app


if __name__ == "__main__":
    asyncio.run(main())
