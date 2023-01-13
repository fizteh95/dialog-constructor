import typing as tp
from abc import ABC
from abc import abstractmethod

from src.domain.model import Event


class Subscriber(tp.Protocol):
    async def handle_message(self, message: Event) -> tp.List[Event]:
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
                events = await sub.handle_message(current_message)
                self.queue += events
