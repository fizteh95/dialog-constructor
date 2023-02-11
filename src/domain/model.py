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
from jsonpath_ng import parse


@dataclass(kw_only=True)
class Event(ABC):
    """Message for bus"""

    to_process: bool = True


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


@dataclass(kw_only=True)
class InEvent(Event):  # noqa
    user: User
    project_name: str
    text: tp.Optional[str] = None
    button_pushed_next: tp.Optional[str] = None
    intent: tp.Optional[str] = None


@dataclass
class Button:
    text: str
    text_to_chat: str
    text_to_bot: str
    callback_data: tp.Optional[str]


@dataclass(kw_only=True)
class OutEvent(Event):  # noqa
    user: User
    text: str
    linked_node_id: str
    scenario_name: str
    project_name: tp.Optional[str] = None
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
    getVariable = "getVariable"
    passNode = "passNode"
    loopCounter = "loopCounter"
    ...


@dataclass
class ExecuteNode(ABC):
    """Base class for executor node classes"""

    element_id: str
    next_ids: tp.List[str] | None
    value: str
    node_type: NodeType
    buttons: tp.List[tp.Tuple[str, str, str, str]] | None = None
    procedural_source: tp.Optional[bool] = False

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
    ) -> tp.Dict[
        str, tp.Union[str, tp.List[str], tp.List[tp.Tuple[str, str, str, str]], None]
    ]:
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


class PassNode(ExecuteNode):
    async def execute(
        self, user: User, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[OutEvent], tp.Dict[str, str], str]:
        if in_text:
            return [], {}, in_text
        else:
            return [], {}, ""


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
        out_event = OutEvent(
            user=user,
            text=self.value,
            linked_node_id=self.element_id,
            scenario_name=user.current_scenario_name,
        )
        buttons_to_add = []
        procedural_buttons = []
        if self.buttons:
            buttons_to_add = [
                Button(
                    text=str(x[0]),
                    callback_data=str(x[1]),
                    text_to_bot=str(x[2]),
                    text_to_chat=str(x[3]),
                )
                for x in self.buttons
            ]
        if self.procedural_source and in_text:
            buttons_data = json.loads(in_text)
            if len(buttons_data) == 3:
                button_texts, to_bot_texts, to_chat_texts = buttons_data
                for t, b, c in zip(button_texts, to_bot_texts, to_chat_texts):
                    procedural_buttons.append(
                        Button(
                            text=str(t),
                            callback_data="",
                            text_to_bot=str(b),
                            text_to_chat=str(c),
                        )
                    )
        all_buttons: tp.List[Button] = procedural_buttons + buttons_to_add
        if all_buttons:
            out_event.buttons = all_buttons
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
            scenario_name=user.current_scenario_name,
        )
        if self.buttons:
            out_event.buttons = [
                Button(
                    text=x[0], callback_data=x[1], text_to_bot=x[2], text_to_chat=x[3]
                )
                for x in self.buttons
            ]
        return [out_event], {}, ""


class DataExtract(ExecuteNode):
    async def execute(
        self, user: User, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[OutEvent], tp.Dict[str, str], str]:
        """
        jsonpath_expr = parse("[*].['custom Name']")
        jsonpath_expr = parse('[*].balance.RUB')
        [match.value for match in jsonpath_expr.find(data)]
        => [1234, 346245]
        """
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
            try:
                jsonpath_expr = parse(self.value[5:-1])
                extracted = [
                    match.value for match in jsonpath_expr.find(json.loads(in_text))
                ]
                if len(extracted) > 0:
                    return [], {}, str(extracted[0])
            except Exception as e:
                print(e)
            return [], {}, ""
        elif extract_type == "jsonList":
            try:
                values_to_extract = self.value[9:-1].split("#")
                ret_val = []
                for v in values_to_extract:
                    jsonpath_expr = parse(v)
                    extracted = [
                        match.value for match in jsonpath_expr.find(json.loads(in_text))
                    ]
                    ret_val.append(extracted)
                return [], {}, json.dumps(ret_val)
            except Exception as e:
                print(e)
            return [], {}, ""
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
        elif self.value == "IF":
            if in_text:
                return [], {}, self.next_ids[0]
            else:
                return [], {}, self.next_ids[1]
        elif self.value == "OR":
            if in_text is None:
                raise ValueError("Logical unit AND must have string in input")
            in_results = in_text.split("###$###")  # должен быть список строк после
            for ir in in_results:
                if ir:
                    return [], {}, self.next_ids[0]
            return [], {}, self.next_ids[1]
        elif self.value == "AND":
            if in_text is None:
                raise ValueError("Logical unit AND must have string in input")
            in_results = in_text.split("###$###")  # должен быть список строк
            for ir in in_results:
                if not ir:
                    return [], {}, self.next_ids[1]
            return [], {}, self.next_ids[0]
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
            if (
                ("+" not in self.value)
                and ("-" not in self.value)
                and ("=" not in self.value)
            ):
                # установка в переменную того, что пришло из пайплайна
                return [], {var_name: in_text}, ""
            elif (
                ("+" not in self.value)
                and ("-" not in self.value)
                and ("=" in self.value)
            ):
                # установка конкретного значения
                value = self.value.split("=")[1]
                return [], {var_name: str(value)}, ""
            elif ("+=" in self.value) and ("-" not in self.value):
                # сумма со вторым числом либо строкой
                value = self.value.split("+=")[1]
                try:
                    new_value = int(ctx[var_name]) + int(value)
                except ValueError:
                    new_value = str(ctx[var_name]) + str(value)
                return [], {var_name: str(new_value)}, ""
            elif ("-=" in self.value) and ("+" not in self.value):
                # разница со вторым числом либо строкой
                value = self.value.split("-=")[1]
                try:
                    new_value = int(ctx[var_name]) - int(value)
                except ValueError:
                    new_value = str(ctx[var_name])[: -len(str(value))]
                return [], {var_name: str(new_value)}, ""
        else:
            raise NotImplementedError("Such variable type not implemented")


class GetVariable(ExecuteNode):
    async def execute(
        self, user: User, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[OutEvent], tp.Dict[str, str], str]:
        var_name = self.value.split("(")[1].split(")")[0]
        var_type = self.value.split("(")[0]
        if var_type == "user":
            res = ctx.get(var_name)
            if res is None:
                res = ""
            return [], {}, res
        else:
            raise NotImplementedError("Such variable type not implemented")


class LoopCounter(ExecuteNode):
    async def execute(
        self, user: User, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[OutEvent], tp.Dict[str, str], str]:
        if self.next_ids is None:
            raise Exception("Need two child for loop counter node")
        current_count = int(ctx.get(f"__{self.element_id}_count", 1))
        # value = self.value.split("(")[1].split(")")[0]
        if current_count > int(self.value):
            print("tp0")
            return [], {f"__{self.element_id}_count": str(current_count + 1)}, self.next_ids[1]
        else:
            print(f"tp1, {current_count}")
            return [], {f"__{self.element_id}_count": str(current_count + 1)}, self.next_ids[0]


class_dict = {
    "inIntent": InIntent,
    "matchText": MatchText,
    "inMessage": InMessage,
    "outMessage": OutMessage,
    "editMessage": EditMessage,
    "remoteRequest": RemoteRequest,
    "dataExtract": DataExtract,
    "setVariable": SetVariable,
    "getVariable": GetVariable,
    "logicalUnit": LogicalUnit,
    "passNode": PassNode,
    "loopCounter": LoopCounter,
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
        for n in self.nodes.values():
            if n.next_ids is None:
                continue
            if current_node.element_id in n.next_ids:
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
