from __future__ import annotations
import xml.etree.cElementTree as et
from enum import Enum
import typing as tp
from abc import ABC, abstractmethod
import uuid


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
    btnArray = "btnArray"
    ...


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


class Button:
    def __init__(self, button_text: str, next_node: DialogueNode) -> None:
        self._text = button_text
        self.next_node = next_node

    @property
    def text(self) -> str:
        return texts.get(self._text, "text not found")


class DialogueNode:
    def __init__(self, node_type: NodeType, value: str | None, buttons: None | tp.List[Button] = None) -> None:
        self.id = uuid.uuid4()
        self.node_type = node_type
        self._value = value
        self.next_node_id: None | str = None
        self._buttons = buttons

    def add_next(self, node_id: str) -> None:
        self.next_node_id = node_id

    @property
    def value(self) -> str:
        return texts.get(self._value, "text not found")


class Parser(ABC):
    def __init__(self) -> None:
        """
        Parser for dialogues
        """

    @abstractmethod
    def parse(self, input_stuff: tp.Any) -> tp.List[DialogueNode]:
        raise


xml_src_path = "/home/dmitriy/PycharmProjects/dialogue-constructor/src/resources/dialogue-schema-test.xml"


class XMLParser(Parser):
    @staticmethod
    def _get_node_type(value: str) -> str:
        return value.split(":")[0]

    @staticmethod
    def _get_text_template(value: str) -> str:
        try:
            return value.split(":")[1]
        except IndexError:
            return "not found template"

    # @staticmethod
    # def _get_child_over_arrow

    def parse(self, src_path: str) -> tp.List[DialogueNode]:
        tree = et.parse(src_path)
        dialogue_root = tree.findall(".//mxCell[@id='0OOwWBntzJv1pY5lexbC-0']")[0]

        xml_value = dialogue_root.get("value")
        node_type = NodeType(self._get_node_type(xml_value))
        if node_type == NodeType.outMessage:
            text_template = self._get_text_template(xml_value)
        else:
            text_template = None
        root = DialogueNode(node_type=node_type, value=text_template)

        arrow = tree.findall(f".//mxCell[@source='0OOwWBntzJv1pY5lexbC-0']")[0]
        next_step = tree.findall(f".//mxCell[@id='{arrow.get('target')}']")[0]
        print(next_step.get("value"))
