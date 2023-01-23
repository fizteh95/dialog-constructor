from __future__ import annotations

import json
import re
import typing as tp
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum

import aiohttp
import curlparser


class Event(ABC):
    """Message for bus"""


@dataclass
class User:
    outer_id: str
    nickname: None | str = None
    name: None | str = None
    surname: None | str = None
    patronymic: None | str = None
    current_scenario_name: None | str = None
    current_node_id: None | str = None

    async def update_current_node_id(self, node_id: str | None) -> None:
        self.current_node_id = node_id

    async def update_current_scenario_name(self, name: str | None) -> None:
        self.current_scenario_name = name


@dataclass
class InEvent(Event):
    user: User
    text: tp.Optional[str] = None
    button_pushed_next: tp.Optional[str] = None
    intent: tp.Optional[str] = None


@dataclass
class Button:
    text: str
    callback_data: tp.Optional[str]


@dataclass
class OutEvent(Event):
    user: User
    text: str
    linked_node_id: str
    buttons: tp.Optional[tp.List[Button]] = None
    node_to_edit: tp.Optional[str] = None
    ...


class NodeType(Enum):
    inIntent = "inIntent"
    matchText = "matchText"
    inMessage = "inMessage"
    outMessage = "outMessage"
    editMessage = "editMessage"
    dataExtract = "dataExtract"
    logicalUnit = "logicalUnit"
    remoteRequest = "remoteRequest"
    setVariable = "setVariable"
    ...


@dataclass
class ExecuteNode(ABC):
    """Base class for executor node classes"""

    element_id: str
    next_ids: tp.List[str] | None
    value: str
    node_type: NodeType
    buttons: tp.List[tp.Tuple[str, str]] | None = None

    @abstractmethod
    async def execute(
        self, user: User, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[OutEvent], tp.Dict[str, str], str]:
        """
        Исполнение ноды, берет входные данные, отдает событие и текст для дальнейшего пайплайна
        :param user: юзер для создания исходящего события
        :param ctx: контекст исполнения, все переменные юзера и глобальные (для этого сценария)
        :param in_text: текст с предыдущего шага пайплайна
        :return: тапл из списков исходящих событий, обновления контекста и текст для дальнейшей обработки
        """

    def to_dict(
        self,
    ) -> tp.Dict[str, tp.Union[str, tp.List[str], tp.List[tp.Tuple[str, str]], None]]:
        return dict(
            element_id=self.element_id,
            next_ids=self.next_ids,
            value=self.value,
            node_type=self.node_type.value,
            buttons=self.buttons,
        )

    @classmethod
    def from_dict(cls, kwargs_dict: tp.Dict[str, tp.Any]) -> ExecuteNode:
        """Create node from json"""
        return cls(
            element_id=kwargs_dict["element_id"],
            next_ids=kwargs_dict["next_ids"],
            value=kwargs_dict["value"],
            node_type=NodeType(kwargs_dict["node_type"]),
            buttons=[tuple(x) for x in kwargs_dict["buttons"]] if kwargs_dict["buttons"] is not None else None,  # type: ignore
        )


class InIntent(ExecuteNode):
    async def execute(
        self, user: User, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[OutEvent], tp.Dict[str, str], str]:
        if in_text:
            return [], {}, in_text
        else:
            return [], {}, ""


class MatchText(ExecuteNode):
    async def execute(
        self, user: User, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[OutEvent], tp.Dict[str, str], str]:
        if in_text:
            pattern = re.compile(rf"{self.value}")
            res = pattern.match(in_text)
            if res is None:
                return [], {}, ""
            return [], {}, in_text[res.start() : res.end()]
        else:
            return [], {}, ""


class InMessage(ExecuteNode):
    async def execute(
        self, user: User, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[OutEvent], tp.Dict[str, str], str]:
        if in_text:
            return [], {}, in_text
        else:
            return [], {}, ""


class OutMessage(ExecuteNode):
    async def execute(
        self, user: User, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[OutEvent], tp.Dict[str, str], str]:
        out_event = OutEvent(user=user, text=self.value, linked_node_id=self.element_id)
        if self.buttons:
            out_event.buttons = [
                Button(text=x[0], callback_data=x[1]) for x in self.buttons
            ]
        return [out_event], {}, ""


class EditMessage(ExecuteNode):
    async def execute(
        self, user: User, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[OutEvent], tp.Dict[str, str], str]:
        if self.next_ids is None:
            raise Exception("EditMessage node need next_ids field")
        out_event = OutEvent(
            user=user,
            text=self.value,
            node_to_edit=self.next_ids[0],  # [0]
            linked_node_id=self.element_id,
        )
        if self.buttons:
            out_event.buttons = [
                Button(text=x[0], callback_data=x[1]) for x in self.buttons
            ]
        return [out_event], {}, ""


class DataExtract(ExecuteNode):
    async def execute(
        self, user: User, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[OutEvent], tp.Dict[str, str], str]:
        if in_text is None:
            raise Exception("No input in extracting node")
        extract_type = self.value.split("(")[0]
        if extract_type == "re":
            pattern = re.compile(rf"{self.value[3:-1]}")
            res = pattern.match(in_text)
            if res is None:
                return [], {}, ""
            return [], {}, in_text[res.start() : res.end()]
        elif extract_type == "json":
            input_json = json.loads(in_text)  # noqa
            search_path = self.value[5:-1]
            return [], {}, eval(f"input_json{search_path}")
        else:
            raise NotImplementedError("Such data extract type not implemented")


class LogicalUnit(ExecuteNode):
    async def execute(
        self, user: User, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[OutEvent], tp.Dict[str, str], str]:
        if self.next_ids is None:
            raise ValueError("Logical unit must have only two child")
        if len(self.next_ids) != 2:
            raise ValueError("Logical unit must have only two child")
        if self.value == "NOT":
            if in_text:
                return [], {}, self.next_ids[1]
            else:
                return [], {}, self.next_ids[0]
        elif self.value == "OR":
            # TODO: create logic
            return [], {}, "tratata"
        else:
            raise NotImplementedError("Logical unit with such type not implemented")


class RemoteRequest(ExecuteNode):
    async def execute(
        self, user: User, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[OutEvent], tp.Dict[str, str], str]:
        curl_str = self.value[1:-1]
        parsed_curl = curlparser.parse(curl_str)
        request_url = parsed_curl.url
        for k, v in ctx.items():
            request_url = request_url.replace(f"#{k}#", str(v))
        if parsed_curl.method == "GET":
            async with aiohttp.ClientSession() as session:
                async with session.get(request_url) as resp:
                    res = await resp.text()
        elif parsed_curl.method == "POST":
            async with aiohttp.ClientSession() as session:
                async with session.post(request_url, json=parsed_curl.json) as resp:
                    res = await resp.text()
        else:
            raise NotImplementedError(f"{parsed_curl.method} method not implemented")
        return [], {}, res


class SetVariable(ExecuteNode):
    async def execute(
        self, user: User, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[OutEvent], tp.Dict[str, str], str]:
        var_name = self.value.split("(")[1].split(")")[0]
        if in_text is None:
            in_text = ""
        var_type = self.value.split("(")[0]
        if var_type == "user":
            return [], {var_name: in_text}, ""
        else:
            raise NotImplementedError("Such variable type not implemented")


class_dict = {
    "inIntent": InIntent,
    "matchText": MatchText,
    "inMessage": InMessage,
    "outMessage": OutMessage,
    "editMessage": EditMessage,
    "remoteRequest": RemoteRequest,
    "dataExtract": DataExtract,
    "setVariable": SetVariable,
    "logicalUnit": LogicalUnit,
}


@dataclass
class Scenario:
    name: str
    root_id: str
    nodes: tp.Dict[str, ExecuteNode]
    intent_names: tp.List[str] | None = None
    match_strings: tp.List[str] | None = None

    def get_node_by_id(self, node_id: str) -> ExecuteNode:
        return self.nodes[node_id]

    def get_nodes_by_type(self, node_type: NodeType) -> tp.List[ExecuteNode]:
        res: tp.List[ExecuteNode] = []
        for n in self.nodes.values():
            if n.node_type == node_type:
                res.append(n)
        return res

    def get_parents_of_node(self, node_id: str) -> tp.List[ExecuteNode]:
        res: tp.List[ExecuteNode] = []
        current_node = self.get_node_by_id(node_id=node_id)
        if current_node.next_ids is None:
            return []
        for n in self.nodes.values():
            if n.element_id in current_node.next_ids:
                res.append(n)
        return res

    def to_dict(
        self,
    ) -> tp.Dict[
        str, tp.Union[None, str, tp.List[str], tp.Dict[str, tp.Any]]
    ]:  # TODO: right typing
        return dict(
            name=self.name,
            root_id=self.root_id,
            nodes={k: v.to_dict() for k, v in self.nodes.items()},
            intent_names=self.intent_names,
            match_strings=self.match_strings,
        )

    @classmethod
    def from_dict(cls, kwargs_dict: tp.Dict[str, tp.Any]) -> Scenario:
        nodes: tp.Dict[str, ExecuteNode] = {}
        for k, v in kwargs_dict["nodes"].items():
            need_class = class_dict[v["node_type"]]
            dialogue_node = need_class.from_dict(v)
            nodes[k] = dialogue_node
        return cls(
            name=kwargs_dict["name"],
            root_id=kwargs_dict["root_id"],
            nodes=nodes,
            intent_names=kwargs_dict["intent_names"],
            match_strings=kwargs_dict["match_strings"],
        )
