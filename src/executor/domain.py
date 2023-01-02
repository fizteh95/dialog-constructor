import typing as tp
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass

import aiogram


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
        self.current_scenario_id: None | int = None
        self.current_node_id: None | int = None

    def get_user_var(self, var: str) -> tp.Any:
        raise


@dataclass
class InEvent(Event):
    user: User
    text: str
    ...


@dataclass
class Button:
    text: str
    callback_data: tp.Optional[tp.Dict[str, str]]


@dataclass
class OutEvent(Event):
    user: User
    text: str
    buttons: tp.Optional[tp.List[Button]]
    ...


class Subscriber(ABC):
    @abstractmethod
    def handle_message(self, message: Event) -> None:
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
    def public_message(self, message: Event) -> None:
        """Register subscriber in bus"""


class Poller(ABC):
    def __init__(self, bus: MessageBus, *args: tp.Any, **kwargs: tp.Any) -> None:
        """Initialize of poller"""
        self.bus = bus

    @abstractmethod
    async def poll(self) -> None:
        """Poll from outer service"""


class Sender(ABC, Subscriber):  # type: ignore
    def __init__(self, *args: tp.Any, **kwargs: tp.Any) -> None:
        """Initialize of sender"""

    @abstractmethod
    async def send(self, event: OutEvent) -> None:
        """Send to outer service"""


class Executor(ABC, Subscriber):  # type: ignore
    @abstractmethod
    def __init__(self) -> None:
        """Initialize of executor"""

    @abstractmethod
    def execute_dialogue(self) -> None:
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

    def public_message(self, message: Event) -> None:
        """Public and handle message"""
        self.queue.append(message)
        while self.queue:
            current_message = self.queue.pop()
            for sub in self.services:
                sub.handle_message(current_message)


class TgPoller(Poller):
    def __init__(self, bus: MessageBus, bot: aiogram.Bot) -> None:
        """Initialize of poller"""
        super().__init__(bus)
        self.bot = bot
        self.dp = aiogram.Dispatcher(self.bot)
        self.dp.register_message_handler(self.process_message)

    async def process_message(self, tg_message: aiogram.types.Message) -> None:
        """Process message from telegram"""
        try:
            text = tg_message.text
        except Exception as e:
            raise

        user = User(
            outer_id=tg_message.from_user.id,
            nickname=tg_message.from_user.username,
            name=tg_message.from_user.first_name,
            surname=tg_message.from_user.last_name,
        )
        message = InEvent(user=user, text=text)
        self.bus.public_message(message=message)

    async def poll(self) -> None:
        """Poll from outer service. Must be run in background task"""
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
        keyboard = None
        if event.buttons is not None:
            keyboard = aiogram.types.InlineKeyboardMarkup()
            for button in event.buttons:
                keyboard.row(aiogram.types.InlineKeyboardButton(text=button.text))
        await self.bot.send_message(chat_id=event.user.outer_id, text=event.text, reply_markup=keyboard)


class ConcreteExecutor(Executor):
    def __init__(self) -> None:
        """Initialize of executor"""

    def handle_message(self, message: Event) -> None:
        """Handle message from bus"""

    def execute_dialogue(self) -> None:
        """Execute dialogue method"""
