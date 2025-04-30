from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message
from loguru import logger

from bot.keyboards.basic import build_main_keyboard
from bot.logic import check_invite, create_user
from database.models import UserCreate, UserRole

router = Router(name=__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, user_role: UserRole | None, command: CommandObject):
    """Обработка команды /start."""
    logger.debug(f"Обработка команды /start от юзера {message.from_user.id}")
    if user_role:
        # Отвечаем пользователю
        await message.answer(
            text="И снова здравствуй! 😻",
            reply_markup=build_main_keyboard(user_role),
        )
        return

    if command.args and (invite := await check_invite(command.args)):
        # Создаем нового пользователя
        model = UserCreate(
            tg_id=message.from_user.id,
            name=invite.username,
            role=invite.role,
        )
        await create_user(model)

        # Отвечаем пользователю
        await message.answer(
            text=(
                "Добро пожаловать! 😻 "
                "Чтобы начать пользоваться сервисом, используй клавиатуру снизу."
            ),
            reply_markup=build_main_keyboard(invite.role),
        )
        return

    await message.answer(text="Ссылка недействительна 😿")
