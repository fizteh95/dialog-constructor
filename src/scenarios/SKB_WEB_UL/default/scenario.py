from src.domain.model import InIntent
from src.domain.model import NodeType
from src.domain.model import OutMessage
from src.domain.model import Scenario


def make_scenario() -> Scenario:
    mock_node = InIntent(
        element_id="id_1",
        value="mock_start",
        next_ids=["id_2"],
        node_type=NodeType.inIntent,
    )
    mock_out_node = OutMessage(
        element_id="id_2",
        value="TEXT1",
        next_ids=[],
        node_type=NodeType.outMessage,
    )
    default_scenario = Scenario(
        "default", "id_1", {"id_1": mock_node, "id_2": mock_out_node}
    )
    return default_scenario
