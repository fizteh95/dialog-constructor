import json
import typing as tp

import pytest

from src.domain.events import EventProcessor
from src.domain.model import Button
from src.domain.model import DataExtract
from src.domain.model import InEvent
from src.domain.model import NodeType
from src.domain.model import OutEvent
from src.domain.model import OutMessage
from src.domain.model import RemoteRequest
from src.domain.model import Scenario
from src.domain.model import User
from tests.conftest import FakeScenarioGetter


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scenarios", [["default", "intent_scenario", "matchtext_scenario"]]
)
async def test_start_matchtext_scenario(
    prepared_ep: tp.Tuple[EventProcessor, FakeScenarioGetter],
    matchtext_scenario: Scenario,
) -> None:
    ep, fake_sg = prepared_ep
    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scenarios", [["default", "intent_scenario", "matchtext_scenario_with_or"]]
)
async def test_start_matchtext_scenario_with_or(
    prepared_ep: tp.Tuple[EventProcessor, FakeScenarioGetter],
    matchtext_scenario_with_or: Scenario,
) -> None:
    ep, fake_sg = prepared_ep

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="not start", project_name="test_project")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario_with_or.get_node_by_id("id_4").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scenarios", [["default", "intent_scenario", "matchtext_scenario"]]
)
async def test_start_intent_scenario(
    prepared_ep: tp.Tuple[EventProcessor, FakeScenarioGetter],
    intent_scenario: Scenario,
) -> None:
    ep, fake_sg = prepared_ep

    user = User(outer_id="1")
    in_event = InEvent(
        user=user,
        intent="test_intent",
        text="phrase for triggered intent",
        project_name="test_project",
    )
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == intent_scenario.get_node_by_id("id_2").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scenarios", [["default", "intent_scenario_with_or", "matchtext_scenario"]]
)
async def test_start_intent_scenario_with_or(
    prepared_ep: tp.Tuple[EventProcessor, FakeScenarioGetter],
    intent_scenario_with_or: Scenario,
) -> None:
    ep, fake_sg = prepared_ep

    user = User(outer_id="1")
    in_event = InEvent(
        user=user,
        intent="test_intent2",
        text="phrase for triggered intent",
        project_name="test_project",
    )
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == intent_scenario_with_or.get_node_by_id("id_4").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scenarios", [["default", "intent_scenario", "matchtext_scenario"]]
)
async def test_start_default_scenario(
    prepared_ep: tp.Tuple[EventProcessor, FakeScenarioGetter], mock_scenario: Scenario
) -> None:
    ep, fake_sg = prepared_ep

    user = User(outer_id="1")
    in_event = InEvent(
        user=user, intent="habahaba", text="habahaba", project_name="test_project"
    )
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == mock_scenario.get_node_by_id("id_2").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scenarios",
    [
        [
            "default",
            "intent_scenario",
            "matchtext_scenario",
            "another_matchtext_scenario",
            "another_intent_scenario",
        ]
    ],
)
async def test_start_scenario_with_several_intent_scenarios(
    prepared_ep: tp.Tuple[EventProcessor, FakeScenarioGetter],
    another_intent_scenario: Scenario,
) -> None:
    ep, fake_sg = prepared_ep

    user = User(outer_id="1")
    in_event = InEvent(
        user=user,
        intent="another_test_intent",
        text="habahaba",
        project_name="test_project",
    )
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == another_intent_scenario.get_node_by_id("id_2").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scenarios",
    [
        [
            "default",
            "intent_scenario",
            "matchtext_scenario",
            "another_matchtext_scenario",
            "another_intent_scenario",
        ]
    ],
)
async def test_start_scenario_with_several_matchtext_scenarios(
    prepared_ep: tp.Tuple[EventProcessor, FakeScenarioGetter],
    another_matchtext_scenario: Scenario,
) -> None:
    ep, fake_sg = prepared_ep

    user = User(outer_id="1")
    in_event = InEvent(
        user=user, intent="", text="another start", project_name="test_project"
    )
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == another_matchtext_scenario.get_node_by_id("id_2").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            ["outMessage", "id_2", "TEXT_matchtext_scenario", ["id_3"], ""],
            ["outMessage", "id_3", "TEXT_matchtext_scenario2", [], ""],
        ]
    ],
)
async def test_in_out_out(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    assert len(out_events) == 2
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert out_events[1].text == matchtext_scenario.get_node_by_id("id_3").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            ["passNode", "id_2", "", ["id_3"], ""],
            ["outMessage", "id_3", "TEXT_matchtext_scenario2", [], ""],
        ]
    ],
)
async def test_in_pass_out(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_3").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            ["outMessage", "id_2", "TEXT_matchtext_scenario", ["id_3"], ""],
            ["inMessage", "id_3", "", [], ""],
        ]
    ],
)
async def test_in_out_in(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_3").element_id
    assert user.current_scenario_name == matchtext_scenario.name


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            ["outMessage", "id_2", "TEXT_matchtext_scenario", ["id_3"], ""],
            ["outMessage", "id_3", "TEXT_matchtext_scenario2", ["id_4"], ""],
            ["inMessage", "id_4", "", [], ""],
        ]
    ],
)
async def test_in_out_out_in(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    assert len(out_events) == 2
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert out_events[1].text == matchtext_scenario.get_node_by_id("id_3").value
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_4").element_id
    assert user.current_scenario_name == matchtext_scenario.name


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            ["outMessage", "id_2", "TEXT_matchtext_scenario", ["id_3"], ""],
            ["outMessage", "id_3", "TEXT_matchtext_scenario2", ["id_4"], ""],
            ["outMessage", "id_4", "TEXT_matchtext_scenario3", ["id_5"], ""],
            ["outMessage", "id_5", "TEXT_matchtext_scenario4", ["id_6"], ""],
            ["outMessage", "id_6", "TEXT_matchtext_scenario5", ["id_7"], ""],
            ["outMessage", "id_7", "TEXT_matchtext_scenario6", ["id_8"], ""],
            ["outMessage", "id_8", "TEXT_matchtext_scenario7", ["id_9"], ""],
            ["inMessage", "id_9", "", [], ""],
        ]
    ],
)
async def test_in_out_x7_in(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

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
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_9").element_id
    assert user.current_scenario_name == matchtext_scenario.name


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            ["outMessage", "id_2", "TEXT_matchtext_scenario", ["id_3"], ""],
            ["inMessage", "id_3", "", ["id_4"], ""],
            ["outMessage", "id_4", "TEXT_matchtext_scenario2", [], ""],
        ]
    ],
)
async def test_in_out_in_out(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_3").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event = InEvent(user=user, text="Some blah blah", project_name="test_project")
    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_4").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            [
                "outMessage",
                "id_2",
                "TEXT_matchtext_scenario",
                ["id_3"],
                [("TEXT1_1", "id_98", "", ""), ("TEXT1_2", "id_99", "", "")],
            ],
            ["outMessage", "id_3", "TEXT_matchtext_scenario2", [], ""],
        ]
    ],
)
async def test_in_out_buttons_out(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    assert len(out_events) == 2
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert out_events[0].buttons is not None
    assert out_events[0].buttons[0].text == "TEXT1_1"
    assert out_events[0].buttons[0].callback_data == "id_98"
    assert out_events[0].buttons[1].text == "TEXT1_2"
    assert out_events[0].buttons[1].callback_data == "id_99"
    assert out_events[1].text == matchtext_scenario.get_node_by_id("id_3").value
    assert out_events[1].buttons is None
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_2").element_id
    assert user.current_scenario_name == matchtext_scenario.name


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            [
                "outMessage",
                "id_2",
                "TEXT_matchtext_scenario",
                ["id_3"],
                [("TEXT1_1", "id_98", "", ""), ("TEXT1_2", "id_99", "", "")],
            ],
            ["outMessage", "id_3", "TEXT_matchtext_scenario2", ["id_4"], ""],
            ["inMessage", "id_4", "", [], ""],
        ]
    ],
)
async def test_in_out_buttons_out_in(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    assert len(out_events) == 2
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert out_events[0].buttons is not None
    assert out_events[0].buttons[0].text == "TEXT1_1"
    assert out_events[0].buttons[0].callback_data == "id_98"
    assert out_events[0].buttons[1].text == "TEXT1_2"
    assert out_events[0].buttons[1].callback_data == "id_99"
    assert out_events[1].text == matchtext_scenario.get_node_by_id("id_3").value
    assert out_events[1].buttons is None
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_4").element_id
    assert user.current_scenario_name == matchtext_scenario.name


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            [
                "outMessage",
                "id_2",
                "TEXT_matchtext_scenario",
                ["id_3"],
                [("TEXT1_1", "id_4", "", ""), ("TEXT1_2", "id_99", "", "")],
            ],
            ["outMessage", "id_3", "TEXT_matchtext_scenario2", [], ""],
            ["outMessage", "id_4", "TEXT_matchtext_scenario3", [], ""],
        ]
    ],
)
async def test_in_out_buttons_out_in_button_out(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    assert len(out_events) == 2
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert out_events[0].buttons is not None
    assert out_events[0].buttons[0].text == "TEXT1_1"
    assert out_events[0].buttons[0].callback_data == "id_4"
    assert out_events[0].buttons[1].text == "TEXT1_2"
    assert out_events[0].buttons[1].callback_data == "id_99"
    assert out_events[1].text == matchtext_scenario.get_node_by_id("id_3").value
    assert out_events[1].buttons is None
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_2").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event = InEvent(
        user=user, text="", button_pushed_next="id_4", project_name="test_project"
    )
    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_4").value
    assert out_events[0].buttons is None
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            ["outMessage", "id_2", "TEXT_scenario", [], [("TEXT1_1", "id_3", "", "")]],
            ["outMessage", "id_3", "TEXT_scenario2", [], [("TEXT1_2", "id_4", "", "")]],
            ["outMessage", "id_4", "TEXT_scenario3", [], ""],
        ]
    ],
)
async def test_double_click(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert out_events[0].buttons is not None
    assert len(out_events[0].buttons) == 1
    assert out_events[0].buttons[0].text == "TEXT1_1"
    assert out_events[0].buttons[0].callback_data == "id_3"
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_2").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event2 = InEvent(
        user=user, button_pushed_next="id_3", project_name="test_project"
    )
    out_events, new_ctx = await ep.process_event(in_event2, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_3").value
    assert out_events[0].buttons is not None
    assert len(out_events[0].buttons) == 1
    assert out_events[0].buttons[0].text == "TEXT1_2"
    assert out_events[0].buttons[0].callback_data == "id_4"
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_3").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event3 = InEvent(
        user=user, button_pushed_next="id_4", project_name="test_project"
    )
    out_events, new_ctx = await ep.process_event(in_event3, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_4").value
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
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            ["outMessage", "id_2", "TEXT_scenario", ["id_3"], ""],
            ["inMessage", "id_3", "", ["id_4"], ""],
            ["dataExtract", "id_4", "re(^[Дд]а$)", ["id_5"], ""],
            ["logicalUnit", "id_5", "NOT", ["id_6", "id_7"], ""],
            ["outMessage", "id_6", "TEXT_scenario2", [], ""],
            ["outMessage", "id_7", "TEXT_scenario3", [], ""],
        ]
    ],
)
async def test_logical_unit_not(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    start_in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {}
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    out_events, new_ctx = await ep.process_event(start_in_event, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_3").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event2 = InEvent(user=user, text="нетнетнет", project_name="test_project")
    out_events, new_ctx = await ep.process_event(in_event2, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_6").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None

    # и еще раз, по другому пути
    out_events, new_ctx = await ep.process_event(start_in_event, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_3").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event2 = InEvent(user=user, text="да", project_name="test_project")
    out_events, new_ctx = await ep.process_event(in_event2, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_7").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            ["outMessage", "id_2", "TEXT_scenario", ["id_3"], ""],
            ["inMessage", "id_3", "", ["id_4"], ""],
            ["dataExtract", "id_4", "re(^[Дд]а$)", ["id_5"], ""],
            ["logicalUnit", "id_5", "IF", ["id_6", "id_7"], ""],
            ["outMessage", "id_6", "TEXT_scenario2", [], ""],
            ["outMessage", "id_7", "TEXT_scenario3", [], ""],
        ]
    ],
)
async def test_logical_unit_if(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    start_in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {}
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    out_events, new_ctx = await ep.process_event(start_in_event, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_3").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event2 = InEvent(user=user, text="нетнетнет", project_name="test_project")
    out_events, new_ctx = await ep.process_event(in_event2, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_7").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None

    # и еще раз, по другому пути
    out_events, new_ctx = await ep.process_event(start_in_event, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_3").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event2 = InEvent(user=user, text="да", project_name="test_project")
    out_events, new_ctx = await ep.process_event(in_event2, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_6").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            ["outMessage", "id_2", "TEXT_scenario", ["id_3"], ""],
            ["inMessage", "id_3", "", ["id_4"], ""],
            ["dataExtract", "id_4", "re(^[Дд]а$)", ["id_5"], ""],
            [
                "remoteRequest",
                "id_8",
                """(curl -XGET 'https://catfact.ninja/fact')""",
                ["id_9"],
                "",
            ],
            ["dataExtract", "id_9", """json(["length"])""", ["id_5"], ""],
            ["logicalUnit", "id_5", "AND", ["id_6", "id_7"], ""],
            ["outMessage", "id_6", "TEXT_scenario2", [], ""],
            ["outMessage", "id_7", "TEXT_scenario3", [], ""],
        ]
    ],
)
async def test_logical_unit_and(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    start_in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {}
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    out_events, new_ctx = await ep.process_event(start_in_event, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_3").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event2 = InEvent(user=user, text="нетнетнет", project_name="test_project")
    out_events, new_ctx = await ep.process_event(in_event2, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_7").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None

    # и еще раз, по другому пути
    out_events, new_ctx = await ep.process_event(start_in_event, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_3").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event2 = InEvent(user=user, text="да", project_name="test_project")
    out_events, new_ctx = await ep.process_event(in_event2, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_6").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            ["outMessage", "id_2", "TEXT_scenario", ["id_3"], ""],
            ["inMessage", "id_3", "", ["id_4"], ""],
            ["dataExtract", "id_4", "re(^[Дд]а$)", ["id_5"], ""],
            ["logicalUnit", "id_5", "NOT", ["id_6", "id_7"], ""],
            ["outMessage", "id_6", "TEXT_scenario2", ["id_3"], ""],
            ["outMessage", "id_7", "TEXT_scenario3", [], ""],
        ]
    ],
)
async def test_cycle_until_done(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    start_in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {}
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    out_events, new_ctx = await ep.process_event(start_in_event, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_3").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event = InEvent(
        user=user, text="не хочу заканчивать сценарий", project_name="test_project"
    )
    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_6").value
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_3").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event = InEvent(user=user, text="все равно не хочу", project_name="test_project")
    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_6").value
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_3").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event = InEvent(user=user, text="да", project_name="test_project")
    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_7").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            ["outMessage", "id_2", "TEXT_scenario", ["id_3"], ""],
            ["inMessage", "id_3", "", ["id_4"], ""],
            ["setVariable", "id_4", "user(test_var1)", ["id_5"], ""],
            ["inMessage", "id_5", "", [], ""],
        ]
    ],
)
async def test_set_variable(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {"old_var": "some_text"}
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_3").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event = InEvent(user=user, text="Hi!", project_name="test_project")
    out_events, new_ctx = await ep.process_event(in_event, new_ctx, fake_sg.find)
    assert len(new_ctx) == 2
    assert new_ctx["old_var"] == "some_text"
    assert new_ctx["test_var1"] == in_event.text
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_5").element_id
    assert user.current_scenario_name == matchtext_scenario.name


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            ["outMessage", "id_2", "TEXT_scenario", ["id_3"], ""],
            ["inMessage", "id_3", "", ["id_4"], ""],
            ["setVariable", "id_4", "user(test_var1)=1", ["id_5"], ""],
            ["inMessage", "id_5", "", [], ""],
        ]
    ],
)
async def test_set_variable_as_value(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {"old_var": "some_text"}
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_3").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event = InEvent(user=user, text="Hi!", project_name="test_project")
    out_events, new_ctx = await ep.process_event(in_event, new_ctx, fake_sg.find)
    assert len(new_ctx) == 2
    assert new_ctx["old_var"] == "some_text"
    assert new_ctx["test_var1"] == "1"
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_5").element_id
    assert user.current_scenario_name == matchtext_scenario.name


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            ["outMessage", "id_2", "TEXT_scenario", ["id_3"], ""],
            ["inMessage", "id_3", "", ["id_4"], ""],
            ["setVariable", "id_4", "user(old_var)+=1", ["id_5"], ""],
            ["inMessage", "id_5", "", [], ""],
        ]
    ],
)
async def test_set_variable_as_plus(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {"old_var": "1"}
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)

    in_event = InEvent(user=user, text="Hi!", project_name="test_project")
    out_events, new_ctx = await ep.process_event(in_event, new_ctx, fake_sg.find)
    assert len(new_ctx) == 1
    assert new_ctx["old_var"] == "2"
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_5").element_id
    assert user.current_scenario_name == matchtext_scenario.name


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            ["outMessage", "id_2", "TEXT_scenario", ["id_3"], ""],
            ["inMessage", "id_3", "", ["id_4"], ""],
            ["setVariable", "id_4", "user(old_var)-=1", ["id_5"], ""],
            ["inMessage", "id_5", "", [], ""],
        ]
    ],
)
async def test_set_variable_as_minus(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {"old_var": "10"}
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)

    in_event = InEvent(user=user, text="Hi!", project_name="test_project")
    out_events, new_ctx = await ep.process_event(in_event, new_ctx, fake_sg.find)
    assert len(new_ctx) == 1
    assert new_ctx["old_var"] == "9"
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_5").element_id
    assert user.current_scenario_name == matchtext_scenario.name


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            ["outMessage", "id_2", "TEXT_scenario", ["id_3"], ""],
            ["inMessage", "id_3", "", ["id_4"], ""],
            ["setVariable", "id_4", "user(old_var)+= haba haba!", ["id_5"], ""],
            ["inMessage", "id_5", "", [], ""],
        ]
    ],
)
async def test_set_variable_as_plus_as_string(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {"old_var": "what?"}
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)

    in_event = InEvent(user=user, text="Hi!", project_name="test_project")
    out_events, new_ctx = await ep.process_event(in_event, new_ctx, fake_sg.find)
    assert len(new_ctx) == 1
    assert new_ctx["old_var"] == "what? haba haba!"
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_5").element_id
    assert user.current_scenario_name == matchtext_scenario.name


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            ["outMessage", "id_2", "TEXT_scenario", ["id_3"], ""],
            ["inMessage", "id_3", "", ["id_4"], ""],
            ["setVariable", "id_4", "user(old_var)", ["id_5"], ""],
            ["inMessage", "id_5", "", [], ""],
        ]
    ],
)
async def test_set_variable_update(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {"old_var": "some_text"}
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_3").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event = InEvent(user=user, text="Hi!", project_name="test_project")
    out_events, new_ctx = await ep.process_event(in_event, new_ctx, fake_sg.find)
    assert len(new_ctx) == 1
    assert new_ctx["old_var"] == in_event.text
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_5").element_id
    assert user.current_scenario_name == matchtext_scenario.name


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            ["setVariable", "id_2", "user(test_var1)", ["id_3"], ""],
            ["getVariable", "id_3", "user(test_var1)", ["id_4"], ""],
            ["dataExtract", "id_4", "re(^[Ss]tart$)", ["id_5"], ""],
            ["logicalUnit", "id_5", "NOT", ["id_6", "id_7"], ""],
            ["outMessage", "id_6", "TEXT_scenario2", [], ""],
            ["inMessage", "id_7", "", [], ""],
        ]
    ],
)
async def test_get_variable(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {"old_var": "some_text"}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    assert new_ctx["old_var"] == "some_text"
    assert new_ctx["test_var1"] == in_event.text
    assert len(out_events) == 0
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_7").element_id
    assert user.current_scenario_name == matchtext_scenario.name


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
        value="""json(first_key[0].second_key)""",
    )
    json_to_extract = """{"first_key": [{"second_key": "tadam!"}]}"""
    events, new_ctx, text_to_pipeline = await extract_node.execute(
        user, ctx, json_to_extract
    )
    assert events == []
    assert new_ctx == {}
    assert text_to_pipeline == "tadam!"


@pytest.mark.asyncio
async def test_data_extract_json_list() -> None:
    user = User(outer_id="1")
    ctx: tp.Dict[str, str] = {}
    extract_node = DataExtract(
        element_id="id_1",
        next_ids=[],
        node_type=NodeType.dataExtract,
        value="""jsonList([*].balance.RUB#[*].id#[*].requisites.inn)""",
    )
    json_to_extract = """[
        {
            "id": 7333876,
            "balance": {"RUB": 33118521.85, "USD": 0.0, "EUR": 0.0},
            "startDate": "20.06.2012",
            "hidden": false,
            "requisites": {
                "bankName": "ПАО 'СКБ-БАНК'",
                "address": "620078, г. Екатеринбург, ул. Малышева, дом 122",
                "bic": "046577756",
                "inn": "6608003052",
                "corrAccount": "30101810800000000756"
            },
            "pdfLink": "/export/account/pdf/7333876"
        },
        {
            "id": 7333882,
            "balance": {"RUB": 0.0, "USD": 0.0, "EUR": 0.0},
            "startDate": "18.08.2017",
            "hidden": false,
            "requisites": {
                "bankName": "ПАО 'СКБ-БАНК'",
                "address": "620078, г. Екатеринбург, ул. Малышева, дом 122",
                "bic": "046577756",
                "inn": "6608003052",
                "corrAccount": "30101810800000000756"
            }
        }
    ]"""
    events, new_ctx, text_to_pipeline = await extract_node.execute(
        user, ctx, json_to_extract
    )
    assert events == []
    assert new_ctx == {}
    assert text_to_pipeline == json.dumps(
        [[33118521.85, 0.0], [7333876, 7333882], ["6608003052", "6608003052"]]
    )


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
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            ["outMessage", "id_2", "TEXT_matchtext_scenario", ["id_3"], ""],
            ["editMessage", "id_3", "edited text", ["id_2", "id_4"], ""],
            ["outMessage", "id_4", "TEXT_matchtext_scenario2", [], ""],
        ]
    ],
)
async def test_edit_message(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    assert len(out_events) == 3
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert out_events[0].node_to_edit is None

    assert isinstance(out_events[1], OutEvent)
    assert out_events[1].text == matchtext_scenario.get_node_by_id("id_3").value
    assert (
        out_events[1].node_to_edit
        == matchtext_scenario.get_node_by_id("id_2").element_id
    )

    assert isinstance(out_events[2], OutEvent)
    assert out_events[2].text == matchtext_scenario.get_node_by_id("id_4").value
    assert out_events[2].node_to_edit is None

    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            [
                "outMessage",
                "id_2",
                "TEXT1",
                [],
                [("TEXT1_1", "id_3", "", ""), ("TEXT1_2", "id_4", "", "")],
            ],
            ["editMessage", "id_3", "edited text", ["id_2", "id_4"], ""],
            ["outMessage", "id_4", "TEXT3", [], ""],
        ]
    ],
)
async def test_edit_message_and_final_node(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {}
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert out_events[0].node_to_edit is None
    assert isinstance(out_events[0].buttons, tp.List)
    assert isinstance(out_events[0].buttons[0], Button)
    assert out_events[0].buttons[0].text == "TEXT1_1"
    assert out_events[0].buttons[0].callback_data == "id_3"
    assert isinstance(out_events[0].buttons[1], Button)
    assert out_events[0].buttons[1].text == "TEXT1_2"
    assert out_events[0].buttons[1].callback_data == "id_4"

    in_event2 = InEvent(
        user=user, button_pushed_next="id_3", project_name="test_project"
    )
    out_events, new_ctx = await ep.process_event(in_event2, ctx, fake_sg.find)
    assert len(out_events) == 2
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_3").value
    assert (
        out_events[0].node_to_edit
        == matchtext_scenario.get_node_by_id("id_2").element_id
    )
    assert isinstance(out_events[1], OutEvent)
    assert out_events[1].text == matchtext_scenario.get_node_by_id("id_4").value
    assert out_events[1].node_to_edit is None
    assert user.current_node_id is None
    assert user.current_scenario_name is None

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    assert len(out_events) == 1

    in_event2 = InEvent(
        user=user, button_pushed_next="id_4", project_name="test_project"
    )
    out_events, new_ctx = await ep.process_event(in_event2, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_4").value
    assert out_events[0].node_to_edit is None
    assert user.current_node_id is None
    assert user.current_scenario_name is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["inIntent", "id_1", "test_intent", ["id_2"], ""],
            [
                "dataExtract",
                "id_2",
                "jsonList([*].balance.RUB#[*].id#[*].requisites.inn)",
                ["id_3"],
                "",
            ],
            OutMessage(
                element_id="id_3",
                next_ids=[],
                value="test text",
                node_type=NodeType.outMessage,
                procedural_source=True,
            ),
        ]
    ],
)
async def test_procedural_buttons(
    generate_intent_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter],
) -> None:
    ep, fake_sg = generate_intent_scenario

    user = User(outer_id="1")
    in_event = InEvent(
        user=user,
        intent="test_intent",
        text="""[
        {
            "id": 7333876,
            "balance": {"RUB": 33118521.85, "USD": 0.0, "EUR": 0.0},
            "startDate": "20.06.2012",
            "hidden": false,
            "requisites": {
                "bankName": "ПАО 'СКБ-БАНК'",
                "address": "620078, г. Екатеринбург, ул. Малышева, дом 122",
                "bic": "046577756",
                "inn": "6608003052",
                "corrAccount": "30101810800000000756"
            },
            "pdfLink": "/export/account/pdf/7333876"
        },
        {
            "id": 7333882,
            "balance": {"RUB": 0.0, "USD": 0.0, "EUR": 0.0},
            "startDate": "18.08.2017",
            "hidden": false,
            "requisites": {
                "bankName": "ПАО 'СКБ-БАНК'",
                "address": "620078, г. Екатеринбург, ул. Малышева, дом 122",
                "bic": "046577756",
                "inn": "6608003052",
                "corrAccount": "30101810800000000756"
            }
        }
    ]""",
        project_name="test_project",
    )
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    intent_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == intent_scenario.get_node_by_id("id_3").value

    assert out_events[0].buttons is not None
    assert len(out_events[0].buttons) == 2
    assert out_events[0].buttons[0].text == "33118521.85"
    assert out_events[0].buttons[0].text_to_bot == "7333876"
    assert out_events[0].buttons[0].text_to_chat == "6608003052"
    assert out_events[0].buttons[1].text == "0.0"
    assert out_events[0].buttons[1].text_to_bot == "7333882"
    assert out_events[0].buttons[1].text_to_chat == "6608003052"

    assert user.current_node_id == "id_3"
    assert user.current_scenario_name == "matchtext_test"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["inIntent", "id_1", "test_intent", ["id_2"], ""],
            [
                "dataExtract",
                "id_2",
                "jsonList([*].balance.RUB#[*].id#[*].requisites.inn)",
                ["id_3"],
                "",
            ],
            OutMessage(
                element_id="id_3",
                next_ids=[],
                value="test text",
                node_type=NodeType.outMessage,
                buttons=[
                    ("TEXT1.1", "", "1.1_to_bot", "1.1_to_chat"),
                    ("TEXT1.2", "", "1.2_to_bot", "1.2_to_chat"),
                ],
                procedural_source=True,
            ),
        ]
    ],
)
async def test_procedural_buttons_with_regular(
    generate_intent_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter],
) -> None:
    ep, fake_sg = generate_intent_scenario

    user = User(outer_id="1")
    in_event = InEvent(
        user=user,
        intent="test_intent",
        text="""[
        {
            "id": 7333876,
            "balance": {"RUB": 33118521.85, "USD": 0.0, "EUR": 0.0},
            "startDate": "20.06.2012",
            "hidden": false,
            "requisites": {
                "bankName": "ПАО 'СКБ-БАНК'",
                "address": "620078, г. Екатеринбург, ул. Малышева, дом 122",
                "bic": "046577756",
                "inn": "6608003052",
                "corrAccount": "30101810800000000756"
            },
            "pdfLink": "/export/account/pdf/7333876"
        },
        {
            "id": 7333882,
            "balance": {"RUB": 0.0, "USD": 0.0, "EUR": 0.0},
            "startDate": "18.08.2017",
            "hidden": false,
            "requisites": {
                "bankName": "ПАО 'СКБ-БАНК'",
                "address": "620078, г. Екатеринбург, ул. Малышева, дом 122",
                "bic": "046577756",
                "inn": "6608003052",
                "corrAccount": "30101810800000000756"
            }
        }
    ]""",
        project_name="test_project",
    )
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    intent_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == intent_scenario.get_node_by_id("id_3").value

    assert out_events[0].buttons is not None
    assert len(out_events[0].buttons) == 4
    assert out_events[0].buttons[0].text == "33118521.85"
    assert out_events[0].buttons[0].text_to_bot == "7333876"
    assert out_events[0].buttons[0].text_to_chat == "6608003052"
    assert out_events[0].buttons[1].text == "0.0"
    assert out_events[0].buttons[1].text_to_bot == "7333882"
    assert out_events[0].buttons[1].text_to_chat == "6608003052"
    assert out_events[0].buttons[2].text == "TEXT1.1"
    assert out_events[0].buttons[2].text_to_bot == "1.1_to_bot"
    assert out_events[0].buttons[2].text_to_chat == "1.1_to_chat"
    assert out_events[0].buttons[3].text == "TEXT1.2"
    assert out_events[0].buttons[3].text_to_bot == "1.2_to_bot"
    assert out_events[0].buttons[3].text_to_chat == "1.2_to_chat"

    assert user.current_node_id == "id_3"
    assert user.current_scenario_name == "matchtext_test"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            [
                "outMessage",
                "id_2",
                "TEXT_matchtext_scenario",
                ["id_3"],
                [("TEXT1_1", "id_98", "", ""), ("TEXT1_2", "id_99", "", "")],
            ],
            ["inMessage", "id_3", "", [], ""],
        ]
    ],
)
async def test_next_block_after_buttons(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert out_events[0].buttons is not None
    assert out_events[0].buttons[0].text == "TEXT1_1"
    assert out_events[0].buttons[0].callback_data == "id_98"
    assert out_events[0].buttons[1].text == "TEXT1_2"
    assert out_events[0].buttons[1].callback_data == "id_99"
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_3").element_id
    assert user.current_scenario_name == matchtext_scenario.name


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "elements",
    [
        [
            ["matchText", "id_1", "start", ["id_2"], ""],
            [
                "outMessage",
                "id_2",
                "Закончим?",
                [],
                [("Да", "id_4", "", ""), ("Нет", "id_3", "", "")],
            ],
            ["loopCounter", "id_3", "2", ["id_2", "id_5"], ""],
            ["outMessage", "id_4", "Закончили", [], ""],
            ["outMessage", "id_5", "Закончили по счетчику", [], ""],
        ]
    ],
)
async def test_loop_counter(
    generate_scenario: tp.Tuple[EventProcessor, FakeScenarioGetter]
) -> None:
    ep, fake_sg = generate_scenario

    user = User(outer_id="1")
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx: tp.Dict[str, str] = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert out_events[0].buttons is not None
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_2").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event2 = InEvent(
        user=user, button_pushed_next="id_4", project_name="test_project"
    )
    out_events, new_ctx = await ep.process_event(in_event2, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_4").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None

    # теперь по счетчику
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    assert len(out_events) == 1
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_2").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    in_event3 = InEvent(
        user=user, button_pushed_next="id_3", project_name="test_project"
    )
    out_events, new_ctx = await ep.process_event(in_event3, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert ctx == {"__id_3_loopCount": "2"}
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_2").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    out_events, new_ctx = await ep.process_event(in_event3, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert ctx == {"__id_3_loopCount": "3"}
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_2").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    out_events, new_ctx = await ep.process_event(in_event3, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert ctx == {"__id_3_loopCount": "1"}
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_5").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None

    # теперь раньше превышения счетчика
    in_event = InEvent(user=user, text="start", project_name="test_project")
    ctx = {}

    out_events, new_ctx = await ep.process_event(in_event, ctx, fake_sg.find)
    matchtext_scenario = fake_sg.projects["test_project"]["matchtext_test"]

    assert len(out_events) == 1
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_2").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    out_events, new_ctx = await ep.process_event(in_event3, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_2").value
    assert ctx == {"__id_3_loopCount": "2"}
    assert user.current_node_id == matchtext_scenario.get_node_by_id("id_2").element_id
    assert user.current_scenario_name == matchtext_scenario.name

    out_events, new_ctx = await ep.process_event(in_event2, ctx, fake_sg.find)
    assert len(out_events) == 1
    assert isinstance(out_events[0], OutEvent)
    assert out_events[0].text == matchtext_scenario.get_node_by_id("id_4").value
    assert user.current_node_id is None
    assert user.current_scenario_name is None
