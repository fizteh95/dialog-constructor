import asyncio
import typing as tp
from abc import ABC
from abc import abstractmethod

import aiogram

from src.domain.model import OutEvent

texts = {
    "TEXT1": "Введите широту",
    "TEXT2": "Неправильная широта, попробуйте еще раз",
    "TEXT3": "Введите долготу",
    "TEXT4": "Неправильная долгота, попробуйте еще раз",
    "TEXT5": "Температура в заданном месте: $temperature$ градусов Цельсия",
    "TEXT6": "Что-то пошло не так",
    "TEXT7": "Хотите посмотреть фичу изменения сообщения?",
    "TEXT8": "Да",
    "TEXT9": "Нет",
    "TEXT10": "Сообщение изменено ;)",
    "TEXT11": "Сценарий окончен.",
}


class Sender(ABC):
    def __init__(self, *args: tp.Any, **kwargs: tp.Any) -> None:
        """Initialize of sender"""

    @abstractmethod
    async def send(
        self,
        event: OutEvent,
        history: tp.List[tp.Dict[str, str]],
        ctx: tp.Dict[str, tp.Dict[str, str]],
    ) -> str | None:
        """Send to outer service"""


class TgSender(Sender):
    def __init__(self, bot: aiogram.Bot) -> None:
        """Initialize of sender"""
        super().__init__()
        self.bot = bot

    @staticmethod
    async def _search_linked_message(
        history: tp.List[tp.Dict[str, str]], linked_node_id: str
    ) -> str:
        for pair in history[::-1]:
            if linked_node_id in pair:
                return pair[linked_node_id]
        return ""

    async def get_keyboard(
        self,
        event: OutEvent,
        ctx: tp.Dict[str, tp.Dict[str, str]],
    ) -> None | aiogram.types.InlineKeyboardMarkup:
        keyboard = None
        if event.buttons is not None:
            keyboard = aiogram.types.InlineKeyboardMarkup()
            for button in event.buttons:
                keyboard.row(
                    aiogram.types.InlineKeyboardButton(
                        text=self.prepare_text(event.user.outer_id, button.text, ctx),
                        callback_data=button.callback_data,
                    )
                )
        return keyboard

    def prepare_text(
        self, user_outer_id: str, text: str, ctx: tp.Dict[str, tp.Dict[str, str]]
    ) -> str:
        # TODO: move to RE
        current_ctx = ctx[user_outer_id]
        if text in texts:
            new_text = texts[text]
            if "$" in new_text:
                splits = new_text.split("$")
                new_text = ""
                for s in splits:
                    if s in current_ctx:
                        new_text += str(current_ctx[s])
                    else:
                        new_text += s
            return new_text
        return "Text not found"

    async def send(
        self,
        event: OutEvent,
        history: tp.List[tp.Dict[str, str]],
        ctx: tp.Dict[str, tp.Dict[str, str]],
    ) -> str | None:
        """Send to outer service"""
        print("send message")
        if event.node_to_edit:
            keyboard = await self.get_keyboard(event, ctx)
            message_id_to_edit = await self._search_linked_message(
                history=history, linked_node_id=event.node_to_edit
            )
            res = await self.bot.edit_message_text(
                chat_id=event.user.outer_id,
                text=self.prepare_text(event.user.outer_id, event.text, ctx),
                message_id=message_id_to_edit,
                reply_markup=keyboard,
            )
        else:
            keyboard = await self.get_keyboard(event, ctx)
            res = await self.bot.send_message(
                chat_id=event.user.outer_id,
                text=self.prepare_text(event.user.outer_id, event.text, ctx),
                reply_markup=keyboard,
            )
        await asyncio.sleep(1)
        return str(res.message_id)
