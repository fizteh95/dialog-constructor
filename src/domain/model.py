import re
import typing as tp
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum


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


@dataclass
class Button:
    text: str
    callback_data: tp.Optional[str]


@dataclass
class OutEvent(Event):
    user: User
    text: str
    buttons: tp.Optional[tp.List[Button]] = None
    node_to_edit: tp.Optional[str] = None
    ...


class NodeType(Enum):
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
    ) -> tp.Tuple[tp.List[Event], tp.Dict[str, str], str]:
        """
        Исполнение ноды, берет входные данные, отдает событие и текст для дальнейшего пайплайна
        :param user: юзер для создания исходящего события
        :param ctx: контекст исполнения, все переменные юзера и глобальные (для этого сценария)
        :param in_text: текст с предыдущего шага пайплайна
        :return: тапл из списков исходящих событий, обновления контекста и текст для дальнейшей обработки
        """


class InMessage(ExecuteNode):
    async def execute(
        self, user: User, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[Event], tp.Dict[str, str], str]:
        if in_text:
            return [], {}, in_text
        else:
            return [], {}, ""


class OutMessage(ExecuteNode):
    async def execute(
        self, user: User, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[Event], tp.Dict[str, str], str]:
        out_event = OutEvent(user=user, text=self.value)
        if self.buttons:
            out_event.buttons = [
                Button(text=x[0], callback_data=x[1]) for x in self.buttons
            ]
        return [out_event], {}, ""


class EditMessage(ExecuteNode):
    async def execute(
        self, user: User, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[Event], tp.Dict[str, str], str]:
        ...
        return [], {}, ""


class DataExtract(ExecuteNode):
    async def execute(
        self, user: User, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[Event], tp.Dict[str, str], str]:
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
            ...
        else:
            raise NotImplementedError("Such data extract type not implemented")
        return [], {}, ""


class LogicalUnit(ExecuteNode):
    async def execute(
        self, user: User, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[Event], tp.Dict[str, str], str]:
        if self.value == "NOT":
            if in_text:
                return [], {}, ""
            else:
                return [], {}, "Logical unit NOT was passed"
        else:
            raise NotImplementedError("Logical unit with such type not implemented")


class RemoteRequest(ExecuteNode):
    async def execute(
        self, user: User, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[Event], tp.Dict[str, str], str]:
        ...
        return [], {}, ""


class SetVariable(ExecuteNode):
    async def execute(
        self, user: User, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[Event], tp.Dict[str, str], str]:
        var_name = self.value.split("(")[1].split(")")[0]
        if in_text is None:
            in_text = ""
        var_type = self.value.split("(")[0]
        if var_type == "user":
            return [], {var_name: in_text}, ""
        else:
            raise NotImplementedError("Such variable type not implemented")


@dataclass
class Scenario:
    name: str
    root_id: str
    nodes: tp.Dict[str, ExecuteNode]

    def get_node_by_id(self, node_id: str) -> ExecuteNode:
        return self.nodes[node_id]
