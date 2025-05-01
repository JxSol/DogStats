from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
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


@router.callback_query(F.data == "cancel")
async def handle_cb_cancel(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработка нажатия кнопки отмены."""
    logger.debug(f"Пользователь {callback.from_user.id} отменил действие.")
    await state.clear()
    await callback.answer("Действие отменено.")
    await callback.message.delete()
