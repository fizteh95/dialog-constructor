import typing as tp
from enum import Enum

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


class Button:
    def __init__(self, button_text: str, next_node_ids: tp.List[str]) -> None:
        self._text = button_text
        self.next_node_ids = next_node_ids

    @property
    def text(self) -> str:
        return texts.get(self._text, "text not found")


class DialogueNode:
    def __init__(
        self,
        element_id: str,
        node_type: NodeType,
        value: str | None,
        buttons: None | tp.List[Button] = None,
    ) -> None:
        self.id = element_id
        self.node_type = node_type
        self._value = value
        self.next_node_ids: None | tp.List[str] = None
        self.buttons = buttons

    def add_next(self, node_ids: tp.List[str] | None) -> None:
        self.next_node_ids = node_ids

    # @property
    # def value(self) -> str:
    #     if self._value is None:
    #         return "text not found"
    #     return texts.get(self._value, "text not found")


class Dialogue:
    def __init__(self, root_id: str, name: str, nodes: tp.List[DialogueNode]) -> None:
        self.name = name
        self.root_id = root_id
        self._nodes = {}
        for node in nodes:
            self._nodes[node.id] = node

    def get_init_root(self) -> DialogueNode:
        return self._nodes[self.root_id]

    def get_next_node(self, current_node: DialogueNode) -> tp.Optional[DialogueNode]:
        next_node_ids = current_node.next_node_ids
        if next_node_ids is None:
            return None
        return self._nodes[next_node_id]

    def get_node_by_id(self, node_id: str) -> DialogueNode:
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
                    buttons.append((b.text, b.next_node_ids))
                text += f"{k}, {v.node_type}, {v._value}, {v.next_node_ids} {buttons}\n"
            else:
                text += f"{k}, {v.node_type}, {v._value}, {v.next_node_ids}\n"
        return text[:-1]
