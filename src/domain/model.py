import typing as tp
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum


class Event(ABC):
    """Message for bus"""


@dataclass
class User:
    outer_id: int
    nickname: None | str = None
    name: None | str = None
    surname: None | str = None
    patronymic: None | str = None
    current_scenario_name: None | str = None
    current_node_id: None | str = None


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
        self, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[Event], str]:
        """
        Исполнение ноды, берет входные данные, отдает событие и текст для дальнейшего пайплайна
        :param ctx: контекст исполнения, все переменные юзера и глобальные (для этого сценария)
        :param in_text: текст с предыдущего шага пайплайна
        :return: тапл из списков исходящих событий и текст для дальнейшей обработки
        """


class InMessage(ExecuteNode):
    async def execute(
        self, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[Event], str]:
        ...
        return [], ""


class OutMessage(ExecuteNode):
    async def execute(
        self, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[Event], str]:
        ...
        return [], ""


class EditMessage(ExecuteNode):
    async def execute(
        self, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[Event], str]:
        ...
        return [], ""


class DataExtract(ExecuteNode):
    async def execute(
        self, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[Event], str]:
        ...
        return [], ""


class LogicalUnit(ExecuteNode):
    async def execute(
        self, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[Event], str]:
        ...
        return [], ""


class RemoteRequest(ExecuteNode):
    async def execute(
        self, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[Event], str]:
        ...
        return [], ""


class SetVariable(ExecuteNode):
    async def execute(
        self, ctx: tp.Dict[str, str], in_text: str | None = None
    ) -> tp.Tuple[tp.List[Event], str]:
        ...
        return [], ""


@dataclass
class Scenario:
    name: str
    root_id: str
    nodes: tp.Dict[str, ExecuteNode]

    def get_node_by_id(self, node_id: str) -> ExecuteNode:
        return self.nodes[node_id]
