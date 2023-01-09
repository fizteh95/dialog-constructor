import asyncio
import copy
import typing as tp
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass

import aiogram

from src.dialogues.domain import Dialogue
from src.dialogues.domain import DialogueNode
from src.dialogues.domain import NodeType


class Event(ABC):
    """Message for bus"""


class User:
    def __init__(
        self,
        outer_id: int,
        nickname: None | str = None,
        name: None | str = None,
        surname: None | str = None,
        patronim: None | str = None,
    ) -> None:
        self.outer_id = outer_id
        self.nickname = nickname
        self.name = name
        self.surname = surname
        self.patronim = patronim
        self.event_history: tp.List[Event] = []
        self.current_scenario_id: None | str = None
        self.current_node_id: None | str = None

    def get_user_var(self, var: str) -> tp.Any:
        raise


class AbstractRepo(ABC):
    # TODO: split repos for every model
    @abstractmethod
    async def create_user(self, user: User) -> User:
        ...

    @abstractmethod
    async def get_user(self, user_id: int) -> User:
        ...

    @abstractmethod
    async def get_or_create_user(self, user: User) -> User:
        ...

    @abstractmethod
    async def set_user_current_scenario(
        self, user: User, scenario_name: str | None
    ) -> None:
        ...

    @abstractmethod
    async def set_user_current_node(self, user: User, node_id: str | None) -> None:
        ...

    @abstractmethod
    async def create_dialogue_scenario(self, dialogue: Dialogue) -> Dialogue:
        ...

    @abstractmethod
    async def get_dialogue(self, dialogue_name: str) -> Dialogue:
        ...


class InMemoryRepo(AbstractRepo):
    def __init__(self) -> None:
        self.users: tp.Dict[int, User] = {}
        self.dialogues: tp.Dict[str, Dialogue] = {}

    async def create_user(self, user: User) -> User:
        self.users[user.outer_id] = user
        return user

    async def get_user(self, user_id: int) -> User:
        return self.users[user_id]

    async def get_or_create_user(self, user: User) -> User:
        try:
            user_from_repo = await self.get_user(user.outer_id)
        except KeyError:
            user_from_repo = await self.create_user(user)
        return user_from_repo

    async def set_user_current_scenario(
        self, user: User, scenario_name: str | None
    ) -> None:
        user_copy = copy.deepcopy(await self.get_user(user.outer_id))
        user_copy.current_scenario_id = scenario_name
        self.users[user.outer_id] = user_copy

    async def set_user_current_node(self, user: User, node_id: str | None) -> None:
        user_copy = copy.deepcopy(await self.get_user(user.outer_id))
        user_copy.current_node_id = node_id
        self.users[user.outer_id] = user_copy

    async def create_dialogue_scenario(self, dialogue: Dialogue) -> Dialogue:
        self.dialogues[dialogue.name] = dialogue
        return dialogue

    async def get_dialogue(self, dialogue_name: str) -> Dialogue:
        return self.dialogues[dialogue_name]


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


class Subscriber:
    @abstractmethod
    async def handle_message(self, message: Event) -> None:
        """Handle message from bus"""


class MessageBus(ABC):
    @abstractmethod
    def __init__(self) -> None:
        """Initialize of bus"""

    @abstractmethod
    def register(self, subscriber: Subscriber) -> None:
        """Register subscriber in bus"""

    @abstractmethod
    def unregister(self, subscriber: Subscriber) -> None:
        """Unregister subscriber in bus"""

    @abstractmethod
    async def public_message(self, message: tp.Union[Event, tp.List[Event]]) -> None:
        """Public message in bus for all subscribers"""


class Poller(ABC):
    def __init__(self, bus: MessageBus, repo: AbstractRepo) -> None:
        """Initialize of poller"""
        self.bus = bus
        self.repo = repo

    @abstractmethod
    async def poll(self) -> None:
        """Poll from outer service"""


class Sender(ABC, Subscriber):
    def __init__(self, *args: tp.Any, **kwargs: tp.Any) -> None:
        """Initialize of sender"""

    @abstractmethod
    async def send(self, event: OutEvent) -> None:
        """Send to outer service"""


class Executor(ABC, Subscriber):
    def __init__(self, repo: AbstractRepo, bus: MessageBus) -> None:
        """Initialize of executor"""
        self.repo = repo
        self.bus = bus

    @abstractmethod
    async def execute_dialogue(self, event: InEvent) -> None:
        """Execute dialogue method"""


class ConcreteMessageBus(MessageBus):
    def __init__(self) -> None:
        """Initialize of bus"""
        self.queue: tp.List[Event] = []
        self.services: tp.List[Subscriber] = []

    def register(self, subscriber: Subscriber) -> None:
        """Register subscriber in bus"""
        self.services.append(subscriber)

    def unregister(self, subscriber: Subscriber) -> None:
        """Unregister subscriber in bus"""
        self.services.remove(subscriber)

    async def public_message(self, message: tp.Union[Event, tp.List[Event]]) -> None:
        """Public and handle message"""
        if isinstance(message, tp.List):
            self.queue += message
        elif isinstance(message, Event):
            self.queue.append(message)
        while self.queue:
            current_message = self.queue.pop(0)
            for sub in self.services:
                await sub.handle_message(current_message)


class TgPoller(Poller):
    def __init__(self, bus: MessageBus, repo: AbstractRepo, bot: aiogram.Bot) -> None:
        """Initialize of poller"""
        super().__init__(bus, repo)
        self.bot = bot
        self.dp = aiogram.Dispatcher(self.bot)
        self.dp.register_message_handler(self.process_message)
        self.dp.register_callback_query_handler(self.process_button_push)

    async def process_message(self, tg_message: aiogram.types.Message) -> None:
        """Process message from telegram"""
        print(f"new text from poller {tg_message.text}")
        try:
            text = tg_message.text
        except Exception as e:
            raise e

        user = User(
            outer_id=tg_message.from_user.id,
            nickname=tg_message.from_user.username,
            name=tg_message.from_user.first_name,
            surname=tg_message.from_user.last_name,
        )
        await self.repo.get_or_create_user(user)
        message = InEvent(user=user, text=text)
        await self.bus.public_message(message=message)

    async def process_button_push(
        self,
        query: aiogram.types.CallbackQuery,  # callback_data: str
    ) -> None:
        """Process pushed button"""
        print("button pushed")
        print(query.data)
        try:
            pushed_button = str(query.data)
        except Exception as e:
            raise e

        user = User(
            outer_id=query.from_user.id,
            nickname=query.from_user.username,
            name=query.from_user.first_name,
            surname=query.from_user.last_name,
        )
        await self.repo.get_or_create_user(user)
        message = InEvent(user=user, button_pushed=pushed_button)
        await self.bus.public_message(message=message)

    async def poll(self) -> None:
        """Poll from outer service. Must be run in background task"""
        print("Start polling")
        try:
            try:
                await self.dp.start_polling()
            except Exception as e:
                raise e
        finally:
            await self.bot.close()


class TgSender(Sender):
    def __init__(self, bot: aiogram.Bot) -> None:
        """Initialize of sender"""
        super().__init__()
        self.bot = bot

    async def handle_message(self, message: Event) -> None:
        """Handle message from bus"""
        if isinstance(message, OutEvent):
            await self.send(message)

    async def send(self, event: OutEvent) -> None:
        """Send to outer service"""
        print("send message")
        keyboard = None
        if event.buttons is not None:
            keyboard = aiogram.types.InlineKeyboardMarkup()
            for button in event.buttons:
                keyboard.row(
                    aiogram.types.InlineKeyboardButton(
                        text=button.text, callback_data=button.callback_data
                    )
                )
        await self.bot.send_message(
            chat_id=event.user.outer_id, text=event.text, reply_markup=keyboard
        )
        await asyncio.sleep(1)


class ConcreteExecutor(Executor):
    def __init__(self, repo: AbstractRepo, bus: MessageBus) -> None:
        """Initialize of executor"""
        super().__init__(repo, bus)

    async def handle_message(self, message: Event) -> None:
        """Handle message from bus"""
        if isinstance(message, InEvent):
            await self.execute_dialogue(message)

    def translate_node_to_event(self, user: User, node: DialogueNode) -> OutEvent:
        if node.node_type == NodeType.inMessage:
            raise
        elif node.node_type == NodeType.outMessage:
            if node.buttons is not None:
                buttons: None | tp.List[Button] = []
                for b in node.buttons:
                    buttons.append(
                        Button(text=b.text, callback_data=f"{b.next_node_id}")
                    )
            else:
                buttons = None
            out_event = OutEvent(user=user, text=node.value, buttons=buttons)
            return out_event
        else:
            raise NotImplementedError

    async def execute_dialogue(self, event: InEvent) -> None:
        """Execute dialogue method"""

        user = await self.repo.get_user(event.user.outer_id)

        if user.current_scenario_id is None:
            print("current scenario is None")
            init_scenario_name = "Test scenario"
            await self.repo.set_user_current_scenario(user, init_scenario_name)

            current_scenario = await self.repo.get_dialogue(init_scenario_name)
            current_node = current_scenario.get_init_root()
        else:
            print(f"current scenario is {user.current_scenario_id}")
            current_scenario = await self.repo.get_dialogue(user.current_scenario_id)
            user_current_node = user.current_node_id
            if user_current_node is None:
                current_node = current_scenario.get_init_root()
            else:
                current_node = current_scenario.get_node_by_id(user.current_node_id)  # type: ignore

        print(f"current node is {current_node.id}")
        new_events: tp.List[OutEvent] = []
        next_node = current_scenario.get_next_node(current_node)
        if (
            (next_node is None)
            and (current_node.node_type == NodeType.outMessage)
            and (current_node.buttons is not None)
        ):
            print("tp0")
            if event.button_pushed is None:
                print("tp1")
                # очищаем текущий сценарий и текущую ноду пользователя
                await self.repo.set_user_current_scenario(user, None)
                await self.repo.set_user_current_node(user, None)
            else:
                print("tp2")
                next_node = current_scenario.get_node_by_id(event.button_pushed)
                # нашли следующую ноду
                if next_node.node_type == NodeType.inMessage:
                    print("tp3")
                    await self.repo.set_user_current_node(user, next_node.id)
                    return
                else:
                    print("tp4")
                    if next_node.node_type == NodeType.outMessage:
                        print("tp5")
                        new_event = self.translate_node_to_event(user, next_node)
                        new_events.append(new_event)
                        next_next_node = current_scenario.get_next_node(next_node)
                        if next_next_node is None:
                            # очищаем текущий сценарий и текущую ноду пользователя
                            await self.repo.set_user_current_scenario(user, None)
                            await self.repo.set_user_current_node(user, None)
                        elif next_next_node.node_type == NodeType.inMessage:
                            await self.repo.set_user_current_node(
                                user, next_next_node.id
                            )
                        elif next_next_node.node_type == NodeType.outMessage:
                            new_event = self.translate_node_to_event(
                                user, next_next_node
                            )
                            new_events.append(new_event)
                            next_next_next_node = current_scenario.get_next_node(
                                next_next_node
                            )
                            if next_next_next_node is None:
                                # очищаем текущий сценарий и текущую ноду пользователя
                                await self.repo.set_user_current_scenario(user, None)
                                await self.repo.set_user_current_node(user, None)
                            elif next_next_next_node.node_type == NodeType.inMessage:
                                await self.repo.set_user_current_node(
                                    user, next_next_next_node.id
                                )
                            elif next_next_node.node_type == NodeType.outMessage:
                                ...
                    else:
                        raise NotImplementedError
        elif next_node is None:
            print("tp6")
            # очищаем текущий сценарий и текущую ноду пользователя
            await self.repo.set_user_current_scenario(user, None)
            await self.repo.set_user_current_node(user, None)
        elif next_node is not None:
            print("tp7")
            # нашли следующую ноду
            if next_node.node_type == NodeType.inMessage:
                print("tp8")
                await self.repo.set_user_current_node(user, next_node.id)
                return
            else:
                print("tp9")
                if next_node.node_type == NodeType.outMessage:
                    print("tp10")
                    new_event = self.translate_node_to_event(user, next_node)
                    new_events.append(new_event)
                    next_next_node = current_scenario.get_next_node(next_node)
                    if next_next_node is None and next_node.buttons is not None:
                        print("tp11")
                        await self.repo.set_user_current_node(user, next_node.id)
                    elif next_next_node is None:
                        print("tp12")
                        # очищаем текущий сценарий и текущую ноду пользователя
                        await self.repo.set_user_current_scenario(user, None)
                        await self.repo.set_user_current_node(user, None)
                    elif next_next_node.node_type == NodeType.inMessage:
                        print("tp13")
                        await self.repo.set_user_current_node(user, next_next_node.id)
                    elif next_next_node.node_type == NodeType.outMessage:
                        print("tp14")
                        new_event = self.translate_node_to_event(user, next_next_node)
                        new_events.append(new_event)
                        next_next_next_node = current_scenario.get_next_node(
                            next_next_node
                        )
                        if (
                            next_next_next_node is None
                            and next_next_node.buttons is not None
                        ):
                            print("tp14_1")
                            await self.repo.set_user_current_node(
                                user, next_next_node.id
                            )
                        elif next_next_next_node is None:
                            print("tp15")
                            # очищаем текущий сценарий и текущую ноду пользователя
                            await self.repo.set_user_current_scenario(user, None)
                            await self.repo.set_user_current_node(user, None)
                        elif next_next_next_node.node_type == NodeType.inMessage:
                            print("tp16")
                            await self.repo.set_user_current_node(
                                user, next_next_next_node.id
                            )
                        elif next_next_node.node_type == NodeType.outMessage:
                            ...
                else:
                    raise NotImplementedError
        else:
            raise

        print(new_events)
        await self.bus.public_message(new_events)

        # вытаскиваем текущий сценарий для пользователя
        # if user.current_scenario_id is None:
        #     init_scenario_name = "Test scenario"
        #     await self.repo.set_user_current_scenario(user, init_scenario_name)
        #
        #     current_scenario = await self.repo.get_dialogue(init_scenario_name)
        #     result_out_event = await self.scenario_from_start(current_scenario, user)
        # else:
        #     current_scenario = await self.repo.get_dialogue(user.current_scenario_id)
        #     # вытаскиваем текущую ноду диалога
        #     user_current_node = user.current_node_id
        #     # если текущий ноды нет, значит клиент сценарий еще не начинал
        #     if user_current_node is None:
        #         result_out_event = await self.scenario_from_start(current_scenario, user)
        #     else:  # если текущий сценарий уже был запущен и мы где-то посередине
        #         result_out_event: tp.List[OutEvent] = []
        #         current_node = current_scenario.get_node_by_id(user_current_node)
        #         next_node = current_scenario.get_next_node(current_node)
        #         prev_node = copy.deepcopy(next_node)  # должно быть не None
        #         new_event = self.translate_node_to_event(next_node)
        #         result_out_event.append(new_event)
        #         if next_node.node_type != NodeType.inMessage:
        #             ...
        #         await self.repo.set_user_current_node(user, prev_node.id)  # type: ignore
        # ...
        # await self.bus.public_message(result_out_event)

    # async def scenario_from_start(self, current_scenario: Dialogue, user: User) -> tp.List[OutEvent]:
    #     result_out_event: tp.List[OutEvent] = []
    #     root_node = current_scenario.get_init_root()
    #     # проверяем что этот сценарий начинается с входящего сообщения
    #     if root_node.node_type == NodeType.inMessage:  # over-engeneering, должно быть так
    #         # берем следующую ноду
    #         next_node = current_scenario.get_next_node(root_node)
    #         prev_node = copy.deepcopy(next_node)
    #         # если она есть и ее тип - исходящее сообщение
    #         if next_node is not None and next_node.node_type == NodeType.outMessage:  # тоже должно быть так
    #             prev_node = copy.deepcopy(next_node)
    #             new_event = self.translate_node_to_event(next_node)
    #             result_out_event.append(new_event)
    #
    #             while next_node:
    #                 prev_node = copy.deepcopy(next_node)
    #                 next_node = current_scenario.get_next_node(next_node)
    #                 # если она есть и ее тип - исходящее сообщение
    #                 if next_node is not None and next_node.node_type == NodeType.outMessage:
    #                     new_event = self.translate_node_to_event(next_node)
    #                     result_out_event.append(new_event)
    #         await self.repo.set_user_current_node(user, prev_node.id)  # type: ignore
    #     return result_out_event
