import typing as tp

import pytest
from fastapi.testclient import TestClient

from src.adapters.ep_wrapper import EPWrapper
from src.adapters.repository import InMemoryContextRepo
from src.adapters.repository import InMemoryRepo
from src.adapters.web_adapter import WebAdapter
from src.domain.events import EventProcessor
from src.domain.model import InEvent
from src.domain.model import MatchText
from src.domain.model import NodeType
from src.domain.model import OutEvent
from src.domain.model import OutMessage
from src.domain.model import Scenario
from src.entrypoints.web import Web
from src.service_layer.message_bus import ConcreteMessageBus
from tests.conftest import FakeListener


async def fake_message_handler(message: tp.Dict[str, tp.Any]) -> tp.Dict[str, tp.Any]:
    return message


web = Web(host="test", port=0, message_handler=fake_message_handler)
client = TestClient(web.app)


def test_healthcheck() -> None:
    response = client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_message_text(mock_scenario: Scenario) -> None:
    repo = InMemoryRepo()
    await repo.create_project("test_project")
    await repo.add_scenario(scenario=mock_scenario, project_name="test_project")
    await repo.add_scenario_texts(
        scenario_name=mock_scenario.name,
        project_name="test_project",
        texts={"TEXT_mock_scenario": "Подключаем оператора"},
    )

    ctx_repo = InMemoryContextRepo()

    ep = EventProcessor()
    wrapped_ep = EPWrapper(event_processor=ep, repo=repo, ctx_repo=ctx_repo)
    await wrapped_ep.add_scenario(
        scenario_name=mock_scenario.name, project_name="test_project"
    )

    listener = FakeListener()

    bus = ConcreteMessageBus()
    bus.register(wrapped_ep)
    bus.register(listener)

    web_adapter = WebAdapter(
        repo=repo, bus=bus, ep_wrapped=wrapped_ep, ctx_repo=ctx_repo
    )
    _web = Web(host="localhost", port=8080, message_handler=web_adapter.message_handler)
    web_client = TestClient(_web.app)

    data_message = {
        "user_id": "test1",
        "text": "60",
        "project_name": "test_project",
        "security": {
            "headers": [
                ["Cookie", "JSESSIONID=8558c932-6777-46b5-9504-97a711cc9203"],
                [
                    "User-Agent",
                    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
                ],
            ]
        },
        "integration_url": "https://test-delo.ru",
    }
    response = web_client.post("/message_text", json=data_message)
    assert response.status_code == 200
    assert response.json() == {
        "user_id": "test1",
        "events": [
            {
                "type": "text",
                "project_name": "test_project",
                "intent_name": "default",
                "text": "Подключаем оператора",
            }
        ],
    }


@pytest.mark.asyncio
async def test_web_adapter_integration(mock_scenario: Scenario) -> None:
    in_node = MatchText(
        element_id="id_1", value="Hi!", next_ids=["id_2"], node_type=NodeType.matchText
    )
    out_node = OutMessage(
        element_id="id_2", value="TEXT1", next_ids=[], node_type=NodeType.outMessage
    )
    test_scenario = Scenario("test", "id_1", {"id_1": in_node, "id_2": out_node})

    repo = InMemoryRepo()
    await repo.create_project("test_project")
    await repo.add_scenario(scenario=mock_scenario, project_name="test_project")
    await repo.add_scenario(scenario=test_scenario, project_name="test_project")

    ctx_repo = InMemoryContextRepo()

    ep = EventProcessor()
    wrapped_ep = EPWrapper(event_processor=ep, repo=repo, ctx_repo=ctx_repo)
    await wrapped_ep.add_scenario(
        scenario_name=test_scenario.name, project_name="test_project"
    )
    await wrapped_ep.add_scenario(
        scenario_name=mock_scenario.name, project_name="test_project"
    )

    listener = FakeListener()

    bus = ConcreteMessageBus()
    bus.register(wrapped_ep)
    bus.register(listener)

    web_adapter = WebAdapter(
        repo=repo, bus=bus, ep_wrapped=wrapped_ep, ctx_repo=ctx_repo
    )
    _web = Web(host="localhost", port=8080, message_handler=web_adapter.message_handler)
    web_client = TestClient(_web.app)

    data_message = {
        "user_id": "test123",
        "text": "Hi!",
        "project_name": "test_project",
        "intent": "",
        "integration_url": "https://test-url.ru",
        "security": {
            "headers": [
                ["Cookie", "JSESSIONID=8558c932-6777-46b5-9504-97a711cc9203"],
                [
                    "User-Agent",
                    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
                ],
            ]
        },
    }
    response = web_client.post("/message_text", json=data_message)
    assert response.status_code == 200
    assert response.json() == {
        "events": [
            {
                "intent_name": "test",
                "project_name": "test_project",
                "text": "TEXT1",
                "type": "text",
            }
        ],
        "user_id": "test123",
    }

    assert len(listener.events) == 2
    assert isinstance(listener.events[0], InEvent)
    assert listener.events[0].text == data_message["text"]
    assert isinstance(listener.events[1], OutEvent)
    assert listener.events[1].text == out_node.value

    user = await repo.get_or_create_user(outer_id="test123")
    assert user.current_node_id is None
    assert user.current_scenario_name is None

    assert len(bus.queue) == 0
