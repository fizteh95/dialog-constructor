import typing as tp
from abc import ABC, abstractmethod
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
class OutEvent(Event):
    user: User
    text: str
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


class Sender(ABC, Subscriber):
    @abstractmethod
    def __init__(self) -> None:
        """Initialize of sender"""

    @abstractmethod
    def send(self) -> None:
        """Send to outer service"""


class Executor(ABC, Subscriber):
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
    def __init__(self, bus: MessageBus, bot_token: str) -> None:
        """Initialize of poller"""
        super().__init__(bus)
        self.bot = aiogram.Bot(token=bot_token)
        self.dp = aiogram.Dispatcher(self.bot)

    async def poll(self) -> None:
        """Poll from outer service"""