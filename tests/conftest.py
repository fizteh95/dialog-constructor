import json
import os
import typing as tp

import pytest

from src.adapters.alchemy.repository import SQLAlchemyRepo
from src.adapters.repository import AbstractRepo
from src.domain.events import EventProcessor
from src.domain.model import Event
from src.domain.model import ExecuteNode
from src.domain.model import InIntent
from src.domain.model import LogicalUnit
from src.domain.model import MatchText
from src.domain.model import NodeType
from src.domain.model import OutMessage
from src.domain.model import Scenario
from src.domain.model import class_dict


@pytest.fixture()
def mock_scenario() -> Scenario:
    mock_node = InIntent(
        element_id="id_1",
        value="mock_start",
        next_ids=["id_2"],
        node_type=NodeType.inIntent,
    )
    mock_out_node = OutMessage(
        element_id="id_2",
        value="TEXT_mock_scenario",
        next_ids=[],
        node_type=NodeType.outMessage,
    )

    default_scenario = Scenario(
        "default", "id_1", {"id_1": mock_node, "id_2": mock_out_node}
    )

    return default_scenario


@pytest.fixture()
def intent_scenario() -> Scenario:
    intent_node = InIntent(
        element_id="id_1",
        value="test_intent",
        next_ids=["id_2"],
        node_type=NodeType.inIntent,
    )
    intent_out_node = OutMessage(
        element_id="id_2",
        value="TEXT_intent_scenario",
        next_ids=[],
        node_type=NodeType.outMessage,
    )

    intent_scenario = Scenario(
        "intent_test", "id_1", {"id_1": intent_node, "id_2": intent_out_node}
    )

    return intent_scenario


@pytest.fixture()
def intent_scenario_with_or() -> Scenario:
    intent_node1 = InIntent(
        element_id="id_1",
        value="test_intent1",
        next_ids=["id_3"],
        node_type=NodeType.inIntent,
    )
    intent_node2 = InIntent(
        element_id="id_2",
        value="test_intent2",
        next_ids=["id_3"],
        node_type=NodeType.inIntent,
    )
    or_node = LogicalUnit(
        element_id="id_3",
        value="OR",
        next_ids=["id_4"],
        node_type=NodeType.logicalUnit,
    )
    intent_out_node = OutMessage(
        element_id="id_3",
        value="TEXT_intent_scenario_with_or",
        next_ids=[],
        node_type=NodeType.outMessage,
    )

    intent_scenario = Scenario(
        "intent_test",
        "id_1",
        {
            "id_1": intent_node1,
            "id_2": intent_node2,
            "id_3": or_node,
            "id_4": intent_out_node,
        },
    )

    return intent_scenario


@pytest.fixture()
def another_intent_scenario() -> Scenario:
    intent_node = InIntent(
        element_id="id_1",
        value="another_test_intent",
        next_ids=["id_2"],
        node_type=NodeType.inIntent,
    )
    intent_out_node = OutMessage(
        element_id="id_2",
        value="TEXT_another_intent_scenario",
        next_ids=[],
        node_type=NodeType.outMessage,
    )

    intent_scenario = Scenario(
        "another_intent_test", "id_1", {"id_1": intent_node, "id_2": intent_out_node}
    )

    return intent_scenario


@pytest.fixture()
def matchtext_scenario() -> Scenario:
    matchtext_node = MatchText(
        element_id="id_1",
        value="start",
        next_ids=["id_2"],
        node_type=NodeType.matchText,
    )
    matchtext_out_node = OutMessage(
        element_id="id_2",
        value="TEXT_matchtext_scenario",
        next_ids=[],
        node_type=NodeType.outMessage,
    )

    matchtext_scenario = Scenario(
        "matchtext_test", "id_1", {"id_1": matchtext_node, "id_2": matchtext_out_node}
    )

    return matchtext_scenario


@pytest.fixture()
def matchtext_scenario_with_or() -> Scenario:
    matchtext_node1 = MatchText(
        element_id="id_1",
        value="start",
        next_ids=["id_3"],
        node_type=NodeType.matchText,
    )
    matchtext_node2 = MatchText(
        element_id="id_2",
        value="not start",
        next_ids=["id_3"],
        node_type=NodeType.matchText,
    )
    or_node = LogicalUnit(
        element_id="id_3",
        value="OR",
        next_ids=["id_4"],
        node_type=NodeType.logicalUnit,
    )
    matchtext_out_node = OutMessage(
        element_id="id_4",
        value="TEXT_matchtext_scenario_with_or",
        next_ids=[],
        node_type=NodeType.outMessage,
    )

    matchtext_scenario = Scenario(
        "matchtext_test",
        "id_1",
        {
            "id_1": matchtext_node1,
            "id_2": matchtext_node2,
            "id_3": or_node,
            "id_4": matchtext_out_node,
        },
    )

    return matchtext_scenario


@pytest.fixture()
def another_matchtext_scenario() -> Scenario:
    matchtext_node = MatchText(
        element_id="id_1",
        value="another start",
        next_ids=["id_2"],
        node_type=NodeType.matchText,
    )
    matchtext_out_node = OutMessage(
        element_id="id_2",
        value="TEXT_another_matchtext_scenario",
        next_ids=[],
        node_type=NodeType.outMessage,
    )

    matchtext_scenario = Scenario(
        "another_matchtext_test",
        "id_1",
        {"id_1": matchtext_node, "id_2": matchtext_out_node},
    )

    return matchtext_scenario


class FakeListener:
    def __init__(self) -> None:
        self.events: tp.List[Event] = []

    async def handle_message(self, message: Event) -> tp.List[Event]:
        """Интерфейс для взаимодействия с шиной"""
        self.events.append(message)
        return []


class FakeScenarioGetter:
    def __init__(self, projects: tp.Dict[str, tp.Dict[str, Scenario]]) -> None:
        self.projects = projects

    async def find(self, name: str, project_name: str) -> Scenario:
        try:
            return self.projects[project_name][name]
        except KeyError as e:
            print(project_name)
            print(name)
            print(self.projects)
            raise


@pytest.fixture
def prepared_ep(
    scenarios: tp.List[str],
    mock_scenario: Scenario,
    intent_scenario: Scenario,
    matchtext_scenario: Scenario,
    intent_scenario_with_or: Scenario,
    another_intent_scenario: Scenario,
    matchtext_scenario_with_or: Scenario,
    another_matchtext_scenario: Scenario,
) -> tp.Tuple[EventProcessor, FakeScenarioGetter]:
    scenarios_dict = {
        "default": {"scenario": mock_scenario, "intents": [], "phrases": []},
        "intent_scenario": {
            "scenario": intent_scenario,
            "intents": ["test_intent"],
            "phrases": [],
        },
        "matchtext_scenario": {
            "scenario": matchtext_scenario,
            "intents": [],
            "phrases": ["start"],
        },
        "intent_scenario_with_or": {
            "scenario": intent_scenario_with_or,
            "intents": ["test_intent1", "test_intent2"],
            "phrases": [],
        },
        "another_intent_scenario": {
            "scenario": another_intent_scenario,
            "intents": ["another_test_intent"],
            "phrases": [],
        },
        "matchtext_scenario_with_or": {
            "scenario": matchtext_scenario_with_or,
            "intents": [],
            "phrases": ["start", "not start"],
        },
        "another_matchtext_scenario": {
            "scenario": another_matchtext_scenario,
            "intents": [],
            "phrases": ["another start"],
        },
    }
    dict_for_fake_getter = {
        "test_project": {
            k: v["scenario"] for k, v in scenarios_dict.items() if k in scenarios
        }
    }
    fake_sg = FakeScenarioGetter(dict_for_fake_getter)  # type: ignore
    ep = EventProcessor()
    for k, v in scenarios_dict.items():
        if k not in scenarios:
            continue
        ep.add_scenario(
            scenario_name=k,
            project_name="test_project",
            intents=v["intents"],
            phrases=v["phrases"],
        )
    return ep, fake_sg


@pytest.fixture
def generate_scenario(
    elements: tp.List[tp.List[tp.Any] | ExecuteNode],
) -> tp.Tuple[EventProcessor, FakeScenarioGetter]:
    """
    [
        ["inMessage", "id_1", "", ['id_2'], ""],
        ["outMessage", "id_2", "TEXT1", [], ""],
        ...
    ]
    тип, айдишник, значение, следующие ноды, кнопки
    """
    nodes = []  # : tp.List[ExecuteNode]
    for el in elements:
        if isinstance(el, tp.List):
            need_class = class_dict[el[0]]
            buttons = None
            if el[4]:
                buttons = el[4]
            node = need_class(  # type: ignore
                element_id=el[1],
                node_type=NodeType(el[0]),
                next_ids=el[3],
                value=el[2],
                buttons=buttons,
            )
        elif isinstance(el, ExecuteNode):
            node = el
        else:
            raise
        nodes.append(node)
    new_scenario = Scenario(
        "matchtext_test",
        "id_1",
        {x.element_id: x for x in nodes},
    )
    dict_for_fake_getter = {
        "test_project": {
            "default": mock_scenario,
            "matchtext_test": new_scenario,
        }
    }
    fake_sg = FakeScenarioGetter(dict_for_fake_getter)  # type: ignore
    ep = EventProcessor()
    ep.add_scenario(
        scenario_name="default",
        project_name="test_project",
        intents=[],
        phrases=[],
    )
    ep.add_scenario(
        scenario_name="matchtext_test",
        project_name="test_project",
        intents=[],
        phrases=["start"],
    )
    return ep, fake_sg


@pytest.fixture
def generate_intent_scenario(
    elements: tp.List[tp.List[tp.Any] | ExecuteNode],
) -> tp.Tuple[EventProcessor, FakeScenarioGetter]:
    """
    [
        ["inMessage", "id_1", "", ['id_2'], ""],
        ["outMessage", "id_2", "TEXT1", [], ""],
        ...
    ]
    тип, айдишник, значение, следующие ноды, кнопки
    """
    nodes = []  # : tp.List[ExecuteNode]
    for el in elements:
        if isinstance(el, tp.List):
            need_class = class_dict[el[0]]
            buttons = None
            if el[4]:
                buttons = el[4]
            node = need_class(  # type: ignore
                element_id=el[1],
                node_type=NodeType(el[0]),
                next_ids=el[3],
                value=el[2],
                buttons=buttons,
            )
        elif isinstance(el, ExecuteNode):
            node = el
        else:
            raise
        nodes.append(node)
    new_scenario = Scenario(
        "matchtext_test",
        "id_1",
        {x.element_id: x for x in nodes},
    )
    dict_for_fake_getter = {
        "test_project": {
            "default": mock_scenario,
            "matchtext_test": new_scenario,
        }
    }
    fake_sg = FakeScenarioGetter(dict_for_fake_getter)  # type: ignore
    ep = EventProcessor()
    ep.add_scenario(
        scenario_name="default",
        project_name="test_project",
        intents=[],
        phrases=[],
    )
    ep.add_scenario(
        scenario_name="matchtext_test",
        project_name="test_project",
        intents=["test_intent"],
        phrases=[],
    )
    return ep, fake_sg


@pytest.fixture
async def alchemy_repo() -> AbstractRepo:
    repo = SQLAlchemyRepo()
    await repo._recreate_db()  # noqa
    return repo
