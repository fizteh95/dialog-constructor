from __future__ import annotations
import xml.etree.cElementTree as et
import typing as tp
from abc import ABC, abstractmethod

from src.dialogues.domain import Button
from src.dialogues.domain import Dialogue
from src.dialogues.domain import DialogueNode
from src.dialogues.domain import NodeType


class Parser(ABC):
    def __init__(self) -> None:
        """
        Parser for dialogues
        """

    @abstractmethod
    def parse(self, input_stuff: tp.Any) -> tp.List[DialogueNode]:
        raise


class XMLParser(Parser):
    @staticmethod
    def _get_node_type(value: str) -> str:
        return value.split(":")[0]

    @staticmethod
    def _get_text_template(value: str) -> None | str:
        try:
            return value.split(":")[1]
        except IndexError:
            return None

    @staticmethod
    def _get_key_by_value(value: str, search_dict: tp.Dict[str, str]) -> str:
        for k, v in search_dict.items():
            if v == value:
                return k
        raise

    def parse(self, src_path: str) -> tp.Tuple[str, tp.List[DialogueNode]]:
        tree = et.parse(src_path)

        parent_id = "WIyWlLk6GJQsqaUBKTNV-1"
        nodes = tree.findall(f".//mxCell[@parent='{parent_id}']")
        result = {}
        arrows = {}
        for n in nodes:
            xml_value = n.get("value")
            if xml_value is None:
                source_id = n.get("source")
                target_id = n.get("target")
                arrows[source_id] = target_id
        for n in nodes:
            xml_value = n.get("value")
            if xml_value is not None and xml_value != "btnArray":
                node_type = NodeType(self._get_node_type(xml_value))
                value = self._get_text_template(xml_value)
                dialogue_node = DialogueNode(element_id=n.get("id"), node_type=node_type, value=value)
                dialogue_node.add_next(arrows.get(dialogue_node.id))
                result[dialogue_node.id] = dialogue_node
        for n in nodes:
            xml_value = n.get("value")
            if xml_value == "btnArray":
                array_id = n.get("id")
                xml_buttons = tree.findall(f".//mxCell[@parent='{array_id}']")
                buttons = []
                for b in xml_buttons:
                    text = b.get("value")
                    button_id = b.get("id")
                    next_node_id = arrows[button_id]
                    button = Button(button_text=text, next_node_id=next_node_id)
                    buttons.append(button)
                source_id = self._get_key_by_value(array_id, arrows)
                result[source_id].buttons = buttons
                result[source_id].next_node_id = None
        root_id = list(result.keys())[0].split("-")[0] + "-" + str(min([int(x.split("-")[-1]) for x in result.keys()]))
        return root_id, list(result.values())


def main() -> None:
    xml_src_path = "/src/resources/dialogue-schema-test.xml"
    parser = XMLParser()
    root_id, nodes = parser.parse(src_path=xml_src_path)
    dialogue = Dialogue(root_id=root_id, nodes=nodes)
    print(root_id)
    print(dialogue)


if __name__ == "__main__":
    main()
