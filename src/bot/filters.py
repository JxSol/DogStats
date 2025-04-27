from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message
from loguru import logger

from bot.logic import is_admin


class AdminFilter(BaseFilter):
    """Фильтр для проверки наличия прав администратора у пользователя."""

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        check = await is_admin(event.from_user.id)

        logger.debug(f"Проверка прав администратора для {event.from_user.id}: {check}")
        return check
