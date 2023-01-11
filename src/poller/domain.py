from abc import ABC
from abc import abstractmethod

import aiogram

from src.executor.domain import InEvent
from src.message_bus.domain import MessageBus
from src.repository.repository import AbstractRepo
from src.users.domain import User


class Poller(ABC):
    def __init__(self, bus: MessageBus, repo: AbstractRepo) -> None:
        """Initialize of poller"""
        self.bus = bus
        self.repo = repo

    @abstractmethod
    async def poll(self) -> None:
        """Poll from outer service"""


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