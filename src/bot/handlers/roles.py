from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from bot.callback_factories import UserListAction, UserListCallbackFactory
from bot.filters import AdminFilter
from bot.keyboards.basic import build_confirm_cancel, cancel_builder
from bot.keyboards.roles import (
    build_choose_role,
    build_role_control,
    build_user_list_delete,
    build_user_list_menu,
)
from bot.logic import create_invite, get_users_by_role, user_delete
from bot.states import InviteUserState, UserDeleteState
from database.models import UserFlag, UserRole
from utils import generate_invite_link

router = Router(name=__name__)
router.message.filter(AdminFilter())


@router.message(F.text == "👥 Пользователи")
@router.callback_query(F.data == "role_control")
async def handle_cb_msg_role_control(update: CallbackQuery | Message, state: FSMContext):
    """Обработка открытия меню управления пользователями."""
    await state.clear()

    if isinstance(update, CallbackQuery):
        await update.answer()
        await update.message.delete()
        message = update.message
    else:
        message = update

    await message.answer(
        text="👥 <b>Панель управления пользователями</b>",
        reply_markup=build_role_control(),
        parse_mode="HTML",
    )


@router.callback_query(UserListCallbackFactory.filter(F.action == UserListAction.DISPLAY))
async def handle_cb_user_list_display(
    callback: CallbackQuery,
    callback_data: UserListCallbackFactory,
):
    """Обработка открытия списка пользователей."""
    logger.debug(f"Пользователь {callback.from_user.id} запросил список {callback_data.role}.")
    translated = {
        'ADMIN': 'администраторов',
        'CATCHER': 'работников отлова',
        'GUEST': 'гостей',
    }

    role = UserRole(callback_data.role)
    user_list = await get_users_by_role(role)
    if not user_list:
        await callback.answer(f"🤷‍♂️ Список {translated[role.name]} пуст.")
        return

    users = [f"{i+1}. {u.name} (<code>{u.tg_id}</code>)" for i, u in enumerate(user_list)]
    text = f"💼 <b>Список {translated[role.name]}:</b>\n" f"{'\n'.join(users)}"

    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(
        text=text,
        parse_mode="HTML",
        reply_markup=build_user_list_menu(role),
    )


# * =========================== Приглашение нового пользователя =========================== * #


@router.callback_query(F.data == "invite_user")
async def handle_cb_invite_user(callback: CallbackQuery, state: FSMContext):
    """Команда для добавления нового пользователя."""
    await state.clear()
    await state.set_state(InviteUserState.input_role)

    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(
        text="Выберите роль для нового пользователя:",
        reply_markup=build_choose_role(),
    )


@router.callback_query(InviteUserState.input_role)
async def handle_st_input_role(callback: CallbackQuery, state: FSMContext):
    """Команда для выбора роли нового пользователя."""
    await state.update_data(role=callback.data)
    await state.set_state(InviteUserState.input_name)

    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(
        text="Введите имя для нового пользователя. Это имя будет использоваться во всём сервисе.",
        reply_markup=cancel_builder().as_markup(),
    )


@router.message(InviteUserState.input_name, F.text)
async def handle_st_invite_user_input_name(message: Message, state: FSMContext):
    """Команда для ввода имени нового пользователя."""
    await state.update_data(username=message.text)
    await state.set_state(InviteUserState.confirm)
    data = await state.get_data()

    await message.bot.delete_message(message.chat.id, message.message_id - 1)
    await message.answer(
        text=(
            f"Вы выбрали роль: {data['role']}\n"
            f"Имя: {data['username']}\n"
            f"Подтвердите данные нового пользователя."
        ),
        reply_markup=build_confirm_cancel(),
    )


@router.callback_query(InviteUserState.confirm, F.data == "confirm")
async def handle_st_invite_user_confirm(callback: CallbackQuery, state: FSMContext):
    """Команда для подтверждения приглашения нового пользователя."""
    data = await state.get_data()
    invite = await create_invite(**data)
    link = generate_invite_link(invite.password)

    await state.clear()
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(
        text=(
            f"✅ Приглашение успешно создано.\n"
            f"Отошлите эту ссылку пользователю {data['username']}: `{link}`"
        ),
    )


# * ================================ Удаление пользователя ================================ * #


@router.callback_query(
    StateFilter(None),
    UserListCallbackFactory.filter(F.action == UserListAction.DEL_SELECT),
)
async def handle_cb_user_list_delete(
    callback: CallbackQuery,
    callback_data: UserListCallbackFactory,
    state: FSMContext,
):
    """Обработка коллбэк фабрики user_list::delete."""
    role = UserRole(callback_data.role)
    user_list = await get_users_by_role(role)
    user_list = [UserFlag(**user.model_dump()) for user in user_list]

    await state.set_state(UserDeleteState.select)
    await state.update_data(user_list=[user.model_dump() for user in user_list])

    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(
        text="Выберите пользователей для удаления:",
        reply_markup=build_user_list_delete(user_list),
    )


@router.callback_query(
    UserDeleteState.select, UserListCallbackFactory.filter(F.action == UserListAction.DEL_SELECT)
)
async def handle_st_user_select(
    callback: CallbackQuery,
    callback_data: UserListCallbackFactory,
    state: FSMContext,
):
    """Обработка состояния выбора пользователей на удаление."""
    data = await state.get_data()
    user_list = data['user_list']
    user_list = [UserFlag(**user) for user in data['user_list']]

    for i, user in enumerate(user_list):
        if user.tg_id == callback_data.selected:
            user_list[i].is_selected = not user.is_selected

    await state.update_data(user_list=[user.model_dump() for user in user_list])

    await callback.message.edit_reply_markup(
        reply_markup=build_user_list_delete(user_list),
    )


@router.callback_query(
    UserDeleteState.select, UserListCallbackFactory.filter(F.action == UserListAction.DEL_CONFIRM)
)
async def handle_cb_user_list_delete_selected(
    callback: CallbackQuery,
    callback_data: UserListCallbackFactory,
    state: FSMContext,
):
    """Обработка состояния выбора пользователей на удаление."""
    data = await state.get_data()
    user_list = data['user_list']
    user_list = [UserFlag(**user) for user in data['user_list']]

    deleted = False
    for user in user_list:
        if user.is_selected:
            deleted = True
            await user_delete(user.tg_id)

    if deleted:
        await callback.answer()
        await callback.message.delete()
        await callback.message.answer("✅ Пользователи успешно удалены.")
    else:
        await callback.answer("🤷‍♂️ Не выбрано ни одного пользователя.")
