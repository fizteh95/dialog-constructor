import typing as tp
from enum import Enum

from src.domain.model import ExecuteNode

# from src.dialogues.scenario_loader import NodeType

# from src.executor.domain import NodeType


class NodeType(Enum):
    inMessage = "inMessage"
    outMessage = "outMessage"
    editMessage = "editMessage"
    dataExtract = "dataExtract"
    logicalUnit = "logicalUnit"
    remoteRequest = "remoteRequest"
    setVariable = "setVariable"
    ...


texts = {
    "TEXT1": "test text 1",
    "TEXT2": "test text 2",
    "TEXT3": "test text 3",
    "TEXT4": "test text 4",
    "TEXT5": "test text 5",
    "TEXT6": "test text 6",
    "TEXT7": "test text 7",
    "TEXT8": "test text 8",
    "TEXT9": "test text 9",
}


class Dialogue:
    def __init__(self, root_id: str, name: str, nodes: tp.List[ExecuteNode]) -> None:
        self.name = name
        self.root_id = root_id
        self._nodes = {}
        for node in nodes:
            self._nodes[node.element_id] = node

    def get_init_root(self) -> ExecuteNode:
        return self._nodes[self.root_id]

    def get_node_by_id(self, node_id: str) -> ExecuteNode:
        try:
            return self._nodes[node_id]
        except KeyError:
            raise

    def __repr__(self) -> str:
        text = ""
        for k, v in self._nodes.items():
            if v.buttons is not None:
                buttons = []
                for b in v.buttons:
                    buttons.append((b[0], b[1]))
                text += f"{k}, {v.node_type}, {v.value}, {v.next_ids} {buttons}\n"
            else:
                text += f"{k}, {v.node_type}, {v.value}, {v.next_ids}\n"
        return text[:-1]
