import asyncio
import typing as tp
from abc import ABC
from abc import abstractmethod

import aiogram

from src.domain.model import OutEvent


class Sender(ABC):
    def __init__(self, *args: tp.Any, **kwargs: tp.Any) -> None:
        """Initialize of sender"""

    @abstractmethod
    async def send(
        self,
        event: OutEvent,
        history: tp.List[tp.Dict[str, str]],
        ctx: tp.Dict[str, str],
    ) -> str:
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
        ctx: tp.Dict[str, str],
    ) -> None | aiogram.types.InlineKeyboardMarkup:
        keyboard = None
        if event.buttons is not None:
            keyboard = aiogram.types.InlineKeyboardMarkup()
            for button in event.buttons:
                keyboard.row(
                    aiogram.types.InlineKeyboardButton(
                        text=button.text,
                        callback_data=button.callback_data,
                    )
                )
        return keyboard

    # @staticmethod
    # def prepare_text(text: str, ctx: tp.Dict[str, str]) -> str:
    #     # TODO: move to RE
    #     if text in texts:
    #         new_text = texts[text]
    #         if "$" in new_text:
    #             splits = new_text.split("$")
    #             new_text = ""
    #             for s in splits:
    #                 if s in ctx:
    #                     new_text += str(ctx[s])
    #                 else:
    #                     new_text += s
    #         return new_text
    #     return text

    async def send(
        self,
        event: OutEvent,
        history: tp.List[tp.Dict[str, str]],
        ctx: tp.Dict[str, str],
    ) -> str:
        """Send to outer service"""
        print("send message")
        if event.node_to_edit:
            keyboard = await self.get_keyboard(event, ctx)
            message_id_to_edit = await self._search_linked_message(
                history=history, linked_node_id=event.node_to_edit
            )
            res = await self.bot.edit_message_text(
                chat_id=event.user.outer_id,
                text=event.text,
                message_id=message_id_to_edit,
                reply_markup=keyboard,
            )
        else:
            keyboard = await self.get_keyboard(event, ctx)
            res = await self.bot.send_message(
                chat_id=event.user.outer_id,
                text=event.text,
                reply_markup=keyboard,
            )
        await asyncio.sleep(1)
        return str(res.message_id)
