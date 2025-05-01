import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.mongo import MongoStorage
from loguru import logger

import settings
from bot.handlers import animals_router, roles_router, start_router
from bot.logic import add_superadmins_from_venv, init_indexes
from bot.middleware import LoggerMiddleware, UserRoleMiddleware
from database import client

# Настройка логирования
logger.remove()
logger.add(
    sys.stderr,
    colorize=True,
)


async def main():
    # Заполнение базы данных
    logger.info("Инициализирован процесс создания индексов в локальной базе данных...")
    await init_indexes()
    logger.info("Инициализирован процесс добавления суперадминов из venv...")
    await add_superadmins_from_venv()

    # Инициализация роутеров
    logger.info("Инициализирован процесс добавления роутеров...")
    dp = Dispatcher(
        storage=MongoStorage(client.client),
    )

    dp.include_router(start_router)
    logger.success(f'{start_router} добавлен.')

    dp.include_router(roles_router)
    logger.success(f'{roles_router} добавлен.')

    dp.include_router(animals_router)
    logger.success(f'{animals_router} добавлен.')

    # Инициализация мидлварей
    logger.info("Инициализирован процесс добавления миддлваров...")
    dp.update.outer_middleware(LoggerMiddleware())
    logger.success(f'{LoggerMiddleware} добавлен.')

    dp.update.outer_middleware(UserRoleMiddleware())
    logger.success(f'{UserRoleMiddleware} добавлен.')

    # Инициализация бота
    bot = Bot(
        token=settings.tg.bot_token,
    )
    await bot.delete_webhook(drop_pending_updates=True)

    # Запуск бота
    logger.success("Ожидание входящих сообщений...")
    await dp.start_polling(
        bot,
    )


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
