import pytest
from fastapi.testclient import TestClient

from src.adapters.ep_wrapper import EPWrapper
from src.adapters.repository import InMemoryRepo
from src.bootstrap import bootstrap
from src.domain.events import EventProcessor
from src.entrypoints.web import Web
from src.service_layer.message_bus import ConcreteMessageBus

# web = Web(host="test", port=0, message_handler=fake_message_handler)
# client = TestClient(web.app)


@pytest.mark.asyncio
async def test_bootstrap() -> None:
    # init_app = await bootstrap(
    #     repo=InMemoryRepo,
    #     ep=EventProcessor,
    #     ep_wrapper=EPWrapper,
    #     bus=ConcreteMessageBus,
    #     web=Web,
    #     web_adapter=WebAdapter,
    #     poller=TgPoller,
    #     poller_adapter=PollerAdapter,
    #     sender=TgSender,
    #     sender_wrapper=SenderWrapper,
    # )
    # await init_app
    assert True
