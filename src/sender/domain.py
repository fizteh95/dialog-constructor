import asyncio
import typing as tp
from abc import ABC
from abc import abstractmethod

import aiogram

from src.executor.domain import Event
from src.executor.domain import OutEvent
from src.message_bus.domain import Subscriber


class Sender(ABC, Subscriber):
    def __init__(self, *args: tp.Any, **kwargs: tp.Any) -> None:
        """Initialize of sender"""

    @abstractmethod
    async def send(self, event: OutEvent) -> None:
        """Send to outer service"""


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
