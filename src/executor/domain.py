import typing as tp
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum

# from src.dialogues.domain import DialogueNode
from src.message_bus.domain import MessageBus
from src.message_bus.domain import Subscriber
from src.repository.repository import AbstractRepo
from src.users.domain import User

# from src.users.domain import User


class Event(ABC):
    """Message for bus"""


@dataclass
class InEvent(Event):
    user: User
    text: tp.Optional[str] = None
    button_pushed: tp.Optional[str] = None


@dataclass
class Button:
    text: str
    callback_data: tp.Optional[str]


@dataclass
class OutEvent(Event):
    user: User
    text: str
    buttons: tp.Optional[tp.List[Button]]
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


class ExecuteNode(ABC):
    """Base class for executor node classes"""

    def __init__(
        self,
        element_id: str,
        next_ids: tp.List[str] | None,
        value: str,
        node_type: NodeType,
        buttons: tp.List[tp.Tuple[str, str]] | None = None,
    ):
        self.element_id = element_id
        self.next_ids = next_ids
        self.value = value
        self.node_type = node_type
        self.buttons = buttons

    @abstractmethod
    async def execute(self):
        ...


class InMessage(ExecuteNode):
    ...


class OutMessage(ExecuteNode):
    ...


class DataExtract(ExecuteNode):
    ...


class Executor(ABC, Subscriber):
    def __init__(self, repo: AbstractRepo, bus: MessageBus) -> None:
        """Initialize of executor"""
        self.repo = repo
        self.bus = bus

    @abstractmethod
    async def execute_dialogue(self, event: InEvent) -> None:
        """Execute dialogue method"""


class ConcreteExecutor(Executor):
    def __init__(self, repo: AbstractRepo, bus: MessageBus) -> None:
        """Initialize of executor"""
        super().__init__(repo, bus)

    @abstractmethod
    async def execute_dialogue(self, event: InEvent) -> None:
        """Execute dialogue method"""
        ...

    async def handle_message(self, message: Event) -> None:
        """Handle message from bus"""
        if isinstance(message, InEvent):
            await self.execute_dialogue(message)


# class ConcreteExecutorOld(Executor):
#     def __init__(self, repo: AbstractRepo, bus: MessageBus) -> None:
#         """Initialize of executor"""
#         super().__init__(repo, bus)
#
#     async def handle_message(self, message: Event) -> None:
#         """Handle message from bus"""
#         if isinstance(message, InEvent):
#             await self.execute_dialogue(message)
#
#     def translate_node_to_event(self, user: User, node: DialogueNode) -> OutEvent:
#         if node.node_type == NodeType.inMessage:
#             raise
#         elif node.node_type == NodeType.outMessage:
#             if node.buttons is not None:
#                 buttons: None | tp.List[Button] = []
#                 for b in node.buttons:
#                     buttons.append(
#                         Button(text=b.text, callback_data=f"{b.next_node_id}")
#                     )
#             else:
#                 buttons = None
#             out_event = OutEvent(user=user, text=node.value, buttons=buttons)
#             return out_event
#         else:
#             raise NotImplementedError
#
#     async def execute_dialogue(self, event: InEvent) -> None:
#         """Execute dialogue method"""
#
#         user = await self.repo.get_user(event.user.outer_id)
#
#         if user.current_scenario_id is None:
#             print("current scenario is None")
#             init_scenario_name = "Test scenario"
#             await self.repo.set_user_current_scenario(user, init_scenario_name)
#
#             current_scenario = await self.repo.get_dialogue(init_scenario_name)
#             current_node = current_scenario.get_init_root()
#         else:
#             print(f"current scenario is {user.current_scenario_id}")
#             current_scenario = await self.repo.get_dialogue(user.current_scenario_id)
#             user_current_node = user.current_node_id
#             if user_current_node is None:
#                 current_node = current_scenario.get_init_root()
#             else:
#                 current_node = current_scenario.get_node_by_id(user.current_node_id)  # type: ignore
#
#         print(f"current node is {current_node.id}")
#         new_events: tp.List[OutEvent] = []
#         next_node = current_scenario.get_next_node(current_node)
#         if (
#             (next_node is None)
#             and (current_node.node_type == NodeType.outMessage)
#             and (current_node.buttons is not None)
#         ):
#             print("tp0")
#             if event.button_pushed is None:
#                 print("tp1")
#                 # очищаем текущий сценарий и текущую ноду пользователя
#                 await self.repo.set_user_current_scenario(user, None)
#                 await self.repo.set_user_current_node(user, None)
#             else:
#                 print("tp2")
#                 next_node = current_scenario.get_node_by_id(event.button_pushed)
#                 # нашли следующую ноду
#                 if next_node.node_type == NodeType.inMessage:
#                     print("tp3")
#                     await self.repo.set_user_current_node(user, next_node.id)
#                     return
#                 else:
#                     print("tp4")
#                     if next_node.node_type == NodeType.outMessage:
#                         print("tp5")
#                         new_event = self.translate_node_to_event(user, next_node)
#                         new_events.append(new_event)
#                         next_next_node = current_scenario.get_next_node(next_node)
#                         if next_next_node is None:
#                             # очищаем текущий сценарий и текущую ноду пользователя
#                             await self.repo.set_user_current_scenario(user, None)
#                             await self.repo.set_user_current_node(user, None)
#                         elif next_next_node.node_type == NodeType.inMessage:
#                             await self.repo.set_user_current_node(
#                                 user, next_next_node.id
#                             )
#                         elif next_next_node.node_type == NodeType.outMessage:
#                             new_event = self.translate_node_to_event(
#                                 user, next_next_node
#                             )
#                             new_events.append(new_event)
#                             next_next_next_node = current_scenario.get_next_node(
#                                 next_next_node
#                             )
#                             if next_next_next_node is None:
#                                 # очищаем текущий сценарий и текущую ноду пользователя
#                                 await self.repo.set_user_current_scenario(user, None)
#                                 await self.repo.set_user_current_node(user, None)
#                             elif next_next_next_node.node_type == NodeType.inMessage:
#                                 await self.repo.set_user_current_node(
#                                     user, next_next_next_node.id
#                                 )
#                             elif next_next_node.node_type == NodeType.outMessage:
#                                 ...
#                     else:
#                         raise NotImplementedError
#         elif next_node is None:
#             print("tp6")
#             # очищаем текущий сценарий и текущую ноду пользователя
#             await self.repo.set_user_current_scenario(user, None)
#             await self.repo.set_user_current_node(user, None)
#         elif next_node is not None:
#             print("tp7")
#             # нашли следующую ноду
#             if next_node.node_type == NodeType.inMessage:
#                 print("tp8")
#                 await self.repo.set_user_current_node(user, next_node.id)
#                 return
#             else:
#                 print("tp9")
#                 if next_node.node_type == NodeType.outMessage:
#                     print("tp10")
#                     new_event = self.translate_node_to_event(user, next_node)
#                     new_events.append(new_event)
#                     next_next_node = current_scenario.get_next_node(next_node)
#                     if next_next_node is None and next_node.buttons is not None:
#                         print("tp11")
#                         await self.repo.set_user_current_node(user, next_node.id)
#                     elif next_next_node is None:
#                         print("tp12")
#                         # очищаем текущий сценарий и текущую ноду пользователя
#                         await self.repo.set_user_current_scenario(user, None)
#                         await self.repo.set_user_current_node(user, None)
#                     elif next_next_node.node_type == NodeType.inMessage:
#                         print("tp13")
#                         await self.repo.set_user_current_node(user, next_next_node.id)
#                     elif next_next_node.node_type == NodeType.outMessage:
#                         print("tp14")
#                         new_event = self.translate_node_to_event(user, next_next_node)
#                         new_events.append(new_event)
#                         next_next_next_node = current_scenario.get_next_node(
#                             next_next_node
#                         )
#                         if (
#                             next_next_next_node is None
#                             and next_next_node.buttons is not None
#                         ):
#                             print("tp14_1")
#                             await self.repo.set_user_current_node(
#                                 user, next_next_node.id
#                             )
#                         elif next_next_next_node is None:
#                             print("tp15")
#                             # очищаем текущий сценарий и текущую ноду пользователя
#                             await self.repo.set_user_current_scenario(user, None)
#                             await self.repo.set_user_current_node(user, None)
#                         elif next_next_next_node.node_type == NodeType.inMessage:
#                             print("tp16")
#                             await self.repo.set_user_current_node(
#                                 user, next_next_next_node.id
#                             )
#                         elif next_next_node.node_type == NodeType.outMessage:
#                             ...
#                 else:
#                     raise NotImplementedError
#         else:
#             raise
#
#         print(new_events)
#         await self.bus.public_message(new_events)
