from __future__ import annotations

import typing as tp
import xml.etree.cElementTree as et
from abc import ABC
from abc import abstractmethod
from collections import defaultdict

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
    def parse(self, input_stuff: tp.Any) -> tp.Tuple[str, tp.List[DialogueNode]]:
        raise


class XMLParser(Parser):
    @staticmethod
    def _get_node_type(value: str) -> str:
        return value.split(":")[0]

    @staticmethod
    def _get_template(value: str) -> None | str:
        try:
            return "".join(value.split(":")[1:])
        except IndexError:
            return None

    @staticmethod
    def _get_key_by_value(value: str, search_dict: tp.Dict[str, tp.List[str]]) -> str:
        for k, v in search_dict.items():
            if value in v:
                return k
        raise

    def parse(self, src_path: str) -> tp.Tuple[str, tp.List[DialogueNode]]:
        tree = et.parse(src_path)

        parent_id = "WIyWlLk6GJQsqaUBKTNV-1"
        nodes = tree.findall(f".//mxCell[@parent='{parent_id}']")
        result = {}
        arrows: tp.Dict[str, tp.List[str]] = defaultdict(list)
        # поиск всех стрелок
        for n in nodes:
            xml_value = n.get("value")
            if not xml_value:
                source_id = n.get("source")
                target_id = n.get("target")
                if source_id and target_id:
                    arrows[source_id].append(target_id)
        for k, v in arrows.items():
            print(f"{k} -> {v}")
        # raise
        # поиск всех блоков нод (кроме btnArray)
        for n in nodes:
            xml_value = n.get("value")
            if xml_value and xml_value != "btnArray":
                try:
                    node_type = NodeType(self._get_node_type(xml_value))
                except ValueError:
                    # todo: сделать грамотную обработку если это заметка
                    print(f"unknown NodeType, {xml_value}")
                    continue
                node_value = self._get_template(xml_value)
                element_id = n.get("id")
                if not element_id:
                    print("node has no element id")
                    continue
                dialogue_node = DialogueNode(
                    element_id=element_id, node_type=node_type, value=node_value
                )
                next_nodes = arrows.get(dialogue_node.id)
                dialogue_node.add_next(next_nodes)
                result[dialogue_node.id] = dialogue_node
        # присоединение кнопок к целевым блокам
        for n in nodes:
            xml_value = n.get("value")
            if xml_value == "btnArray":
                array_id = n.get("id")
                if not array_id:
                    print("button array has no id")
                    continue
                xml_buttons = tree.findall(f".//mxCell[@parent='{array_id}']")
                buttons = []
                for b in xml_buttons:
                    text = b.get("value")
                    if not text:
                        print("button has no text")
                        raise
                    button_id = b.get("id")
                    if not button_id:
                        print("has no reference in button")
                        continue
                    next_node_ids = arrows.get(button_id)
                    if not next_node_ids:
                        print("button must have any child")
                        raise
                    button = Button(button_text=text, next_node_ids=next_node_ids)
                    buttons.append(button)
                source_id = self._get_key_by_value(array_id, arrows)
                result[source_id].buttons = buttons
                result[source_id].next_node_ids = None
        root_id = result[list(result.keys())[0]].id
        return root_id, list(result.values())


def main() -> None:
    xml_src_path = "../../src/resources/weather-demo.xml"
    parser = XMLParser()
    root_id, nodes = parser.parse(src_path=xml_src_path)
    dialogue = Dialogue(root_id=root_id, name="Test scenario", nodes=nodes)
    print(root_id)
    print(dialogue)


if __name__ == "__main__":
    main()
