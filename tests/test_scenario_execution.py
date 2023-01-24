import json
import typing as tp

import pytest

from src.domain.events import EventProcessor
from src.domain.model import Button
from src.domain.model import DataExtract
from src.domain.model import EditMessage
from src.domain.model import InEvent
from src.domain.model import InIntent
from src.domain.model import InMessage
from src.domain.model import LogicalUnit
from src.domain.model import MatchText
from src.domain.model import NodeType
from src.domain.model import OutEvent
from src.domain.model import OutMessage
from src.domain.model import RemoteRequest
from src.domain.model import Scenario
from src.domain.model import SetVariable
from src.domain.model import User


class FakeScenarioGetter:
    def __init__(self, scenarios: tp.Dict[str, Scenario]) -> None:
        self.scenarios = scenarios

    async def find(self, name: str) -> Scenario:
        return self.scenarios[name]


@pytest.mark.asyncio
async def test_start_matchtext_scenario(
    matchtext_scenario: Scenario, intent_scenario: Scenario, mock_scenario: Scenario
) -> None:
    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            intent_scenario.name: intent_scenario,
            matchtext_scenario.name: matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            intent_scenario.name: {"intents": ["test_intent"], "phrases": []},
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx)

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_start_matchtext_scenario_with_or(
    matchtext_scenario_with_or: Scenario,
    intent_scenario: Scenario,
    mock_scenario: Scenario,
) -> None:
    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            intent_scenario.name: intent_scenario,
            matchtext_scenario_with_or.name: matchtext_scenario_with_or,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario_with_or.name: {"intents": [], "phrases": ["not start"]},
            intent_scenario.name: {"intents": ["test_intent"], "phrases": []},
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="not start")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx)

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario_with_or.get_node_by_id("id_4").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_start_intent_scenario(
    matchtext_scenario: Scenario, intent_scenario: Scenario, mock_scenario: Scenario
) -> None:
    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            intent_scenario.name: intent_scenario,
            matchtext_scenario.name: matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            intent_scenario.name: {"intents": ["test_intent"], "phrases": []},
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    in_event = InEvent(
        user=user, intent="test_intent", text="phrase for triggered intent"
    )
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx)

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == intent_scenario.get_node_by_id("id_2").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_start_intent_scenario_with_or(
    matchtext_scenario: Scenario,
    intent_scenario_with_or: Scenario,
    mock_scenario: Scenario,
) -> None:
    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            intent_scenario_with_or.name: intent_scenario_with_or,
            matchtext_scenario.name: matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            intent_scenario_with_or.name: {"intents": ["test_intent2"], "phrases": []},
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    in_event = InEvent(
        user=user, intent="test_intent2", text="phrase for triggered intent"
    )
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx)

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == intent_scenario_with_or.get_node_by_id("id_4").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_start_default_scenario(
    matchtext_scenario: Scenario, intent_scenario: Scenario, mock_scenario: Scenario
) -> None:
    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            intent_scenario.name: intent_scenario,
            matchtext_scenario.name: matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            intent_scenario.name: {"intents": ["test_intent"], "phrases": []},
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    in_event = InEvent(user=user, intent="habahaba", text="habahaba")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx)

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == mock_scenario.get_node_by_id("id_2").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_start_scenario_with_several_intent_scenarios(
    matchtext_scenario: Scenario,
    another_matchtext_scenario: Scenario,
    intent_scenario: Scenario,
    another_intent_scenario: Scenario,
    mock_scenario: Scenario,
) -> None:
    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            intent_scenario.name: intent_scenario,
            matchtext_scenario.name: matchtext_scenario,
            another_intent_scenario.name: another_intent_scenario,
            another_matchtext_scenario.name: another_matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            intent_scenario.name: {"intents": ["test_intent"], "phrases": []},
            another_matchtext_scenario.name: {
                "intents": [],
                "phrases": ["another start"],
            },
            another_intent_scenario.name: {
                "intents": ["another_test_intent"],
                "phrases": [],
            },
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    in_event = InEvent(user=user, intent="another_test_intent", text="habahaba")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx)

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == another_intent_scenario.get_node_by_id("id_2").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_start_scenario_with_several_matchtext_scenarios(
    matchtext_scenario: Scenario,
    another_matchtext_scenario: Scenario,
    intent_scenario: Scenario,
    another_intent_scenario: Scenario,
    mock_scenario: Scenario,
) -> None:
    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            intent_scenario.name: intent_scenario,
            matchtext_scenario.name: matchtext_scenario,
            another_intent_scenario.name: another_intent_scenario,
            another_matchtext_scenario.name: another_matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            intent_scenario.name: {"intents": ["test_intent"], "phrases": []},
            another_matchtext_scenario.name: {
                "intents": [],
                "phrases": ["another start"],
            },
            another_intent_scenario.name: {
                "intents": ["another_test_intent"],
                "phrases": [],
            },
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    in_event = InEvent(user=user, intent="", text="another start")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx)

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == another_matchtext_scenario.get_node_by_id("id_2").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_in_out_out(mock_scenario: Scenario) -> None:
    matchtext_node = MatchText(
        element_id="id_1",
        value="start",
        next_ids=["id_2"],
        node_type=NodeType.matchText,
    )
    matchtext_out_node = OutMessage(
        element_id="id_2",
        value="TEXT_matchtext_scenario",
        next_ids=["id_3"],
        node_type=NodeType.outMessage,
    )
    matchtext_out_node2 = OutMessage(
        element_id="id_3",
        value="TEXT_matchtext_scenario2",
        next_ids=[],
        node_type=NodeType.outMessage,
    )
    matchtext_scenario = Scenario(
        "matchtext_test",
        "id_1",
        {
            "id_1": matchtext_node,
            "id_2": matchtext_out_node,
            "id_3": matchtext_out_node2,
        },
    )

    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            matchtext_scenario.name: matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx)

    assert len(out_events) == 2
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert out_events[1].text == matchtext_scenario.get_node_by_id("id_3").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_in_out_in(mock_scenario: Scenario) -> None:
    matchtext_node = MatchText(
        element_id="id_1",
        value="start",
        next_ids=["id_2"],
        node_type=NodeType.matchText,
    )
    matchtext_out_node = OutMessage(
        element_id="id_2",
        value="TEXT_matchtext_scenario",
        next_ids=["id_3"],
        node_type=NodeType.outMessage,
    )
    in_node = InMessage(
        element_id="id_3",
        value="",
        next_ids=[],
        node_type=NodeType.inMessage,
    )
    matchtext_scenario = Scenario(
        "matchtext_test",
        "id_1",
        {
            "id_1": matchtext_node,
            "id_2": matchtext_out_node,
            "id_3": in_node,
        },
    )

    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            matchtext_scenario.name: matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx)

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert user.current_node_id == in_node.element_id
    assert user.current_scenario_name == matchtext_scenario.name


@pytest.mark.asyncio
async def test_in_out_out_in(mock_scenario: Scenario) -> None:
    matchtext_node = MatchText(
        element_id="id_1",
        value="start",
        next_ids=["id_2"],
        node_type=NodeType.matchText,
    )
    matchtext_out_node = OutMessage(
        element_id="id_2",
        value="TEXT_matchtext_scenario",
        next_ids=["id_3"],
        node_type=NodeType.outMessage,
    )
    matchtext_out_node2 = OutMessage(
        element_id="id_3",
        value="TEXT_matchtext_scenario2",
        next_ids=["id_4"],
        node_type=NodeType.outMessage,
    )
    in_node = InMessage(
        element_id="id_4",
        value="",
        next_ids=[],
        node_type=NodeType.inMessage,
    )
    matchtext_scenario = Scenario(
        "matchtext_test",
        "id_1",
        {
            "id_1": matchtext_node,
            "id_2": matchtext_out_node,
            "id_3": matchtext_out_node2,
            "id_4": in_node,
        },
    )

    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            matchtext_scenario.name: matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx)

    assert len(out_events) == 2
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert out_events[1].text == matchtext_scenario.get_node_by_id("id_3").value
    assert user.current_node_id == in_node.element_id
    assert user.current_scenario_name == matchtext_scenario.name


@pytest.mark.asyncio
async def test_in_out_x7_in(mock_scenario: Scenario) -> None:
    matchtext_node = MatchText(
        element_id="id_1",
        value="start",
        next_ids=["id_2"],
        node_type=NodeType.matchText,
    )
    matchtext_out_node = OutMessage(
        element_id="id_2",
        value="TEXT_matchtext_scenario",
        next_ids=["id_3"],
        node_type=NodeType.outMessage,
    )
    matchtext_out_node2 = OutMessage(
        element_id="id_3",
        value="TEXT_matchtext_scenario2",
        next_ids=["id_4"],
        node_type=NodeType.outMessage,
    )
    matchtext_out_node3 = OutMessage(
        element_id="id_4",
        value="TEXT_matchtext_scenario3",
        next_ids=["id_5"],
        node_type=NodeType.outMessage,
    )
    matchtext_out_node4 = OutMessage(
        element_id="id_5",
        value="TEXT_matchtext_scenario4",
        next_ids=["id_6"],
        node_type=NodeType.outMessage,
    )
    matchtext_out_node5 = OutMessage(
        element_id="id_6",
        value="TEXT_matchtext_scenario5",
        next_ids=["id_7"],
        node_type=NodeType.outMessage,
    )
    matchtext_out_node6 = OutMessage(
        element_id="id_7",
        value="TEXT_matchtext_scenario6",
        next_ids=["id_8"],
        node_type=NodeType.outMessage,
    )
    matchtext_out_node7 = OutMessage(
        element_id="id_8",
        value="TEXT_matchtext_scenario7",
        next_ids=["id_9"],
        node_type=NodeType.outMessage,
    )
    in_node = InMessage(
        element_id="id_9",
        value="",
        next_ids=[],
        node_type=NodeType.inMessage,
    )
    matchtext_scenario = Scenario(
        "matchtext_test",
        "id_1",
        {
            "id_1": matchtext_node,
            "id_2": matchtext_out_node,
            "id_3": matchtext_out_node2,
            "id_4": matchtext_out_node3,
            "id_5": matchtext_out_node4,
            "id_6": matchtext_out_node5,
            "id_7": matchtext_out_node6,
            "id_8": matchtext_out_node7,
            "id_9": in_node,
        },
    )

    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            matchtext_scenario.name: matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start")
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
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert out_events[1].text == matchtext_scenario.get_node_by_id("id_3").value
    assert out_events[2].text == matchtext_scenario.get_node_by_id("id_4").value
    assert out_events[3].text == matchtext_scenario.get_node_by_id("id_5").value
    assert out_events[4].text == matchtext_scenario.get_node_by_id("id_6").value
    assert out_events[5].text == matchtext_scenario.get_node_by_id("id_7").value
    assert out_events[6].text == matchtext_scenario.get_node_by_id("id_8").value
    assert user.current_node_id == in_node.element_id
    assert user.current_scenario_name == matchtext_scenario.name


@pytest.mark.asyncio
async def test_in_out_in_out(mock_scenario: Scenario) -> None:
    matchtext_node = MatchText(
        element_id="id_1",
        value="start",
        next_ids=["id_2"],
        node_type=NodeType.matchText,
    )
    matchtext_out_node = OutMessage(
        element_id="id_2",
        value="TEXT_matchtext_scenario",
        next_ids=["id_3"],
        node_type=NodeType.outMessage,
    )
    in_node = InMessage(
        element_id="id_3",
        value="",
        next_ids=["id_4"],
        node_type=NodeType.inMessage,
    )
    matchtext_out_node2 = OutMessage(
        element_id="id_4",
        value="TEXT_matchtext_scenario2",
        next_ids=[],
        node_type=NodeType.outMessage,
    )
    matchtext_scenario = Scenario(
        "matchtext_test",
        "id_1",
        {
            "id_1": matchtext_node,
            "id_2": matchtext_out_node,
            "id_3": in_node,
            "id_4": matchtext_out_node2,
        },
    )

    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            matchtext_scenario.name: matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx)

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert user.current_node_id == in_node.element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event = InEvent(user=user, text="Some blah blah")
    out_events, new_ctx = await ep.process_event(in_event, ctx)

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_4").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_in_out_buttons_out(mock_scenario: Scenario) -> None:
    matchtext_node = MatchText(
        element_id="id_1",
        value="start",
        next_ids=["id_2"],
        node_type=NodeType.matchText,
    )
    buttons = [("TEXT1_1", "id_98"), ("TEXT1_2", "id_99")]
    matchtext_out_node = OutMessage(
        element_id="id_2",
        value="TEXT_matchtext_scenario",
        next_ids=["id_3"],
        node_type=NodeType.outMessage,
        buttons=buttons,
    )
    matchtext_out_node2 = OutMessage(
        element_id="id_3",
        value="TEXT_matchtext_scenario2",
        next_ids=[],
        node_type=NodeType.outMessage,
    )
    matchtext_scenario = Scenario(
        "matchtext_test",
        "id_1",
        {
            "id_1": matchtext_node,
            "id_2": matchtext_out_node,
            "id_3": matchtext_out_node2,
        },
    )

    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            matchtext_scenario.name: matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx)

    assert len(out_events) == 2
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert out_events[0].buttons is not None
    assert out_events[0].buttons[0].text == buttons[0][0]
    assert out_events[0].buttons[0].callback_data == buttons[0][1]
    assert out_events[0].buttons[1].text == buttons[1][0]
    assert out_events[0].buttons[1].callback_data == buttons[1][1]
    assert out_events[1].text == matchtext_scenario.get_node_by_id("id_3").value
    assert out_events[1].buttons is None
    assert user.current_node_id == matchtext_out_node.element_id
    assert user.current_scenario_name == matchtext_scenario.name


@pytest.mark.asyncio
async def test_in_out_buttons_out_in(mock_scenario: Scenario) -> None:
    matchtext_node = MatchText(
        element_id="id_1",
        value="start",
        next_ids=["id_2"],
        node_type=NodeType.matchText,
    )
    buttons = [("TEXT1_1", "id_98"), ("TEXT1_2", "id_99")]
    matchtext_out_node = OutMessage(
        element_id="id_2",
        value="TEXT_matchtext_scenario",
        next_ids=["id_3"],
        node_type=NodeType.outMessage,
        buttons=buttons,
    )
    matchtext_out_node2 = OutMessage(
        element_id="id_3",
        value="TEXT_matchtext_scenario2",
        next_ids=["id_4"],
        node_type=NodeType.outMessage,
    )
    in_node = InMessage(
        element_id="id_4",
        value="",
        next_ids=[],
        node_type=NodeType.inMessage,
    )
    matchtext_scenario = Scenario(
        "matchtext_test",
        "id_1",
        {
            "id_1": matchtext_node,
            "id_2": matchtext_out_node,
            "id_3": matchtext_out_node2,
            "id_4": in_node,
        },
    )

    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            matchtext_scenario.name: matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx)

    assert len(out_events) == 2
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert out_events[0].buttons is not None
    assert out_events[0].buttons[0].text == buttons[0][0]
    assert out_events[0].buttons[0].callback_data == buttons[0][1]
    assert out_events[0].buttons[1].text == buttons[1][0]
    assert out_events[0].buttons[1].callback_data == buttons[1][1]
    assert out_events[1].text == matchtext_scenario.get_node_by_id("id_3").value
    assert out_events[1].buttons is None
    assert user.current_node_id == in_node.element_id
    assert user.current_scenario_name == matchtext_scenario.name


@pytest.mark.asyncio
async def test_in_out_buttons_out_in_button_out(mock_scenario: Scenario) -> None:
    matchtext_node = MatchText(
        element_id="id_1",
        value="start",
        next_ids=["id_2"],
        node_type=NodeType.matchText,
    )
    buttons = [("TEXT1_1", "id_4"), ("TEXT1_2", "id_99")]
    matchtext_out_node = OutMessage(
        element_id="id_2",
        value="TEXT_matchtext_scenario",
        next_ids=["id_3"],
        node_type=NodeType.outMessage,
        buttons=buttons,
    )
    matchtext_out_node2 = OutMessage(
        element_id="id_3",
        value="TEXT_matchtext_scenario2",
        next_ids=[],
        node_type=NodeType.outMessage,
    )
    matchtext_out_node3 = OutMessage(
        element_id="id_4",
        value="TEXT_matchtext_scenario3",
        next_ids=[],
        node_type=NodeType.outMessage,
    )
    matchtext_scenario = Scenario(
        "matchtext_test",
        "id_1",
        {
            "id_1": matchtext_node,
            "id_2": matchtext_out_node,
            "id_3": matchtext_out_node2,
            "id_4": matchtext_out_node3,
        },
    )

    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            matchtext_scenario.name: matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx)

    assert len(out_events) == 2
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert out_events[0].buttons is not None
    assert out_events[0].buttons[0].text == buttons[0][0]
    assert out_events[0].buttons[0].callback_data == buttons[0][1]
    assert out_events[0].buttons[1].text == buttons[1][0]
    assert out_events[0].buttons[1].callback_data == buttons[1][1]
    assert out_events[1].text == matchtext_scenario.get_node_by_id("id_3").value
    assert out_events[1].buttons is None
    assert user.current_node_id == matchtext_out_node.element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event = InEvent(user=user, text="", button_pushed_next="id_4")
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_4").value
    assert out_events[0].buttons is None


@pytest.mark.asyncio
async def test_double_click(mock_scenario: Scenario) -> None:
    matchtext_node = MatchText(
        element_id="id_1",
        value="start",
        next_ids=["id_2"],
        node_type=NodeType.matchText,
    )
    buttons = [("TEXT1_1", "id_3")]
    matchtext_out_node = OutMessage(
        element_id="id_2",
        value="TEXT_matchtext_scenario",
        next_ids=[],
        node_type=NodeType.outMessage,
        buttons=buttons,
    )
    buttons2 = [("TEXT1_2", "id_4")]
    matchtext_out_node2 = OutMessage(
        element_id="id_3",
        value="TEXT_matchtext_scenario2",
        next_ids=[],
        node_type=NodeType.outMessage,
        buttons=buttons2,
    )
    matchtext_out_node3 = OutMessage(
        element_id="id_4",
        value="TEXT_matchtext_scenario3",
        next_ids=[],
        node_type=NodeType.outMessage,
    )
    matchtext_scenario = Scenario(
        "matchtext_test",
        "id_1",
        {
            "id_1": matchtext_node,
            "id_2": matchtext_out_node,
            "id_3": matchtext_out_node2,
            "id_4": matchtext_out_node3,
        },
    )

    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            matchtext_scenario.name: matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_out_node.value
    assert out_events[0].buttons is not None
    assert len(out_events[0].buttons) == 1
    assert out_events[0].buttons[0].text == buttons[0][0]
    assert out_events[0].buttons[0].callback_data == buttons[0][1]
    assert user.current_node_id == matchtext_out_node.element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event2 = InEvent(user=user, button_pushed_next="id_3")
    out_events, new_ctx = await ep.process_event(in_event2, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_out_node2.value
    assert out_events[0].buttons is not None
    assert len(out_events[0].buttons) == 1
    assert out_events[0].buttons[0].text == buttons2[0][0]
    assert out_events[0].buttons[0].callback_data == buttons2[0][1]
    assert user.current_node_id == matchtext_out_node2.element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event3 = InEvent(user=user, button_pushed_next="id_4")
    out_events, new_ctx = await ep.process_event(in_event3, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_out_node3.value
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
async def test_logical_unit_not(mock_scenario: Scenario) -> None:
    matchtext_node = MatchText(
        element_id="id_1",
        value="start",
        next_ids=["id_2"],
        node_type=NodeType.matchText,
    )
    matchtext_out_node = OutMessage(
        element_id="id_2",
        value="TEXT_matchtext_scenario",
        next_ids=["id_3"],
        node_type=NodeType.outMessage,
    )
    in_node = InMessage(
        element_id="id_3",
        value="",
        next_ids=["id_4"],
        node_type=NodeType.inMessage,
    )
    extract_node = DataExtract(
        element_id="id_4",
        value="re(^[Дд]а$)",
        next_ids=["id_5"],
        node_type=NodeType.dataExtract,
    )
    not_node = LogicalUnit(
        element_id="id_5",
        value="NOT",
        next_ids=["id_6", "id_7"],
        node_type=NodeType.logicalUnit,
    )
    matchtext_out_node1 = OutMessage(
        element_id="id_6",
        value="TEXT_matchtext_scenario1",
        next_ids=[],
        node_type=NodeType.outMessage,
    )
    matchtext_out_node2 = OutMessage(
        element_id="id_7",
        value="TEXT_matchtext_scenario2",
        next_ids=[],
        node_type=NodeType.outMessage,
    )
    matchtext_scenario = Scenario(
        "matchtext_test",
        "id_1",
        {
            "id_1": matchtext_node,
            "id_2": matchtext_out_node,
            "id_3": in_node,
            "id_4": extract_node,
            "id_5": not_node,
            "id_6": matchtext_out_node1,
            "id_7": matchtext_out_node2,
        },
    )

    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            matchtext_scenario.name: matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    start_in_event = InEvent(user=user, text="start")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(start_in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_out_node.value
    assert user.current_node_id == in_node.element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event2 = InEvent(user=user, text="нетнетнет")
    out_events, new_ctx = await ep.process_event(in_event2, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_out_node1.value
    assert user.current_node_id is None
    assert user.current_scenario_name is None

    # и еще раз, по другому пути
    out_events, new_ctx = await ep.process_event(start_in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_out_node.value
    assert user.current_node_id == in_node.element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event2 = InEvent(user=user, text="да")
    out_events, new_ctx = await ep.process_event(in_event2, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_out_node2.value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_logical_unit_and(mock_scenario: Scenario) -> None:
    matchtext_node = MatchText(
        element_id="id_1",
        value="start",
        next_ids=["id_2"],
        node_type=NodeType.matchText,
    )
    matchtext_out_node = OutMessage(
        element_id="id_2",
        value="TEXT_matchtext_scenario",
        next_ids=["id_3"],
        node_type=NodeType.outMessage,
    )
    in_node = InMessage(
        element_id="id_3",
        value="",
        next_ids=["id_4"],
        node_type=NodeType.inMessage,
    )
    extract_node = DataExtract(
        element_id="id_4",
        value="re(^[Дд]а$)",
        next_ids=["id_5"],
        node_type=NodeType.dataExtract,
    )
    request_node = RemoteRequest(
        element_id="id_8",
        next_ids=["id_9"],
        node_type=NodeType.remoteRequest,
        value="""(curl -XGET 'https://catfact.ninja/fact')""",
    )
    extract_node_rr = DataExtract(
        element_id="id_9",
        next_ids=["id_5"],
        node_type=NodeType.dataExtract,
        value="""json(["length"])""",
    )
    and_node = LogicalUnit(
        element_id="id_5",
        value="AND",
        next_ids=["id_6", "id_7"],
        node_type=NodeType.logicalUnit,
    )
    matchtext_out_node1 = OutMessage(
        element_id="id_6",
        value="TEXT_matchtext_scenario1",
        next_ids=[],
        node_type=NodeType.outMessage,
    )
    matchtext_out_node2 = OutMessage(
        element_id="id_7",
        value="TEXT_matchtext_scenario2",
        next_ids=[],
        node_type=NodeType.outMessage,
    )
    matchtext_scenario = Scenario(
        "matchtext_test",
        "id_1",
        {
            "id_1": matchtext_node,
            "id_2": matchtext_out_node,
            "id_3": in_node,
            "id_4": extract_node,
            "id_5": and_node,
            "id_6": matchtext_out_node1,
            "id_7": matchtext_out_node2,
            "id_8": request_node,
            "id_9": extract_node_rr,
        },
    )

    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            matchtext_scenario.name: matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    start_in_event = InEvent(user=user, text="start")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(start_in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_out_node.value
    assert user.current_node_id == in_node.element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event2 = InEvent(user=user, text="нетнетнет")
    out_events, new_ctx = await ep.process_event(in_event2, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_out_node2.value
    assert user.current_node_id is None
    assert user.current_scenario_name is None

    # и еще раз, по другому пути
    out_events, new_ctx = await ep.process_event(start_in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_out_node.value
    assert user.current_node_id == in_node.element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event2 = InEvent(user=user, text="да")
    out_events, new_ctx = await ep.process_event(in_event2, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_out_node1.value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_cycle_until_done(mock_scenario: Scenario) -> None:
    matchtext_node = MatchText(
        element_id="id_1",
        value="start",
        next_ids=["id_2"],
        node_type=NodeType.matchText,
    )
    matchtext_out_node = OutMessage(
        element_id="id_2",
        value="TEXT_matchtext_scenario",
        next_ids=["id_3"],
        node_type=NodeType.outMessage,
    )
    in_node = InMessage(
        element_id="id_3",
        value="",
        next_ids=["id_4"],
        node_type=NodeType.inMessage,
    )
    extract_node = DataExtract(
        element_id="id_4",
        next_ids=["id_5"],
        node_type=NodeType.dataExtract,
        value="re(^[Дд]а$)",
    )
    logical_not = LogicalUnit(
        element_id="id_5",
        next_ids=["id_6", "id_7"],
        node_type=NodeType.logicalUnit,
        value="NOT",
    )
    out_node = OutMessage(
        element_id="id_6",
        value="TEXT1",
        next_ids=["id_3"],
        node_type=NodeType.outMessage,
    )
    out_node2 = OutMessage(
        element_id="id_7",
        value="TEXT2",
        next_ids=[],
        node_type=NodeType.outMessage,
    )
    matchtext_scenario = Scenario(
        "matchtext_test",
        "id_1",
        {
            "id_1": matchtext_node,
            "id_2": matchtext_out_node,
            "id_3": in_node,
            "id_4": extract_node,
            "id_5": logical_not,
            "id_6": out_node,
            "id_7": out_node2,
        },
    )

    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            matchtext_scenario.name: matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    start_in_event = InEvent(user=user, text="start")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(start_in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_out_node.value
    assert user.current_node_id == in_node.element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event = InEvent(user=user, text="не хочу заканчивать сценарий")
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == out_node.value
    assert user.current_node_id == in_node.element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event = InEvent(user=user, text="все равно не хочу")
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == out_node.value
    assert user.current_node_id == in_node.element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event = InEvent(user=user, text="да")
    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == out_node2.value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_set_variable(mock_scenario: Scenario) -> None:
    matchtext_node = MatchText(
        element_id="id_1",
        value="start",
        next_ids=["id_2"],
        node_type=NodeType.matchText,
    )
    matchtext_out_node = OutMessage(
        element_id="id_2",
        value="TEXT_matchtext_scenario",
        next_ids=["id_3"],
        node_type=NodeType.outMessage,
    )
    in_node = InMessage(
        element_id="id_3",
        value="",
        next_ids=["id_4"],
        node_type=NodeType.inMessage,
    )
    set_variable = SetVariable(
        element_id="id_4",
        value="user(test_var1)",
        next_ids=["id_5"],
        node_type=NodeType.setVariable,
    )
    matchtext_out_node2 = OutMessage(
        element_id="id_5",
        value="TEXT_matchtext_scenario2",
        next_ids=[],
        node_type=NodeType.outMessage,
    )
    matchtext_scenario = Scenario(
        "matchtext_test",
        "id_1",
        {
            "id_1": matchtext_node,
            "id_2": matchtext_out_node,
            "id_3": in_node,
            "id_4": set_variable,
            "id_5": matchtext_out_node2,
        },
    )

    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            matchtext_scenario.name: matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start")
    ctx: tp.Dict[str, str] = {"old_var": "some_text"}

    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_out_node.value
    assert user.current_node_id == in_node.element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event = InEvent(user=user, text="Hi!")
    out_events, new_ctx = await ep.process_event(in_event, new_ctx)
    assert len(new_ctx) == 2
    assert new_ctx["old_var"] == "some_text"
    assert new_ctx["test_var1"] == in_event.text
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_out_node2.value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_set_variable_update(mock_scenario: Scenario) -> None:
    matchtext_node = MatchText(
        element_id="id_1",
        value="start",
        next_ids=["id_2"],
        node_type=NodeType.matchText,
    )
    matchtext_out_node = OutMessage(
        element_id="id_2",
        value="TEXT_matchtext_scenario",
        next_ids=["id_3"],
        node_type=NodeType.outMessage,
    )
    in_node = InMessage(
        element_id="id_3",
        value="",
        next_ids=["id_4"],
        node_type=NodeType.inMessage,
    )
    set_variable = SetVariable(
        element_id="id_4",
        value="user(old_var)",
        next_ids=["id_5"],
        node_type=NodeType.setVariable,
    )
    matchtext_out_node2 = OutMessage(
        element_id="id_5",
        value="TEXT_matchtext_scenario2",
        next_ids=[],
        node_type=NodeType.outMessage,
    )
    matchtext_scenario = Scenario(
        "matchtext_test",
        "id_1",
        {
            "id_1": matchtext_node,
            "id_2": matchtext_out_node,
            "id_3": in_node,
            "id_4": set_variable,
            "id_5": matchtext_out_node2,
        },
    )

    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            matchtext_scenario.name: matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start")
    ctx: tp.Dict[str, str] = {"old_var": "some_text"}

    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_out_node.value
    assert user.current_node_id == in_node.element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event = InEvent(user=user, text="Hi!")
    out_events, new_ctx = await ep.process_event(in_event, new_ctx)
    assert len(new_ctx) == 1
    assert new_ctx["old_var"] == in_event.text
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_out_node2.value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_remote_request_node() -> None:
    user = User(outer_id="1")
    ctx: tp.Dict[str, str] = {}
    remote_request = RemoteRequest(
        element_id="id_1",
        next_ids=[],
        node_type=NodeType.remoteRequest,
        value="""(curl -XGET 'https://catfact.ninja/fact')""",
    )
    events, new_ctx, text_to_pipeline = await remote_request.execute(user, ctx, "")
    assert events == []
    assert new_ctx == {}
    ret = json.loads(text_to_pipeline)
    assert "fact" in ret and "length" in ret
    assert len(ret["fact"]) == ret["length"]


@pytest.mark.asyncio
async def test_data_extract_json() -> None:
    user = User(outer_id="1")
    ctx: tp.Dict[str, str] = {}
    extract_node = DataExtract(
        element_id="id_1",
        next_ids=[],
        node_type=NodeType.dataExtract,
        value="""json(["first_key"][0]["second_key"])""",
    )
    json_to_extract = """{"first_key": [{"second_key": "tadam!"}]}"""
    events, new_ctx, text_to_pipeline = await extract_node.execute(
        user, ctx, json_to_extract
    )
    assert events == []
    assert new_ctx == {}
    assert text_to_pipeline == "tadam!"


@pytest.mark.asyncio
async def test_remote_request_node_templating() -> None:
    user = User(outer_id="1")
    ctx: tp.Dict[str, str] = {"some_key": "fact"}
    remote_request = RemoteRequest(
        element_id="id_1",
        next_ids=[],
        node_type=NodeType.remoteRequest,
        value="""(curl -XGET 'https://catfact.ninja/#some_key#')""",  # fact
    )
    events, new_ctx, text_to_pipeline = await remote_request.execute(user, ctx, "")
    assert events == []
    assert new_ctx == {}
    ret = json.loads(text_to_pipeline)
    assert "fact" in ret and "length" in ret
    assert len(ret["fact"]) == ret["length"]


@pytest.mark.asyncio
async def test_edit_message(mock_scenario: Scenario) -> None:
    matchtext_node = MatchText(
        element_id="id_1",
        value="start",
        next_ids=["id_2"],
        node_type=NodeType.matchText,
    )
    matchtext_out_node = OutMessage(
        element_id="id_2",
        value="TEXT_matchtext_scenario",
        next_ids=["id_3"],
        node_type=NodeType.outMessage,
    )
    edit_node = EditMessage(
        element_id="id_3",
        value="edited text from node of editing",
        next_ids=["id_2", "id_4"],
        node_type=NodeType.editMessage,
    )
    matchtext_out_node2 = OutMessage(
        element_id="id_4",
        value="TEXT_matchtext_scenario2",
        next_ids=[],
        node_type=NodeType.outMessage,
    )
    matchtext_scenario = Scenario(
        "matchtext_test",
        "id_1",
        {
            "id_1": matchtext_node,
            "id_2": matchtext_out_node,
            "id_3": edit_node,
            "id_4": matchtext_out_node2,
        },
    )

    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            matchtext_scenario.name: matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx)

    assert len(out_events) == 3
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_out_node.value
    assert out_events[0].node_to_edit is None

    assert isinstance(out_events[1], OutEvent)
    assert out_events[1].text == edit_node.value
    assert out_events[1].node_to_edit == matchtext_out_node.element_id

    assert isinstance(out_events[2], OutEvent)
    assert out_events[2].text == matchtext_out_node2.value
    assert out_events[2].node_to_edit is None

    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
async def test_edit_message_and_final_node(mock_scenario: Scenario) -> None:
    matchtext_node = MatchText(
        element_id="id_1",
        value="start",
        next_ids=["id_2"],
        node_type=NodeType.matchText,
    )
    buttons = [("TEXT1_1", "id_3"), ("TEXT1_2", "id_4")]
    out_node = OutMessage(
        element_id="id_2",
        value="TEXT1",
        next_ids=[],
        node_type=NodeType.outMessage,
        buttons=buttons,
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
    matchtext_scenario = Scenario(
        "matchtext_test",
        "id_1",
        {
            "id_1": matchtext_node,
            "id_2": out_node,
            "id_3": edit_node,
            "id_4": out_node2,
        },
    )

    fake_sg = FakeScenarioGetter(
        {
            mock_scenario.name: mock_scenario,
            matchtext_scenario.name: matchtext_scenario,
        }
    )
    ep = EventProcessor(
        scenarios={
            matchtext_scenario.name: {"intents": [], "phrases": ["start"]},
            mock_scenario.name: {"intents": [], "phrases": []},
        },
        scenario_getter=fake_sg.find,
        default_scenario_name=mock_scenario.name,
    )

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == out_node.value
    assert out_events[0].node_to_edit is None
    assert isinstance(out_events[0].buttons, tp.List)
    assert isinstance(out_events[0].buttons[0], Button)
    assert out_events[0].buttons[0].text == buttons[0][0]
    assert out_events[0].buttons[0].callback_data == buttons[0][1]
    assert isinstance(out_events[0].buttons[1], Button)
    assert out_events[0].buttons[1].text == buttons[1][0]
    assert out_events[0].buttons[1].callback_data == buttons[1][1]

    in_event2 = InEvent(user=user, button_pushed_next="id_3")
    out_events, new_ctx = await ep.process_event(in_event2, ctx)
    assert len(out_events) == 2
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == edit_node.value
    assert out_events[0].node_to_edit == out_node.element_id
    assert isinstance(out_events[1], OutEvent)
    assert out_events[1].text == out_node2.value
    assert out_events[1].node_to_edit is None
    assert user.current_node_id is None
    assert user.current_scenario_name is None

    out_events, new_ctx = await ep.process_event(in_event, ctx)
    assert len(out_events) == 1

    in_event2 = InEvent(user=user, button_pushed_next="id_4")
    out_events, new_ctx = await ep.process_event(in_event2, ctx)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == out_node2.value
    assert out_events[0].node_to_edit is None
    assert user.current_node_id is None
    assert user.current_scenario_name is None
