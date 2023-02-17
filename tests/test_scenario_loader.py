from src.domain.model import DataExtract
from src.domain.model import EditMessage
from src.domain.model import GetVariable
from src.domain.model import InIntent
from src.domain.model import InMessage
from src.domain.model import LogicalUnit
from src.domain.model import LoopCounter
from src.domain.model import MatchText
from src.domain.model import NodeType
from src.domain.model import OutMessage
from src.domain.model import RemoteRequest
from src.domain.model import Scenario
from src.domain.model import SetVariable
from src.domain.scenario_loader import XMLParser


def test_scenario_loader_hello() -> None:
    xml_src_path = "tests/resources/hello.xml"
    parser = XMLParser()
    root_id, nodes = parser.parse(input_stuff=xml_src_path)
    assert root_id == "WIyWlLk6GJQsqaUBKTNV-3"
    assert len(nodes) == 10
    scenario = Scenario(
        name="test", root_id=root_id, nodes={x.element_id: x for x in nodes}
    )
    assert InIntent(
        element_id="WIyWlLk6GJQsqaUBKTNV-3",
        next_ids=["a4keutFGz-OHo49sqyN--0"],
        value="поздороваться",
        node_type=NodeType.inIntent,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("WIyWlLk6GJQsqaUBKTNV-3")
    assert RemoteRequest(
        element_id="a4keutFGz-OHo49sqyN--0",
        next_ids=["a4keutFGz-OHo49sqyN--2"],
        value="(curl -XGET 'http://localhost:8081/user/get_info')",
        node_type=NodeType.remoteRequest,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("a4keutFGz-OHo49sqyN--0")
    assert SetVariable(
        element_id="a4keutFGz-OHo49sqyN--2",
        next_ids=["a4keutFGz-OHo49sqyN--16"],
        value="user(user_info_answer)",
        node_type=NodeType.setVariable,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("a4keutFGz-OHo49sqyN--2")
    assert DataExtract(
        element_id="a4keutFGz-OHo49sqyN--4",
        next_ids=["a4keutFGz-OHo49sqyN--5"],
        value="json(name)",
        node_type=NodeType.dataExtract,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("a4keutFGz-OHo49sqyN--4")
    assert SetVariable(
        element_id="a4keutFGz-OHo49sqyN--5",
        next_ids=["a4keutFGz-OHo49sqyN--19"],
        value="user(name)",
        node_type=NodeType.setVariable,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("a4keutFGz-OHo49sqyN--5")
    assert DataExtract(
        element_id="a4keutFGz-OHo49sqyN--6",
        next_ids=["a4keutFGz-OHo49sqyN--7"],
        value="json(patronymic)",
        node_type=NodeType.dataExtract,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("a4keutFGz-OHo49sqyN--6")
    assert SetVariable(
        element_id="a4keutFGz-OHo49sqyN--7",
        next_ids=["a4keutFGz-OHo49sqyN--12"],
        value="user(patronymic)",
        node_type=NodeType.setVariable,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("a4keutFGz-OHo49sqyN--7")
    assert OutMessage(
        element_id="a4keutFGz-OHo49sqyN--12",
        next_ids=[],
        value="TEXT1",
        node_type=NodeType.outMessage,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("a4keutFGz-OHo49sqyN--12")
    assert GetVariable(
        element_id="a4keutFGz-OHo49sqyN--16",
        next_ids=["a4keutFGz-OHo49sqyN--4"],
        value="user(user_info_answer)",
        node_type=NodeType.getVariable,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("a4keutFGz-OHo49sqyN--16")
    assert GetVariable(
        element_id="a4keutFGz-OHo49sqyN--19",
        next_ids=["a4keutFGz-OHo49sqyN--6"],
        value="user(user_info_answer)",
        node_type=NodeType.getVariable,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("a4keutFGz-OHo49sqyN--19")


def test_scenario_loader_weather() -> None:
    xml_src_path = "tests/resources/weather.xml"
    parser = XMLParser()
    root_id, nodes = parser.parse(input_stuff=xml_src_path)
    assert root_id == "hLoXeLj0fWG0-EihJcVe-0"
    assert len(nodes) == 22
    scenario = Scenario(
        name="test", root_id=root_id, nodes={x.element_id: x for x in nodes}
    )
    assert MatchText(
        element_id="hLoXeLj0fWG0-EihJcVe-0",
        next_ids=["7HfLZjwwzprmSE3nwxrW-55"],
        value="/start",
        node_type=NodeType.matchText,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("hLoXeLj0fWG0-EihJcVe-0")
    assert InMessage(
        element_id="y2Gkiw3MHWRdAHyPFfPg-4",
        next_ids=["y2Gkiw3MHWRdAHyPFfPg-11"],
        value="",
        node_type=NodeType.inMessage,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("y2Gkiw3MHWRdAHyPFfPg-4")
    assert OutMessage(
        element_id="y2Gkiw3MHWRdAHyPFfPg-8",
        next_ids=["y2Gkiw3MHWRdAHyPFfPg-24"],
        value="TEXT3",
        node_type=NodeType.outMessage,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("y2Gkiw3MHWRdAHyPFfPg-8")
    assert DataExtract(
        element_id="y2Gkiw3MHWRdAHyPFfPg-11",
        next_ids=["7HfLZjwwzprmSE3nwxrW-0"],
        value="re(^[-+]?[1-9]\\d?$)",
        node_type=NodeType.dataExtract,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("y2Gkiw3MHWRdAHyPFfPg-11")
    assert RemoteRequest(
        element_id="y2Gkiw3MHWRdAHyPFfPg-21",
        next_ids=["y2Gkiw3MHWRdAHyPFfPg-37"],
        value="(curl -XGET 'https://api.open-meteo.com/v1/forecast?latitude={{latitude}}&longitude={{longitude}}&hourly=temperature_2m')",
        node_type=NodeType.remoteRequest,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("y2Gkiw3MHWRdAHyPFfPg-21")
    assert InMessage(
        element_id="y2Gkiw3MHWRdAHyPFfPg-24",
        next_ids=["y2Gkiw3MHWRdAHyPFfPg-28"],
        value="",
        node_type=NodeType.inMessage,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("y2Gkiw3MHWRdAHyPFfPg-24")
    assert DataExtract(
        element_id="y2Gkiw3MHWRdAHyPFfPg-28",
        next_ids=["7HfLZjwwzprmSE3nwxrW-15"],
        value="re(^[+-]?((180$)|(((1[0-7]\\d)|([1-9]\\d?))$)))",
        node_type=NodeType.dataExtract,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("y2Gkiw3MHWRdAHyPFfPg-28")
    assert DataExtract(
        element_id="y2Gkiw3MHWRdAHyPFfPg-37",
        next_ids=["7HfLZjwwzprmSE3nwxrW-25"],
        value='json(["hourly"]["temperature_2m"][0])',
        node_type=NodeType.dataExtract,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("y2Gkiw3MHWRdAHyPFfPg-37")
    assert OutMessage(
        element_id="y2Gkiw3MHWRdAHyPFfPg-41",
        next_ids=["H9drS6L4HsgGu72-MB-w-0"],
        value="TEXT5",
        node_type=NodeType.outMessage,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("y2Gkiw3MHWRdAHyPFfPg-41")
    assert OutMessage(
        element_id="H9drS6L4HsgGu72-MB-w-0",
        next_ids=[],
        value="TEXT7",
        node_type=NodeType.outMessage,
        buttons=[
            ("TEXT8", "H9drS6L4HsgGu72-MB-w-10", "", ""),
            ("TEXT9", "7HfLZjwwzprmSE3nwxrW-46", "", ""),
        ],
        procedural_source=False,
    ) == scenario.get_node_by_id("H9drS6L4HsgGu72-MB-w-0")
    assert EditMessage(
        element_id="H9drS6L4HsgGu72-MB-w-10",
        next_ids=["H9drS6L4HsgGu72-MB-w-0", "7HfLZjwwzprmSE3nwxrW-46"],
        value="TEXT10",
        node_type=NodeType.editMessage,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("H9drS6L4HsgGu72-MB-w-10")
    assert LogicalUnit(
        element_id="7HfLZjwwzprmSE3nwxrW-0",
        next_ids=["7HfLZjwwzprmSE3nwxrW-30", "7HfLZjwwzprmSE3nwxrW-33"],
        value="NOT",
        node_type=NodeType.logicalUnit,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("7HfLZjwwzprmSE3nwxrW-0")
    assert LogicalUnit(
        element_id="7HfLZjwwzprmSE3nwxrW-15",
        next_ids=["7HfLZjwwzprmSE3nwxrW-36", "7HfLZjwwzprmSE3nwxrW-39"],
        value="NOT",
        node_type=NodeType.logicalUnit,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("7HfLZjwwzprmSE3nwxrW-15")
    assert LogicalUnit(
        element_id="7HfLZjwwzprmSE3nwxrW-25",
        next_ids=["7HfLZjwwzprmSE3nwxrW-27", "7HfLZjwwzprmSE3nwxrW-42"],
        value="NOT",
        node_type=NodeType.logicalUnit,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("7HfLZjwwzprmSE3nwxrW-25")
    assert OutMessage(
        element_id="7HfLZjwwzprmSE3nwxrW-27",
        next_ids=[],
        value="TEXT6",
        node_type=NodeType.outMessage,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("7HfLZjwwzprmSE3nwxrW-27")
    assert OutMessage(
        element_id="7HfLZjwwzprmSE3nwxrW-30",
        next_ids=["y2Gkiw3MHWRdAHyPFfPg-4"],
        value="TEXT2",
        node_type=NodeType.outMessage,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("7HfLZjwwzprmSE3nwxrW-30")
    assert SetVariable(
        element_id="7HfLZjwwzprmSE3nwxrW-33",
        next_ids=["y2Gkiw3MHWRdAHyPFfPg-8"],
        value="user(latitude)",
        node_type=NodeType.setVariable,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("7HfLZjwwzprmSE3nwxrW-33")
    assert OutMessage(
        element_id="7HfLZjwwzprmSE3nwxrW-36",
        next_ids=["y2Gkiw3MHWRdAHyPFfPg-24"],
        value="TEXT4",
        node_type=NodeType.outMessage,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("7HfLZjwwzprmSE3nwxrW-36")
    assert SetVariable(
        element_id="7HfLZjwwzprmSE3nwxrW-39",
        next_ids=["y2Gkiw3MHWRdAHyPFfPg-21"],
        value="user(longitude)",
        node_type=NodeType.setVariable,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("7HfLZjwwzprmSE3nwxrW-39")
    assert SetVariable(
        element_id="7HfLZjwwzprmSE3nwxrW-42",
        next_ids=["y2Gkiw3MHWRdAHyPFfPg-41"],
        value="user(temperature)",
        node_type=NodeType.setVariable,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("7HfLZjwwzprmSE3nwxrW-42")
    assert OutMessage(
        element_id="7HfLZjwwzprmSE3nwxrW-46",
        next_ids=[],
        value="TEXT11",
        node_type=NodeType.outMessage,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("7HfLZjwwzprmSE3nwxrW-46")
    assert OutMessage(
        element_id="7HfLZjwwzprmSE3nwxrW-55",
        next_ids=["y2Gkiw3MHWRdAHyPFfPg-4"],
        value="TEXT1",
        node_type=NodeType.outMessage,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("7HfLZjwwzprmSE3nwxrW-55")


def test_scenario_loader_loop_counter() -> None:
    xml_src_path = "tests/resources/loop_counter.xml"
    parser = XMLParser()
    root_id, nodes = parser.parse(input_stuff=xml_src_path)
    assert root_id == "WIyWlLk6GJQsqaUBKTNV-3"
    assert len(nodes) == 8
    scenario = Scenario(
        name="test", root_id=root_id, nodes={x.element_id: x for x in nodes}
    )
    assert MatchText(
        element_id="WIyWlLk6GJQsqaUBKTNV-3",
        next_ids=["_ooN2HpQA74DP4gcZHRg-0"],
        value="/loopCounter",
        node_type=NodeType.matchText,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("WIyWlLk6GJQsqaUBKTNV-3")
    assert OutMessage(
        element_id="_ooN2HpQA74DP4gcZHRg-0",
        next_ids=[],
        value="TEXT1",
        node_type=NodeType.outMessage,
        buttons=[
            ("TEXT1.1", "_ooN2HpQA74DP4gcZHRg-18", "", ""),
            ("TEXT1.2", "_ooN2HpQA74DP4gcZHRg-18", "", ""),
            ("TEXT1.3", "_ooN2HpQA74DP4gcZHRg-23", "", ""),
        ],
        procedural_source=False,
    ) == scenario.get_node_by_id("_ooN2HpQA74DP4gcZHRg-0")
    assert OutMessage(
        element_id="_ooN2HpQA74DP4gcZHRg-7",
        next_ids=[],
        value="TEXT2",
        node_type=NodeType.outMessage,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("_ooN2HpQA74DP4gcZHRg-7")
    assert LoopCounter(
        element_id="_ooN2HpQA74DP4gcZHRg-9",
        next_ids=["_ooN2HpQA74DP4gcZHRg-12", "_ooN2HpQA74DP4gcZHRg-16"],
        value="2",
        node_type=NodeType.loopCounter,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("_ooN2HpQA74DP4gcZHRg-9")
    assert OutMessage(
        element_id="_ooN2HpQA74DP4gcZHRg-12",
        next_ids=["_ooN2HpQA74DP4gcZHRg-0"],
        value="TEXT3",
        node_type=NodeType.outMessage,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("_ooN2HpQA74DP4gcZHRg-12")
    assert OutMessage(
        element_id="_ooN2HpQA74DP4gcZHRg-16",
        next_ids=[],
        value="TEXT4",
        node_type=NodeType.outMessage,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("_ooN2HpQA74DP4gcZHRg-16")
    assert EditMessage(
        element_id="_ooN2HpQA74DP4gcZHRg-18",
        next_ids=["_ooN2HpQA74DP4gcZHRg-0", "_ooN2HpQA74DP4gcZHRg-9"],
        value="TEXT1",
        node_type=NodeType.editMessage,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("_ooN2HpQA74DP4gcZHRg-18")
    assert EditMessage(
        element_id="_ooN2HpQA74DP4gcZHRg-23",
        next_ids=["_ooN2HpQA74DP4gcZHRg-0", "_ooN2HpQA74DP4gcZHRg-7"],
        value="TEXT1",
        node_type=NodeType.editMessage,
        buttons=None,
        procedural_source=False,
    ) == scenario.get_node_by_id("_ooN2HpQA74DP4gcZHRg-23")
