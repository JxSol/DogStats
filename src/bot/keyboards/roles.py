import enum

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callback_factories import UserListAction, UserListCallbackFactory
from bot.keyboards.basic import back_builder, cancel_builder
from database.models import UserFlag, UserRole


def build_role_control() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text="👋 Пригласить нового пользователя",
        callback_data='invite_user',
    )

    builder.button(
        text="💼 Список админов",
        callback_data=UserListCallbackFactory(role=UserRole.ADMIN.value),
    )
    builder.button(
        text="🔦 Список работников отлова",
        callback_data=UserListCallbackFactory(role=UserRole.CATCHER.value),
    )
    builder.button(
        text="👀 Список гостей",
        callback_data=UserListCallbackFactory(role=UserRole.GUEST.value),
    )

    builder.adjust(1)
    return builder.as_markup()


def build_choose_role() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    class UserRoleButtons(enum.StrEnum):
        """Роли доступа."""

        ADMIN = "💼 Админ"
        CATCHER = "🔦 Работник отлова"
        GUEST = "👀 Гость"

    for role in UserRole:
        builder.button(
            text=UserRoleButtons[role.name].value,
            callback_data=f'{role.value}',
        )

    builder.attach(cancel_builder())
    builder.adjust(1)
    return builder.as_markup()


def build_user_list_menu(role: UserRole) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text="🗑️ Перейти к удалению",
        callback_data=UserListCallbackFactory(
            action=UserListAction.DEL_SELECT,
            role=role.value
        ),
    )

    builder.attach(back_builder('role_control'))

    return builder.as_markup()


def build_user_list_delete(user_list: list[UserFlag]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for user in user_list:
        marker = "❌" if user.is_selected else ""
        builder.button(
            text=f"{marker} {user.name} ({user.tg_id})",
            callback_data=UserListCallbackFactory(
                action=UserListAction.DEL_SELECT,
                role=user.role.value,
                selected=user.tg_id,
            ),
        )

    builder.button(
        text="🗑️ Удалить помеченных пользователей",
        callback_data=UserListCallbackFactory(
            action=UserListAction.DEL_CONFIRM,
            role=user_list[0].role.value
        ),
    )

    builder.attach(back_builder('role_control'))
    builder.adjust(1)
    return builder.as_markup()
