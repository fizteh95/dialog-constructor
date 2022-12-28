from __future__ import annotations
import xml.etree.cElementTree as et
from enum import Enum
import typing as tp
from abc import ABC, abstractmethod
from xml.etree import ElementTree

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
    def __init__(self, element_id: str, node_type: NodeType, value: str | None, buttons: None | tp.List[Button] = None) -> None:
        self.id = element_id
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

    def _convert_to_dialogue_node(self, xml_value: str, xml_id: str) -> DialogueNode:
        node_type = NodeType(self._get_node_type(xml_value))

        text_template = None
        if node_type == NodeType.outMessage:
            text_template = self._get_text_template(xml_value)
        elif node_type == NodeType.inMessage:
            ...
        elif node_type == NodeType.editMessage:
            ...
        else:
            raise
        node = DialogueNode(element_id=xml_id, node_type=node_type, value=text_template)
        return node

    def _get_child_over_arrow(self, tree: ElementTree, source_id: str) -> tp.List[DialogueNode]:
        arrows = tree.findall(f".//mxCell[@source='{source_id}']")  # все стрелки
        childs = []
        for arrow in arrows:
            next_step = tree.findall(f".//mxCell[@id='{arrow.get('target')}']")[0]
            xml_value = next_step.get("value")
            xml_id = next_step.get("id")
            node = self._convert_to_dialogue_node(xml_value, xml_id)
            childs.append(node)
        return childs

    def parse(self, src_path: str) -> tp.List[DialogueNode]:
        result = []
        tree = et.parse(src_path)
        root_id = "0OOwWBntzJv1pY5lexbC-0"
        dialogue_root = tree.findall(f".//mxCell[@id='{root_id}']")[0]

        xml_value = dialogue_root.get("value")
        root = self._convert_to_dialogue_node(xml_value, root_id)
        result.append(root)
        childs = self._get_child_over_arrow(tree, root_id)
        new_childs = [c for c in childs if c not in result]
        result += new_childs


def main() -> None:
    print("ha")

    result = []
    tree = et.parse(xml_src_path)
    root_id = "0OOwWBntzJv1pY5lexbC-0"
    dialogue_root = tree.findall(f".//mxCell[@id='{root_id}']")[0]
    xml_value = dialogue_root.get("value")
    xml_id = dialogue_root.get("id")

    result.append((xml_value, xml_id))

    arrows = tree.findall(f".//mxCell[@source='{root_id}']")  # все стрелки
    childs = []
    for arrow in arrows:
        next_step = tree.findall(f".//mxCell[@id='{arrow.get('target')}']")[0]
        xml_value = next_step.get("value")
        xml_id = next_step.get("id")
        childs.append((xml_value, xml_id))

    new_childs = [c for c in childs if c not in result]
    result += new_childs

    for child in new_childs:
        arrows = tree.findall(f".//mxCell[@source='{child[1]}']")  # все стрелки
        childs = []
        for arrow in arrows:
            next_step = tree.findall(f".//mxCell[@id='{arrow.get('target')}']")[0]
            xml_value = next_step.get("value")
            xml_id = next_step.get("id")
            childs.append((xml_value, xml_id))

    new_childs = [c for c in childs if c not in result]
    result += new_childs

    for child in new_childs:
        arrows = tree.findall(f".//mxCell[@source='{child[1]}']")  # все стрелки
        childs = []
        for arrow in arrows:
            next_step = tree.findall(f".//mxCell[@id='{arrow.get('target')}']")[0]
            xml_value = next_step.get("value")
            xml_id = next_step.get("id")
            if xml_value == "btnArray":
                buttons = []
                xml_buttons = tree.findall(f".//mxCell[@parent='{xml_id}']")
                for xml_b in xml_buttons:
                    xml_button_value = xml_b.get("value")
                    xml_button_id = xml_b.get("id")
                    buttons.append((xml_button_value, xml_button_id))
                childs.append((xml_value, xml_id, buttons))
            else:
                childs.append((xml_value, xml_id))

    new_childs = [c for c in childs if c not in result]
    result += new_childs

    #######
    for r in result:
        print(r)


if __name__ == "__main__":
    main()
