import typing as tp

import pytest

from src.domain.events import EventProcessor
from src.domain.model import Event, SetVariable
from src.domain.model import InEvent
from src.domain.model import InMessage
from src.domain.model import NodeType
from src.domain.model import OutEvent
from src.domain.model import OutMessage
from src.domain.model import Scenario
from src.domain.model import User
from src.service_layer.context import InMemoryContext
from src.service_layer.message_bus import ConcreteMessageBus
from src.service_layer.sender import Sender


class FakeListener:
    def __init__(self) -> None:
        self.events: tp.List[Event] = []

    async def handle_message(self, message: Event) -> tp.List[Event]:
        """Интерфейс для взаимодействия с шиной"""
        self.events.append(message)
        return []


class FakeSender(Sender):
    def __init__(self, *args: tp.Any, **kwargs: tp.Any) -> None:
        super().__init__(*args, **kwargs)
        self.out_messages: tp.List[OutEvent] = []

    async def send(self, event: OutEvent, history: tp.List[tp.Dict[str, str]]) -> str | None:
        """Send to outer service"""
        self.out_messages.append(event)
        return f"outer_{event.linked_node_id}"


@pytest.mark.asyncio
async def test_message_bus() -> None:
    in_node = InMessage(
        element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage
    )
    out_node = OutMessage(
        element_id="id_2", value="TEXT1", next_ids=[], node_type=NodeType.outMessage
    )
    test_scenario = Scenario("test", "id_1", {"id_1": in_node, "id_2": out_node})

    ep = EventProcessor([test_scenario], test_scenario.name)
    wrapped_ep = InMemoryContext(event_processor=ep)

    listener = FakeListener()

    bus = ConcreteMessageBus()
    bus.register(wrapped_ep)
    bus.register(listener)

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="Hi!")

    await bus.public_message(in_event)

    assert len(listener.events) == 2
    assert isinstance(listener.events[0], InEvent)
    assert listener.events[0].text == "Hi!"
    assert isinstance(listener.events[1], OutEvent)
    assert listener.events[1].text == "TEXT1"

    assert user.current_node_id is None
    assert user.current_scenario_name is None

    assert len(bus.queue) == 0


@pytest.mark.asyncio
async def test_context_saving() -> None:
    in_node = InMessage(
        element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage
    )
    set_variable = SetVariable(
        element_id="id_2",
        value="user(test_var1)",
        next_ids=["id_3"],
        node_type=NodeType.setVariable,
    )
    out_node = OutMessage(
        element_id="id_3", value="TEXT1", next_ids=[], node_type=NodeType.outMessage
    )
    test_scenario = Scenario(
        "test", "id_1", {"id_1": in_node, "id_2": set_variable, "id_3": out_node}
    )

    ep = EventProcessor([test_scenario], test_scenario.name)
    wrapped_ep = InMemoryContext(event_processor=ep)

    listener = FakeListener()

    bus = ConcreteMessageBus()
    bus.register(wrapped_ep)
    bus.register(listener)

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="Hi!")

    await bus.public_message(in_event)

    assert len(wrapped_ep.users_ctx) == 1
    assert "1" in wrapped_ep.users_ctx
    assert "test_var1" in wrapped_ep.users_ctx["1"]
    assert wrapped_ep.users_ctx["1"]["test_var1"] == "Hi!"
