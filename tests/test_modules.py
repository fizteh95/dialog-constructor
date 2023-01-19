import typing as tp

import pytest

from src.adapters.ep_wrapper import EPWrapper
from src.adapters.poller_adapter import PollerAdapter
from src.adapters.repository import InMemoryRepo
from src.adapters.sender_wrapper import SenderWrapper
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
from src.entrypoints.poller import Poller
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

    async def send(
        self,
        event: OutEvent,
        history: tp.List[tp.Dict[str, str]],
        ctx: tp.Dict[str, str],
    ) -> str:
        """Send to outer service"""
        return f"outer_{event.linked_node_id}"


class FakePoller(Poller):
    def __init__(
        self,
        message_handler: tp.Callable[[InEvent], tp.Awaitable[None]],
        user_finder: tp.Callable[[tp.Dict[str, str]], tp.Awaitable[User]],
    ) -> None:
        super().__init__(message_handler=message_handler, user_finder=user_finder)

    async def poll(self) -> tp.AsyncIterator[InEvent]:  # type: ignore
        user = await self.user_finder(
            dict(
                outer_id="1",
            )
        )
        message = InEvent(user=user, text="Test text")
        await self.message_handler(message)


@pytest.mark.asyncio
async def test_message_bus() -> None:
    in_node = InMessage(
        element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage
    )
    out_node = OutMessage(
        element_id="id_2", value="TEXT1", next_ids=[], node_type=NodeType.outMessage
    )
    test_scenario = Scenario("test", "id_1", {"id_1": in_node, "id_2": out_node})

    repo = InMemoryRepo()

    ep = EventProcessor([test_scenario], test_scenario.name)
    wrapped_ep = EPWrapper(event_processor=ep, repo=repo)

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

    repo = InMemoryRepo()

    ep = EventProcessor([test_scenario], test_scenario.name)
    wrapped_ep = EPWrapper(event_processor=ep, repo=repo)

    listener = FakeListener()

    bus = ConcreteMessageBus()
    bus.register(wrapped_ep)
    bus.register(listener)

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="Hi!")

    await bus.public_message(in_event)

    user_ctx = await repo.get_user_context(user)
    assert len(user_ctx) == 1
    assert "test_var1" in user_ctx
    assert user_ctx["test_var1"] == "Hi!"


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

    repo = InMemoryRepo()

    ep = EventProcessor([test_scenario], test_scenario.name)
    wrapped_ep = EPWrapper(event_processor=ep, repo=repo)

    sender = FakeSender()
    wrapped_sender = SenderWrapper(sender=sender, repo=repo)

    bus = ConcreteMessageBus()
    bus.register(wrapped_ep)
    bus.register(wrapped_sender)

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="Hi!")

    await bus.public_message(in_event)

    history = await repo.get_user_history(user)
    assert len(history) == 3
    assert history[0]["id_2"] == "outer_id_2"
    assert history[1]["id_3"] == "outer_id_3"
    assert history[2]["id_4"] == "outer_id_4"


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

    repo = InMemoryRepo()
    user = User(outer_id="1")
    await repo.update_user_context(user, {"test_key": "test_value"})

    ep = EventProcessor([test_scenario], test_scenario.name)
    wrapped_ep = EPWrapper(event_processor=ep, repo=repo)

    sender = FakeSender()
    wrapped_sender = SenderWrapper(sender=sender, repo=repo)

    bus = ConcreteMessageBus()
    bus.register(wrapped_ep)
    bus.register(wrapped_sender)

    in_event = InEvent(user=user, text="Hi!")

    await bus.public_message(in_event)

    user_ctx = await repo.get_user_context(user)
    assert len(user_ctx) == 1
    assert user_ctx["test_key"] == "test_value"


@pytest.mark.asyncio
async def test_in_memory_repo_user() -> None:
    repo = InMemoryRepo()

    with pytest.raises(Exception) as e:
        await repo.get_or_create_user(name="Test user")
    assert str(e.value) == "User without outer_id is illegal"

    created_user = await repo.get_or_create_user(outer_id="1")
    assert isinstance(created_user, User)
    assert created_user.outer_id == "1"
    same_user = await repo.get_or_create_user(outer_id="1")
    assert created_user.outer_id == same_user.outer_id
    assert created_user.name == same_user.name
    assert created_user == same_user

    created_user2 = await repo.get_or_create_user(outer_id="2", name="Tester")
    assert isinstance(created_user2, User)
    assert created_user2.outer_id == "2"
    same_user2 = await repo.get_or_create_user(outer_id="2")
    assert same_user2.name == "Tester"

    created_user.name = "Test_name"
    await repo.update_user(created_user)
    user_from_repo = await repo.get_or_create_user(outer_id=created_user.outer_id)
    assert user_from_repo.name == "Test_name"


@pytest.mark.asyncio
async def test_in_memory_repo_context() -> None:
    repo = InMemoryRepo()

    user = User(outer_id="1")
    user_ctx = await repo.get_user_context(user)
    assert isinstance(user_ctx, tp.Dict)
    assert user_ctx == {}

    ctx_to_update = {"test_key": "test_value", "key_to_update": "value_to_update"}
    await repo.update_user_context(user, ctx_to_update)
    user_ctx = await repo.get_user_context(user)
    assert len(user_ctx) == 2
    assert "test_key" in user_ctx and "key_to_update" in user_ctx
    assert (
        user_ctx["test_key"] == "test_value"
        and user_ctx["key_to_update"] == "value_to_update"
    )

    new_ctx = {"key_to_update": "updated_value"}
    await repo.update_user_context(user, new_ctx)
    user_ctx = await repo.get_user_context(user)
    assert len(user_ctx) == 2
    assert "test_key" in user_ctx and "key_to_update" in user_ctx
    assert (
        user_ctx["test_key"] == "test_value"
        and user_ctx["key_to_update"] == "updated_value"
    )


@pytest.mark.asyncio
async def test_in_memory_repo_out_message_history() -> None:
    repo = InMemoryRepo()
    user = User(outer_id="1")

    old_history = await repo.get_user_history(user)
    assert isinstance(old_history, tp.List)
    assert len(old_history) == 0

    await repo.add_to_user_history(user, {"id_1": "100500"})
    history = await repo.get_user_history(user)
    assert len(history) == 1
    assert isinstance(history[0], tp.Dict)
    assert len(history[0]) == 1
    assert "id_1" in history[0]
    assert history[0]["id_1"] == "100500"

    await repo.add_to_user_history(user, {"id_2": "100501"})
    history = await repo.get_user_history(user)
    assert len(history) == 2
    assert isinstance(history[0], tp.Dict)
    assert len(history[0]) == 1
    assert "id_1" in history[0]
    assert history[0]["id_1"] == "100500"
    assert isinstance(history[1], tp.Dict)
    assert len(history[1]) == 1
    assert "id_2" in history[1]
    assert history[1]["id_2"] == "100501"


@pytest.mark.asyncio
async def test_poller_adapter() -> None:
    in_node = InMessage(
        element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage
    )
    out_node = OutMessage(
        element_id="id_2",
        value="TEXT1",
        next_ids=["id_3"],
        node_type=NodeType.outMessage,
    )
    in_node2 = InMessage(
        element_id="id_1", value="", next_ids=["id_4"], node_type=NodeType.inMessage
    )
    out_node2 = OutMessage(
        element_id="id_4", value="TEXT2", next_ids=[], node_type=NodeType.outMessage
    )
    test_scenario = Scenario(
        "test",
        "id_1",
        {"id_1": in_node, "id_2": out_node, "id_3": in_node2, "id_4": out_node2},
    )

    repo = InMemoryRepo()

    ep = EventProcessor([test_scenario], test_scenario.name)
    wrapped_ep = EPWrapper(event_processor=ep, repo=repo)

    sender = FakeListener()

    bus = ConcreteMessageBus()
    bus.register(wrapped_ep)
    bus.register(sender)

    poller_adapter = PollerAdapter(bus=bus, repo=repo)
    poller = FakePoller(
        message_handler=poller_adapter.message_handler,
        user_finder=poller_adapter.user_finder,
    )

    await poller.poll()
    assert len(sender.events) == 2
    assert isinstance(sender.events[0], InEvent)
    assert sender.events[0].text == "Test text"
    assert isinstance(sender.events[1], OutEvent)
    assert sender.events[1].text == "TEXT1"

    await poller.poll()
    assert len(sender.events) == 4
    assert isinstance(sender.events[2], InEvent)
    assert sender.events[2].text == "Test text"
    assert isinstance(sender.events[3], OutEvent)
    assert sender.events[3].text == "TEXT1"


@pytest.mark.asyncio
async def test_nodes_to_dict() -> None:
    test_node = OutMessage(
        element_id="id_1",
        value="TEXT1",
        next_ids=["id_2"],
        node_type=NodeType.outMessage,
    )
    res = test_node.to_dict()
    assert res

    recreated_node = OutMessage.from_dict(res)
    assert isinstance(recreated_node, OutMessage)
    assert recreated_node.element_id == test_node.element_id
    assert recreated_node.value == test_node.value
    assert recreated_node.next_ids == test_node.next_ids
    assert recreated_node.node_type == test_node.node_type
