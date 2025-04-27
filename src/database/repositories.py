import abc
from typing import Any, AsyncGenerator, Mapping, Sequence, Type

import pymongo
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument
from pymongo.errors import ConnectionFailure, OperationFailure
from pymongo.results import DeleteResult, InsertManyResult, InsertOneResult, UpdateResult

from .models import (
    AnimalRecordRead,
    InviteRead,
    InviteUpdate,
    MongoCreate,
)
from .models import MongoRead as _MongoRead
from .models import (
    MongoUpdate,
    TgUserID,
    UserCreate,
    UserRead,
    UserRole,
)

MongoDict = Mapping[str, Any]  # * Часть сырого документа Mongo


class BaseRepository[MongoRead: _MongoRead](abc.ABC):
    """Абстрактный класс для CRUD операций."""

    # _bulk_limit = 100  # Ограничение на количество документов в bulk-запросах
    collection: str
    read_model: Type[MongoRead]

    def __init__(self, db: AsyncIOMotorDatabase):
        """Инициализация репозитория."""
        self.client = db[self.collection]

    @abc.abstractmethod
    async def add_indexes(self) -> None:
        """Добавление индексов в таблицу."""
        ...

    async def create_one(self, data: MongoCreate) -> MongoRead:
        """Создать один документ."""
        try:
            response: InsertOneResult = await self.client.insert_one(
                data.model_dump(exclude_none=True)
            )
        except Exception:
            logger.exception(f"Ошибка при записи {data} в {self.client}")

        document = await self.get_one({"_id": response.inserted_id})
        if document:
            logger.success(f"Был создан документ {document}.")
            return document
        else:
            logger.error(
                f"Ошибка при получении документа {response.inserted_id}" f"после его создания."
            )
            raise OperationFailure("Ошибка при получении документа после его создания.")

    async def create_bulk(self, data: Sequence[MongoCreate]) -> int:
        """Создать несколько документов."""
        try:
            response: InsertManyResult = await self.client.insert_many(
                [document.model_dump(exclude_none=True) for document in data]
            )
            logger.success(f"Документы созданы успешно. Количество: {len(response.inserted_ids)}.")
        except Exception:
            logger.exception(f"Ошибка при записи документов в {self.client}")

        return len(response.inserted_ids)

    async def get_one(self, filter: MongoDict) -> MongoRead | None:
        """
        Получить один документ.

        В случае наличия множества документов, вернется первый.
        """
        try:
            document = await self.client.find_one(filter)
        except Exception:
            logger.exception(
                f"Ошибка при получении документа с параметрами {filter} " f"из {self.client}."
            )

        if document:
            logger.success(f"Получен документ {document.get('_id')}.")
            return self.read_model.model_validate(document)
        else:
            logger.info(f"Документ с параметрами {filter} не был найден")

    async def get_bulk(self, filter: MongoDict) -> AsyncGenerator[MongoRead, None]:
        """Получить все документы, удовлетворяющие фильтрам."""
        counter = 0
        try:
            cursor = self.client.find(filter)
            async for document in cursor:
                logger.debug(f"Получен документ {document}")
                validated_document = self.read_model.model_validate(document)
                counter += 1
                yield validated_document

        except ConnectionFailure:
            logger.exception(
                f"Ошибка при получении документов с параметрами {filter} " f"из {self.client}."
            )

        except Exception:
            logger.exception(f"Ошибка в работе генератора. Было получено {counter} документов.")

        logger.info(f"Генератор документов завершил работу. Получено {counter} документов.")

    async def update_one(
        self,
        filter: MongoDict,
        data: MongoUpdate,
    ) -> MongoRead | None:
        """Обновить один документ."""
        try:
            document = await self.client.find_one_and_update(
                filter,
                {"$set": data.model_dump(exclude_none=True)},
                return_document=ReturnDocument.AFTER,
            )
        except Exception:
            logger.exception(
                f"Ошибка при обновлении документа с параметрами {filter} "
                f"данными {data} в {self.client}."
            )

        if document:
            logger.success(f"Документ {document.get('_id')} обновлен.")
            logger.debug(f"Обновлённые данные: {document}")
            return self.read_model.model_validate(document)
        else:
            logger.warning(f"Документ с параметрами {filter} не был найден.")

    async def update_bulk(self, filter: MongoDict, data: MongoUpdate) -> int:
        """Обновить несколько документов."""
        try:
            response: UpdateResult = await self.client.update_many(
                filter,
                {"$set": data.model_dump(exclude_none=True)},
            )
        except Exception:
            logger.exception(
                f"Ошибка при обновлении документов с параметрами {filter} "
                f"данными {data} в {self.client}."
            )

        if response.modified_count > 0:
            logger.success(f"Обновлено {response.modified_count} документов.")
        else:
            logger.info(f"Документы с параметрами {filter} не были найдены.")

        return response.modified_count

    async def delete_one(self, filter: MongoDict) -> MongoDict | None:
        """Удалить один документ."""
        try:
            response: DeleteResult = await self.client.delete_one(filter)
        except Exception:
            logger.exception(
                f"Ошибка при удалении документа с параметрами {filter} в {self.client}."
            )

        if response.raw_result:
            logger.success(f"Документ {response.raw_result} удален.")
            return response.raw_result
        else:
            logger.info(f"Документ с параметрами {filter} не был найден.")


class UserRepository(BaseRepository):
    """Репозиторий для работы с пользователями."""

    collection = "users"
    read_model = UserRead

    async def add_indexes(self) -> None:
        """
        Добавление индексов в таблицу.

        Добавляет уникальные индексы для поля `tg_id`.
        """
        name = f"UQ_{self.collection}_tg_id"
        indexes = await self.client.index_information()
        if indexes.get(name) is None:
            await self.client.create_index(
                [('tg_id', pymongo.ASCENDING)],
                unique=True,
                sparse=True,
                name=name,
            )
            logger.success(f"Индекс tg_id в коллекции {self.collection} создан.")
        else:
            logger.info(f"Индекс tg_id в коллекции {self.collection} уже существует.")

    async def get_by_tg_id(self, tg_id: TgUserID) -> UserRead | None:
        """Получить пользователя по tg_id."""
        return await self.get_one({"tg_id": tg_id})

    async def get_admins(self) -> AsyncGenerator[UserRead, None]:
        """Получить список всех админов."""
        return self.get_bulk({"role": UserRole.ADMIN.value})

    async def is_admin(self, tg_id: TgUserID) -> bool:
        """Проверить, обладает ли пользователь правами админа."""
        user = await self.get_by_tg_id(tg_id)

        return user is not None and user.role == UserRole.ADMIN

    async def add_admin_access(self, tg_id: TgUserID) -> UserRead:
        """Добавить доступ администратору."""
        user = await self.get_by_tg_id(tg_id)

        if user is None:
            model = UserCreate(
                tg_id=tg_id,
                role=UserRole.ADMIN,
            )
            user = await self.create_one(MongoCreate(tg_id=tg_id, role=UserRole.ADMIN.value))

        await self.update_one({"tg_id": tg_id}, MongoUpdate(role=UserRole.ADMIN.value))


class AnimalRecordRepository(BaseRepository):
    """Репозиторий для работы с записями о животных."""

    collection = "animal_records"
    read_model = AnimalRecordRead

    async def add_indexes(self) -> None: ...


class InviteRepository(BaseRepository):
    """Репозиторий для работы с приглашениями."""

    collection = "invites"
    read_model = InviteRead

    async def add_indexes(self) -> None:
        """
        Добавление индексов в таблицу.

        Добавляет уникальные индексы для поля `password`.
        """
        name = f"UQ_{self.collection}_password"
        indexes = await self.client.index_information()
        if indexes.get(name) is None:
            await self.client.create_index(
                [('password', pymongo.ASCENDING)],
                unique=True,
                sparse=True,
                name=name,
            )
            logger.success(f"Индекс password в коллекции {self.collection} создан.")
        else:
            logger.info(f"Индекс password в коллекции {self.collection} уже существует.")

    async def expire(self, password: str) -> InviteRead | None:
        """Пометить приглашение, как истёкшее."""
        return await self.update_one({"password": password}, InviteUpdate())
