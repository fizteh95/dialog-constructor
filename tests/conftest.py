import typing as tp

import pytest

from src.domain.model import Event
from src.domain.model import InIntent
from src.domain.model import LogicalUnit
from src.domain.model import MatchText
from src.domain.model import NodeType
from src.domain.model import OutMessage
from src.domain.model import Scenario


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
