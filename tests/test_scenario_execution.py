import typing as tp

import pytest

from src.domain.events import EventProcessor
from src.domain.model import DataExtract
from src.domain.model import InEvent
from src.domain.model import InMessage
from src.domain.model import LogicalUnit
from src.domain.model import NodeType
from src.domain.model import OutEvent
from src.domain.model import OutMessage
from src.domain.model import Scenario
from src.domain.model import SetVariable
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
        element_id="id_2",
        value="TEXT1",
        next_ids=[],
        node_type=NodeType.outMessage,
        buttons=buttons,
    )
    out_node2 = OutMessage(
        element_id="id_3",
        value="TEXT2",
        next_ids=[],
        node_type=NodeType.outMessage,
    )
    out_node3 = OutMessage(
        element_id="id_4",
        value="TEXT3",
        next_ids=[],
        node_type=NodeType.outMessage,
    )
    test_scenario = Scenario(
        "test",
        "id_1",
        {"id_1": in_node, "id_2": out_node, "id_3": out_node2, "id_4": out_node3},
    )
    ep = EventProcessor([test_scenario], test_scenario.name)
    user = User(outer_id="1")

    in_event = InEvent(user=user, text="Hi!")
    ctx: tp.Dict[str, str] = {}
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == "TEXT1"
    assert out_events[0].buttons is not None
    assert len(out_events[0].buttons) == 2
    assert out_events[0].buttons[0].text == "TEXT1_1"
    assert out_events[0].buttons[0].callback_data == "id_3"
    assert out_events[0].buttons[1].text == "TEXT1_2"
    assert out_events[0].buttons[1].callback_data == "id_4"
    assert user.current_node_id == "id_2"
    assert user.current_scenario_name == "test"

    in_event2 = InEvent(user=user, button_pushed_next="id_3")
    out_events, new_ctx = await ep.process_event(in_event2, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == "TEXT2"
    assert out_events[0].buttons is None
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_double_click() -> None:
    in_node = InMessage(
        element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage
    )
    buttons = [("TEXT1_1", "id_3")]
    out_node = OutMessage(
        element_id="id_2",
        value="TEXT1",
        next_ids=[],
        node_type=NodeType.outMessage,
        buttons=buttons,
    )
    buttons2 = [("TEXT2_1", "id_4")]
    out_node2 = OutMessage(
        element_id="id_3",
        value="TEXT2",
        next_ids=[],
        node_type=NodeType.outMessage,
        buttons=buttons2,
    )
    out_node3 = OutMessage(
        element_id="id_4",
        value="TEXT3",
        next_ids=[],
        node_type=NodeType.outMessage,
    )
    test_scenario = Scenario(
        "test",
        "id_1",
        {"id_1": in_node, "id_2": out_node, "id_3": out_node2, "id_4": out_node3},
    )
    ep = EventProcessor([test_scenario], test_scenario.name)
    user = User(outer_id="1")

    in_event = InEvent(user=user, text="Hi!")
    ctx: tp.Dict[str, str] = {}
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == "TEXT1"
    assert out_events[0].buttons is not None
    assert len(out_events[0].buttons) == 1
    assert out_events[0].buttons[0].text == "TEXT1_1"
    assert out_events[0].buttons[0].callback_data == "id_3"
    assert user.current_node_id == "id_2"
    assert user.current_scenario_name == "test"

    in_event2 = InEvent(user=user, button_pushed_next="id_3")
    out_events, new_ctx = await ep.process_event(in_event2, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == "TEXT2"
    assert out_events[0].buttons is not None
    assert len(out_events[0].buttons) == 1
    assert out_events[0].buttons[0].text == "TEXT2_1"
    assert out_events[0].buttons[0].callback_data == "id_4"
    assert user.current_node_id == "id_3"
    assert user.current_scenario_name == "test"

    in_event3 = InEvent(user=user, button_pushed_next="id_4")
    out_events, new_ctx = await ep.process_event(in_event3, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == "TEXT3"
    assert out_events[0].buttons is None
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_re_data_extract() -> None:
    user = User(outer_id="1")
    ctx: tp.Dict[str, str] = {}
    extract_node = DataExtract(
        element_id="id_1",
        next_ids=[],
        node_type=NodeType.dataExtract,
        value="re(^[-]?((180$)|(((1[0-7]\d)|([1-9]\d?))$)))",
    )  # выделяет числа от -180 до +180
    events, new_ctx, text_to_pipeline = await extract_node.execute(user, ctx, "180")
    assert events == []
    assert new_ctx == {}
    assert text_to_pipeline == "180"
    events, new_ctx, text_to_pipeline = await extract_node.execute(user, ctx, "900")
    assert events == []
    assert new_ctx == {}
    assert text_to_pipeline == ""
    _, _, text_to_pipeline = await extract_node.execute(user, ctx, "+180")
    assert text_to_pipeline == ""
    _, _, text_to_pipeline = await extract_node.execute(user, ctx, "-101")
    assert text_to_pipeline == "-101"
    _, _, text_to_pipeline = await extract_node.execute(user, ctx, "-1010")
    assert text_to_pipeline == ""


@pytest.mark.asyncio
async def test_re_data_extract_pass_scenario() -> None:
    in_node = InMessage(
        element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage
    )
    extract_node = DataExtract(
        element_id="id_2",
        next_ids=["id_3"],
        node_type=NodeType.dataExtract,
        value="re(^[Пп]ривет[!)]?$)",
    )
    out_node = OutMessage(
        element_id="id_3", value="TEXT1", next_ids=[], node_type=NodeType.outMessage
    )
    test_scenario = Scenario(
        "test", "id_1", {"id_1": in_node, "id_2": extract_node, "id_3": out_node}
    )
    ep = EventProcessor([test_scenario], test_scenario.name)
    user = User(outer_id="1")
    in_event = InEvent(user=user, text="привет)")
    ctx: tp.Dict[str, str] = {}
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == "TEXT1"
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_re_data_extract_not_block_scenario() -> None:
    in_node = InMessage(
        element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage
    )
    extract_node = DataExtract(
        element_id="id_2",
        next_ids=["id_3"],
        node_type=NodeType.dataExtract,
        value="re(^[Пп]ривет[!)]?$)",
    )
    out_node = OutMessage(
        element_id="id_3", value="TEXT1", next_ids=[], node_type=NodeType.outMessage
    )
    test_scenario = Scenario(
        "test", "id_1", {"id_1": in_node, "id_2": extract_node, "id_3": out_node}
    )
    ep = EventProcessor([test_scenario], test_scenario.name)
    user = User(outer_id="1")
    in_event = InEvent(user=user, text="купи слона")
    ctx: tp.Dict[str, str] = {}
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == "TEXT1"
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_logical_unit_not() -> None:
    in_node = InMessage(
        element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage
    )
    extract_node = DataExtract(
        element_id="id_2",
        next_ids=["id_3"],
        node_type=NodeType.dataExtract,
        value="re(^[Пп]ривет[!)]?$)",
    )
    logical_not = LogicalUnit(
        element_id="id_3",
        next_ids=["id_4"],
        node_type=NodeType.logicalUnit,
        value="NOT",
    )
    out_node = OutMessage(
        element_id="id_4", value="TEXT1", next_ids=[], node_type=NodeType.outMessage
    )
    test_scenario = Scenario(
        "test",
        "id_1",
        {"id_1": in_node, "id_2": extract_node, "id_3": logical_not, "id_4": out_node},
    )
    ep = EventProcessor([test_scenario], test_scenario.name)
    user = User(outer_id="1")
    in_event = InEvent(user=user, text="купи слона!)")
    ctx: tp.Dict[str, str] = {}
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == "TEXT1"
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_re_data_extract_choose_only_way_bypass_not() -> None:
    in_node = InMessage(
        element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage
    )
    extract_node = DataExtract(
        element_id="id_2",
        next_ids=["id_3"],
        node_type=NodeType.dataExtract,
        value="re(^[Дд]а$)",
    )
    logical_not = LogicalUnit(
        element_id="id_3",
        next_ids=["id_4", "id_5"],
        node_type=NodeType.logicalUnit,
        value="NOT",
    )
    out_node = OutMessage(
        element_id="id_4", value="TEXT1", next_ids=[], node_type=NodeType.outMessage
    )
    out_node2 = OutMessage(
        element_id="id_5", value="TEXT2", next_ids=[], node_type=NodeType.outMessage
    )
    test_scenario = Scenario(
        "test",
        "id_1",
        {
            "id_1": in_node,
            "id_2": extract_node,
            "id_3": logical_not,
            "id_4": out_node,
            "id_5": out_node2,
        },
    )
    ep = EventProcessor([test_scenario], test_scenario.name)
    user = User(outer_id="1")
    in_event = InEvent(user=user, text="купи слона!)")
    ctx: tp.Dict[str, str] = {}
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == "TEXT1"
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_re_data_extract_choose_only_way_when_passed() -> None:
    in_node = InMessage(
        element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage
    )
    extract_node = DataExtract(
        element_id="id_2",
        next_ids=["id_3"],
        node_type=NodeType.dataExtract,
        value="re(^[Дд]а$)",
    )
    logical_not = LogicalUnit(
        element_id="id_3",
        next_ids=["id_4", "id_5"],
        node_type=NodeType.logicalUnit,
        value="NOT",
    )
    out_node = OutMessage(
        element_id="id_4", value="TEXT1", next_ids=[], node_type=NodeType.outMessage
    )
    out_node2 = OutMessage(
        element_id="id_5", value="TEXT2", next_ids=[], node_type=NodeType.outMessage
    )
    test_scenario = Scenario(
        "test",
        "id_1",
        {
            "id_1": in_node,
            "id_2": extract_node,
            "id_3": logical_not,
            "id_4": out_node,
            "id_5": out_node2,
        },
    )
    ep = EventProcessor([test_scenario], test_scenario.name)
    user = User(outer_id="1")
    in_event = InEvent(user=user, text="да")
    ctx: tp.Dict[str, str] = {}
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == "TEXT2"
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_cycle_until_done() -> None:
    in_node = InMessage(
        element_id="id_1", value="", next_ids=["id_2"], node_type=NodeType.inMessage
    )
    extract_node = DataExtract(
        element_id="id_2",
        next_ids=["id_3"],
        node_type=NodeType.dataExtract,
        value="re(^[Дд]а$)",
    )
    logical_not = LogicalUnit(
        element_id="id_3",
        next_ids=["id_4", "id_5"],
        node_type=NodeType.logicalUnit,
        value="NOT",
    )
    out_node = OutMessage(
        element_id="id_4",
        value="TEXT1",
        next_ids=["id_1"],
        node_type=NodeType.outMessage,
    )
    out_node2 = OutMessage(
        element_id="id_5",
        value="TEXT2",
        next_ids=[],
        node_type=NodeType.outMessage,
    )
    test_scenario = Scenario(
        "test",
        "id_1",
        {
            "id_1": in_node,
            "id_2": extract_node,
            "id_3": logical_not,
            "id_4": out_node,
            "id_5": out_node2,
        },
    )
    ep = EventProcessor([test_scenario], test_scenario.name)
    user = User(outer_id="1")
    in_event = InEvent(user=user, text="не хочу заканчивать сценарий")
    ctx: tp.Dict[str, str] = {}
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == "TEXT1"
    assert user.current_node_id == "id_1"
    assert user.current_scenario_name == "test"

    in_event = InEvent(user=user, text="все равно не хочу")
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == "TEXT1"
    assert user.current_node_id == "id_1"
    assert user.current_scenario_name == "test"

    in_event = InEvent(user=user, text="да")
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == "TEXT2"
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_set_variable() -> None:
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
    user = User(outer_id="1")
    in_event = InEvent(user=user, text="Hi!")
    ctx: tp.Dict[str, str] = {"old_var": "some_text"}
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(new_ctx) == 2
    assert new_ctx["old_var"] == "some_text"
    assert new_ctx["test_var1"] == "Hi!"
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == "TEXT1"
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_set_variable_rewrite_old_value() -> None:
    ...
