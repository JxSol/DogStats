import secrets

from loguru import logger

import settings
from database.client import client
from database.models import (
    AnimalRecordCreate,
    AnimalRecordRead,
    InviteCreate,
    InviteRead,
    UserCreate,
    UserRead,
    UserRole,
)
from database.repositories import AnimalRecordRepository, InviteRepository, UserRepository


async def init_indexes() -> None:
    """Инициализация индексов в базе данных."""
    repo = UserRepository(client.db)
    await repo.add_indexes()

    repo = InviteRepository(client.db)
    await repo.add_indexes()


async def is_admin(tg_id: int) -> bool:
    """Проверяет, является ли пользователь администратором."""
    repo = UserRepository(client.db)
    return await repo.is_admin(tg_id)


async def get_users_by_role(role: UserRole) -> list[UserRead]:
    """Получает список пользователей по роли."""
    repo = UserRepository(client.db)
    return [user async for user in repo.get_bulk({"role": role.value})]


async def get_admins() -> list[UserRead]:
    """Получает список администраторов."""
    repo = UserRepository(client.db)
    return [admin async for admin in await repo.get_admins()]


async def get_user(tg_id: int) -> UserRead | None:
    """Получает пользователя по tg_id."""
    repo = UserRepository(client.db)
    return await repo.get_by_tg_id(tg_id)


async def check_invite(password: str) -> InviteRead | None:
    """Проверить приглашение."""
    repo = InviteRepository(client.db)
    invite = await repo.get_one({"password": password})

    if invite is None or invite.is_expired:
        return None

    await repo.expire(password)
    return invite


async def create_user(UserCreate: UserCreate) -> UserRead:
    """Создать нового пользователя."""
    repo = UserRepository(client.db)
    return await repo.create_one(UserCreate)


async def create_invite(role: UserRole, username: str) -> InviteRead:
    """Создать новое приглашение."""
    repo = InviteRepository(client.db)

    model = InviteCreate(
        password=secrets.token_urlsafe(6),
        role=role,
        username=username,
    )

    return await repo.create_one(model)


async def add_superadmins_from_venv() -> None:
    """Добавление суперадминов из переменных окружения."""
    repo = UserRepository(client.db)

    for _id in settings.tg.admin_ids:
        user = await repo.get_by_tg_id(_id)

        if user is None:
            model = UserCreate(
                tg_id=_id,
                role=UserRole.ADMIN,
                name="Администратор",
            )
            await repo.create_one(model)
            logger.success(f"Суперадмин {_id} добавлен.")
        else:
            logger.info(f"Суперадмин {_id} уже существует.")


async def user_delete(tg_id: int) -> None:
    """Удалить пользователя."""
    repo = UserRepository(client.db)
    result = await repo.delete_one({"tg_id": tg_id})
    if result:
        logger.success(f"Пользователь {tg_id} был удален.")
    else:
        logger.error(f"Пользователь {tg_id} не был удален.")


async def add_animal_record(model: AnimalRecordCreate) -> AnimalRecordRead:
    """Добавить запись о животном."""
    repo = AnimalRecordRepository(client.db)
    return await repo.create_one(model)
