from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from loguru import logger

from bot.logic import get_user


class LoggerMiddleware(BaseMiddleware):
    async def __call__(  # type: ignore
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        update: Update,
        data: dict[str, Any],
    ) -> Any:
        if update.message:
            text = update.message.text
            if text and len(text) > 9:
                text = text[:10] + '...'

            logger.debug(
                f"\nLoggerMiddleware("
                f"\n    update_type: message;"
                f"\n    state: {await data['state'].get_state()};"
                f"\n    user_id: {update.message.from_user.id};"
                f"\n    content_type: {update.message.content_type};"
                f"\n    text: {text}"
                f"\n)"
            )

        elif update.callback_query:
            logger.debug(
                f"\nLoggerMiddleware("
                f"\n    update_type: callback;"
                f"\n    state: {await data['state'].get_state()};"
                f"\n    user_id: {update.callback_query.from_user.id};"
                f"\n    callback_data: {update.callback_query.data}"
                f"\n)"
            )

        elif update.chat_join_request:
            if update.chat_join_request.invite_link:
                invited_by = update.chat_join_request.invite_link.creator.id
            else:
                invited_by = 'Undefined'

            logger.debug(
                f"\nLoggerMiddleware("
                f"\n    update_type: chat_join_request;"
                f"\n    user_id: {update.chat_join_request.from_user.id};"
                f"\n    chat_id: {update.chat_join_request.chat.id};"
                f"\n    chat_type: {update.chat_join_request.chat.type};"
                f"\n    invited_by: {invited_by};"
                f"\n)"
            )

        else:
            for event in tuple(update.__dict__.values())[1:]:
                if event:
                    logger.debug(f'LoggerMiddleware{event}')

        return await handler(update, data)


class UserRoleMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Добавляет роль пользователя в data."""
        data["user_role"] = None
        user = data.get("event_from_user")

        if user:
            _user = await get_user(user.id)
            data["user_role"] = _user.role if _user else None

        logger.debug(f"UserRoleMiddleware: {user.id}: {data['user_role']}")

        result = await handler(event, data)
        return result
