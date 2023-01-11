import typing as tp

import pytest

from src.domain.events import EventProcessor
from src.domain.model import Scenario, User, InMessage, NodeType, InEvent, OutEvent, OutMessage, Button


@pytest.mark.asyncio
async def test_simple_in_out() -> None:
    in_node = InMessage(element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage)
    out_node = OutMessage(element_id="id_2", value="TEXT1", next_ids=[], node_type=NodeType.outMessage)
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
    in_node = InMessage(element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage)
    out_node = OutMessage(element_id="id_2", value="TEXT1", next_ids=["id_3"], node_type=NodeType.outMessage)
    out_node2 = OutMessage(element_id="id_3", value="TEXT2", next_ids=[], node_type=NodeType.outMessage)
    test_scenario = Scenario("test", "id_1", {"id_1": in_node, "id_2": out_node, "id_3": out_node2})
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
    in_node = InMessage(element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage)
    out_node = OutMessage(element_id="id_2", value="TEXT1", next_ids=["id_3"], node_type=NodeType.outMessage)
    in_node2 = InMessage(element_id="id_3", value="", next_ids=[], node_type=NodeType.inMessage)
    test_scenario = Scenario("test", "id_1", {"id_1": in_node, "id_2": out_node, "id_3": in_node2})
    ep = EventProcessor([test_scenario], test_scenario.name)
    user = User(outer_id="1")
    in_event = InEvent(user=user, text="Hi!")
    ctx: tp.Dict[str, str] = {}
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == "TEXT1"
    assert user.current_node_id == "id_3"
    # assert user.current_scenario_name == "test"


@pytest.mark.asyncio
async def test_in_out_buttons_out() -> None:
    in_node = InMessage(element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage)
    buttons = [("TEXT1_1", "id_98"), ("TEXT1_2", "id_99")]
    out_node = OutMessage(element_id="id_2", value="TEXT1", next_ids=["id_3"], node_type=NodeType.outMessage, buttons=buttons)
    out_node2 = OutMessage(element_id="id_3", value="TEXT2", next_ids=[], node_type=NodeType.outMessage)
    test_scenario = Scenario("test", "id_1", {"id_1": in_node, "id_2": out_node, "id_3": out_node2})
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
    # assert user.current_scenario_name == "test"
