import typing as tp
from collections import defaultdict

import pytest

from src.domain.events import EventProcessor
from src.domain.model import EditMessage
from src.domain.model import Event
from src.domain.model import InEvent
from src.domain.model import InMessage
from src.domain.model import NodeType
from src.domain.model import OutEvent
from src.domain.model import OutMessage
from src.domain.model import Scenario
from src.domain.model import SetVariable
from src.domain.model import User
from src.service_layer.context import InMemoryContext
from src.service_layer.history import InMemoryHistory
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
        self.stored_ctx = {}

    async def send(
        self, event: OutEvent, history: tp.List[tp.Dict[str, str]], ctx: tp.Dict[str, tp.Dict[str, str]],
    ) -> str | None:
        """Send to outer service"""
        self.out_messages.append(event)
        self.stored_ctx = ctx
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

    ctx: tp.Dict[str, tp.Dict[str, str]] = defaultdict(dict)

    ep = EventProcessor([test_scenario], test_scenario.name)
    wrapped_ep = InMemoryContext(event_processor=ep, users_ctx=ctx)

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

    ctx: tp.Dict[str, tp.Dict[str, str]] = defaultdict(dict)

    ep = EventProcessor([test_scenario], test_scenario.name)
    wrapped_ep = InMemoryContext(event_processor=ep, users_ctx=ctx)

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


@pytest.mark.asyncio
async def test_out_messages_saving() -> None:
    in_node = InMessage(
        element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage
    )
    out_node = OutMessage(
        element_id="id_2",
        value="TEXT1",
        next_ids=["id_3"],
        node_type=NodeType.outMessage,
    )
    edit_node = EditMessage(
        element_id="id_3",
        value="TEXT2",
        next_ids=["id_2", "id_4"],
        node_type=NodeType.editMessage,
    )
    out_node2 = OutMessage(
        element_id="id_4", value="TEXT3", next_ids=[], node_type=NodeType.outMessage
    )
    test_scenario = Scenario(
        "test",
        "id_1",
        {"id_1": in_node, "id_2": out_node, "id_3": edit_node, "id_4": out_node2},
    )

    ctx: tp.Dict[str, tp.Dict[str, str]] = defaultdict(dict)

    ep = EventProcessor([test_scenario], test_scenario.name)
    wrapped_ep = InMemoryContext(event_processor=ep, users_ctx=ctx)

    sender = FakeSender()
    wrapped_sender = InMemoryHistory(sender=sender, users_ctx=ctx)

    bus = ConcreteMessageBus()
    bus.register(wrapped_ep)
    bus.register(wrapped_sender)

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="Hi!")

    await bus.public_message(in_event)

    assert len(sender.out_messages) == 3
    assert len(wrapped_sender.users_history["1"]) == 3
    assert wrapped_sender.users_history["1"][0]["id_2"] == "outer_id_2"
    assert wrapped_sender.users_history["1"][1]["id_3"] == "outer_id_3"
    assert wrapped_sender.users_history["1"][2]["id_4"] == "outer_id_4"


@pytest.mark.asyncio
async def test_context_available_in_wrapped_sender() -> None:
    in_node = InMessage(
        element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage
    )
    out_node = OutMessage(
        element_id="id_2",
        value="TEXT1",
        next_ids=[],
        node_type=NodeType.outMessage,
    )
    test_scenario = Scenario(
        "test",
        "id_1",
        {"id_1": in_node, "id_2": out_node},
    )

    ctx: tp.Dict[str, tp.Dict[str, str]] = defaultdict(dict)
    ctx["1"] = {"test_key": "test_value"}

    ep = EventProcessor([test_scenario], test_scenario.name)
    wrapped_ep = InMemoryContext(event_processor=ep, users_ctx=ctx)

    sender = FakeSender()
    wrapped_sender = InMemoryHistory(sender=sender, users_ctx=ctx)

    bus = ConcreteMessageBus()
    bus.register(wrapped_ep)
    bus.register(wrapped_sender)

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="Hi!")

    await bus.public_message(in_event)

    assert len(sender.stored_ctx) == 1
    assert "1" in sender.stored_ctx
    assert len(sender.stored_ctx["1"]) == 1
    assert sender.stored_ctx["1"]["test_key"] == "test_value"
