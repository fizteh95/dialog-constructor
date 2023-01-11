import typing as tp

import pytest

from src.domain.events import EventProcessor
from src.domain.model import InEvent
from src.domain.model import InMessage
from src.domain.model import NodeType
from src.domain.model import OutEvent
from src.domain.model import OutMessage
from src.domain.model import Scenario
from src.domain.model import User


@pytest.mark.asyncio
async def test_simple_in_out() -> None:
    in_node = InMessage(
        element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage
    )
    out_node = OutMessage(
        element_id="id_2", value="TEXT1", next_ids=[], node_type=NodeType.outMessage
    )
    test_scenario = Scenario("test", "id_1", {"id_1": in_node, "id_2": out_node})
    ep = EventProcessor([test_scenario], test_scenario.name)
    user = User(outer_id="1")
    in_event = InEvent(user=user, text="Hi!")
    ctx: tp.Dict[str, str] = {}
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == "TEXT1"
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_in_out_out() -> None:
    in_node = InMessage(
        element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage
    )
    out_node = OutMessage(
        element_id="id_2",
        value="TEXT1",
        next_ids=["id_3"],
        node_type=NodeType.outMessage,
    )
    out_node2 = OutMessage(
        element_id="id_3", value="TEXT2", next_ids=[], node_type=NodeType.outMessage
    )
    test_scenario = Scenario(
        "test", "id_1", {"id_1": in_node, "id_2": out_node, "id_3": out_node2}
    )
    ep = EventProcessor([test_scenario], test_scenario.name)
    user = User(outer_id="1")
    in_event = InEvent(user=user, text="Hi!")
    ctx: tp.Dict[str, str] = {}
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 2
    assert isinstance(out_events[0], OutEvent)
    assert isinstance(out_events[1], OutEvent)
    assert out_events[0].text == "TEXT1"
    assert out_events[1].text == "TEXT2"
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_in_out_in() -> None:
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
        element_id="id_3", value="", next_ids=[], node_type=NodeType.inMessage
    )
    test_scenario = Scenario(
        "test", "id_1", {"id_1": in_node, "id_2": out_node, "id_3": in_node2}
    )
    ep = EventProcessor([test_scenario], test_scenario.name)
    user = User(outer_id="1")
    in_event = InEvent(user=user, text="Hi!")
    ctx: tp.Dict[str, str] = {}
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == "TEXT1"
    assert user.current_node_id == "id_3"
    assert user.current_scenario_name == "test"


@pytest.mark.asyncio
async def test_in_out_buttons_out() -> None:
    in_node = InMessage(
        element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage
    )
    buttons = [("TEXT1_1", "id_98"), ("TEXT1_2", "id_99")]
    out_node = OutMessage(
        element_id="id_2",
        value="TEXT1",
        next_ids=["id_3"],
        node_type=NodeType.outMessage,
        buttons=buttons,
    )
    out_node2 = OutMessage(
        element_id="id_3", value="TEXT2", next_ids=[], node_type=NodeType.outMessage
    )
    test_scenario = Scenario(
        "test", "id_1", {"id_1": in_node, "id_2": out_node, "id_3": out_node2}
    )
    ep = EventProcessor([test_scenario], test_scenario.name)
    user = User(outer_id="1")
    in_event = InEvent(user=user, text="Hi!")
    ctx: tp.Dict[str, str] = {}
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 2
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].buttons is not None
    assert isinstance(out_events[1], OutEvent)
    assert out_events[0].text == "TEXT1"
    assert out_events[1].text == "TEXT2"
    assert user.current_node_id == "id_2"
    assert user.current_scenario_name == "test"


@pytest.mark.asyncio
async def test_in_out_buttons_out_in() -> None:
    in_node = InMessage(
        element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage
    )
    buttons = [("TEXT1_1", "id_98"), ("TEXT1_2", "id_99")]
    out_node = OutMessage(
        element_id="id_2",
        value="TEXT1",
        next_ids=["id_3"],
        node_type=NodeType.outMessage,
        buttons=buttons,
    )
    out_node2 = OutMessage(
        element_id="id_3",
        value="TEXT2",
        next_ids=["id_4"],
        node_type=NodeType.outMessage,
    )
    in_node2 = InMessage(
        element_id="id_4", value="", next_ids=[], node_type=NodeType.inMessage
    )
    test_scenario = Scenario(
        "test",
        "id_1",
        {"id_1": in_node, "id_2": out_node, "id_3": out_node2, "id_4": in_node2},
    )
    ep = EventProcessor([test_scenario], test_scenario.name)
    user = User(outer_id="1")
    in_event = InEvent(user=user, text="Hi!")
    ctx: tp.Dict[str, str] = {}
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 2
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].buttons is not None
    assert isinstance(out_events[1], OutEvent)
    assert out_events[0].text == "TEXT1"
    assert out_events[1].text == "TEXT2"
    assert user.current_node_id == "id_4"
    assert user.current_scenario_name == "test"


@pytest.mark.asyncio
async def test_in_out_x7_in() -> None:
    in_node = InMessage(
        element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage
    )
    out_node = OutMessage(
        element_id="id_2",
        value="TEXT1",
        next_ids=["id_3"],
        node_type=NodeType.outMessage,
    )
    out_node2 = OutMessage(
        element_id="id_3",
        value="TEXT2",
        next_ids=["id_4"],
        node_type=NodeType.outMessage,
    )
    out_node3 = OutMessage(
        element_id="id_4",
        value="TEXT3",
        next_ids=["id_5"],
        node_type=NodeType.outMessage,
    )
    out_node4 = OutMessage(
        element_id="id_5",
        value="TEXT4",
        next_ids=["id_6"],
        node_type=NodeType.outMessage,
    )
    out_node5 = OutMessage(
        element_id="id_6",
        value="TEXT5",
        next_ids=["id_7"],
        node_type=NodeType.outMessage,
    )
    out_node6 = OutMessage(
        element_id="id_7",
        value="TEXT6",
        next_ids=["id_8"],
        node_type=NodeType.outMessage,
    )
    out_node7 = OutMessage(
        element_id="id_8",
        value="TEXT7",
        next_ids=["id_9"],
        node_type=NodeType.outMessage,
    )
    in_node2 = InMessage(
        element_id="id_9", value="", next_ids=[], node_type=NodeType.inMessage
    )
    test_scenario = Scenario(
        "test",
        "id_1",
        {
            "id_1": in_node,
            "id_2": out_node,
            "id_3": out_node2,
            "id_4": out_node3,
            "id_5": out_node4,
            "id_6": out_node5,
            "id_7": out_node6,
            "id_8": out_node7,
            "id_9": in_node2,
        },
    )
    ep = EventProcessor([test_scenario], test_scenario.name)
    user = User(outer_id="1")
    in_event = InEvent(user=user, text="Hi!")
    ctx: tp.Dict[str, str] = {}
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 7
    assert isinstance(out_events[0], OutEvent)
    assert isinstance(out_events[1], OutEvent)
    assert isinstance(out_events[2], OutEvent)
    assert isinstance(out_events[3], OutEvent)
    assert isinstance(out_events[4], OutEvent)
    assert isinstance(out_events[5], OutEvent)
    assert isinstance(out_events[6], OutEvent)
    assert out_events[0].text == "TEXT1"
    assert out_events[1].text == "TEXT2"
    assert out_events[2].text == "TEXT3"
    assert out_events[3].text == "TEXT4"
    assert out_events[4].text == "TEXT5"
    assert out_events[5].text == "TEXT6"
    assert out_events[6].text == "TEXT7"
    assert user.current_node_id == "id_9"
    assert user.current_scenario_name == "test"


@pytest.mark.asyncio
async def test_in_out_buttons_in_button_out() -> None:
    in_node = InMessage(
        element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage
    )
    buttons = [("TEXT1_1", "id_3"), ("TEXT1_2", "id_4")]
    out_node = OutMessage(
        element_id="id_2", value="TEXT1", next_ids=[], node_type=NodeType.outMessage, buttons=buttons,
    )
    out_node2 = OutMessage(
        element_id="id_3", value="TEXT2", next_ids=[], node_type=NodeType.outMessage,
    )
    out_node3 = OutMessage(
        element_id="id_4", value="TEXT3", next_ids=[], node_type=NodeType.outMessage,
    )
    test_scenario = Scenario("test", "id_1", {"id_1": in_node, "id_2": out_node, "id_3": out_node2, "id_4": out_node3})
    ep = EventProcessor([test_scenario], test_scenario.name)
    user = User(outer_id="1")

    in_event = InEvent(user=user, text="Hi!")
    ctx: tp.Dict[str, str] = {}
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == "TEXT1"
    assert user.current_node_id == "id_2"
    assert user.current_scenario_name == "test"

    in_event2 = InEvent(user=user, button_pushed_next="id_3")
    out_events, new_ctx = await ep.process_event(in_event2, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == "TEXT2"
    assert user.current_node_id is None
    assert user.current_scenario_name is None
