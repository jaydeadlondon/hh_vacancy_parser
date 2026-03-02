from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, TelegramObject

from shared.utils.logger import get_logger

logger = get_logger(__name__)

PUBLIC_COMMANDS = {"/start", "/help", "/register", "/login"}
PUBLIC_CALLBACKS = {"register", "login", "help"}


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:

        fsm_context: FSMContext | None = data.get("state")
        if fsm_context:
            state = await fsm_context.get_state()

            if state is not None:
                return await handler(event, data)

            state_data = await fsm_context.get_data()
            token = state_data.get("jwt_token")
            if token:
                data["jwt_token"] = token
                return await handler(event, data)

        if isinstance(event, Message):
            text = event.text or ""
            command = text.split()[0] if text.startswith("/") else ""
            if command in PUBLIC_COMMANDS:
                return await handler(event, data)

        elif isinstance(event, CallbackQuery):
            callback_data = event.data or ""
            if callback_data in PUBLIC_CALLBACKS:
                return await handler(event, data)

        if isinstance(event, Message):
            await event.answer(
                "🔐 Для использования бота необходимо авторизоваться.\n"
                "Используй /start чтобы начать.",
            )
        elif isinstance(event, CallbackQuery):
            await event.answer(
                "🔐 Необходима авторизация. Используй /start",
                show_alert=True,
            )

        return None
