import typing as tp
from abc import ABC
from abc import abstractmethod

import aiogram

from src.adapters.repository import AbstractRepo
from src.domain.model import InEvent
from src.domain.model import User
from src.service_layer.message_bus import MessageBus


class Poller(ABC):
    def __init__(
        self,
        message_handler: tp.Callable[[InEvent], tp.Awaitable[None]],
        user_finder: tp.Callable[[tp.Dict[str, str]], tp.Awaitable[User]],
    ) -> None:
        """Initialize of entrypoints"""
        self.message_handler = message_handler
        self.user_finder = user_finder

    @abstractmethod
    async def poll(self) -> None:
        """Poll from outer service"""


class TgPoller(Poller):
    def __init__(
        self,
        message_handler: tp.Callable[[InEvent], tp.Awaitable[None]],
        user_finder: tp.Callable[[tp.Dict[str, str]], tp.Awaitable[User]],
        bot: aiogram.Bot,
    ) -> None:
        """Initialize of entrypoints"""
        super().__init__(message_handler, user_finder)
        self.bot = bot
        self.dp = aiogram.Dispatcher(self.bot)
        self.dp.register_message_handler(self.process_message)
        self.dp.register_callback_query_handler(self.process_button_push)

    async def process_message(self, tg_message: aiogram.types.Message) -> None:
        """Process message from telegram"""
        print(f"new text from entrypoints {tg_message.text}")
        try:
            text = tg_message.text
        except Exception as e:
            raise e

        user = await self.user_finder(
            dict(
                outer_id=tg_message.from_user.id,
                nickname=tg_message.from_user.username,
                name=tg_message.from_user.first_name,
                surname=tg_message.from_user.last_name,
            )
        )
        message = InEvent(user=user, text=text)
        await self.message_handler(message)

    async def process_button_push(
        self,
        query: aiogram.types.CallbackQuery,
    ) -> None:
        """Process pushed button"""
        print("button pushed")
        print(query.data)
        await query.answer()
        try:
            pushed_button = str(query.data)
        except Exception as e:
            raise e

        user = await self.user_finder(
            dict(
                outer_id=query.from_user.id,
                nickname=query.from_user.username,
                name=query.from_user.first_name,
                surname=query.from_user.last_name,
            )
        )
        message = InEvent(user=user, button_pushed_next=pushed_button)
        await self.message_handler(message)

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
