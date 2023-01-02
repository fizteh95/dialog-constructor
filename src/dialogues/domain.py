import typing as tp
from enum import Enum

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


class NodeType(Enum):
    inMessage = "inMessage"
    outMessage = "outMessage"
    editMessage = "editMessage"
    ...


class Button:
    def __init__(self, button_text: str, next_node_id: str) -> None:
        self._text = button_text
        self.next_node_id = next_node_id

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
        self.next_node_id: None | str = None
        self.buttons = buttons

    def add_next(self, node_id: str) -> None:
        self.next_node_id = node_id

    @property
    def value(self) -> str:
        return texts.get(self._value, "text not found")


class Dialogue:
    def __init__(self, root_id: str, nodes: tp.List[DialogueNode]) -> None:
        self.root_id = root_id
        self._nodes = {}
        for node in nodes:
            self._nodes[node.id] = node

    def get_init_root(self) -> DialogueNode:
        return self._nodes[self.root_id]

    def get_next_node(self, current_node: DialogueNode) -> DialogueNode:
        next_node_id = current_node.next_node_id
        return self._nodes[next_node_id]

    def __repr__(self):
        text = ""
        for k, v in self._nodes.items():
            if v.buttons is not None:
                buttons = []
                for b in v.buttons:
                    buttons.append((b.text, b.next_node_id))
                text += f"{k}, {v.node_type}, {v.value}, {v.next_node_id} {buttons}\n"
            else:
                text += f"{k}, {v.node_type}, {v.value}, {v.next_node_id}\n"
        return text
