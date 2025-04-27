from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

import settings


class MongoClient:
    """
    Класс для работы с базой данных MongoDB.

    Использование:
    from _localdb.client import client
    await client.db.collection.find_one()
    await client.aiogram_fsm.collection.find_one()
    """

    def __init__(self, dsn: str, db_name: str):
        self.dsn = dsn
        self._db = db_name
        self.client = self._init_client()

    def _init_client(self) -> AsyncIOMotorClient:
        try:
            client = AsyncIOMotorClient(self.dsn)
        except Exception:
            logger.exception(f"Не получилось осуществить подключение к {self.dsn}")

        return client

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Получить соединение с основной базой данных."""
        try:
            client = self.client[self._db]
            logger.success(f"Подключение к {self.dsn}/{self._db} прошло успешно")
        except Exception:
            logger.exception(f"Не получилось осуществить подключение к базе {self.dsn}/{self._db}")

        return client

    @property
    def aiogram_fsm(self) -> AsyncIOMotorDatabase:
        """Получить соединение с базой данных для хранения состояний в aiogram."""
        try:
            client = self.client['aiogram_fsm']
            logger.success(f"Подключение к {self.dsn}/aiogram_fsm прошло успешно")
        except Exception:
            logger.exception(
                f"Не получилось осуществить подключение к базе " f"{self.dsn}/aiogram_fsm"
            )

        return client


client = MongoClient(
    settings.db.db_dsn,
    'dog_stats_db',
)
