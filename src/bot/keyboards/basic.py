from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from database.models import UserRole


def back_builder(callback: str | CallbackData) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()

    builder.button(
        text="↩️ Назад",
        callback_data=callback,
    )

    return builder


def cancel_builder(callback: str | CallbackData = 'cancel') -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()

    builder.button(
        text="❌ Отмена",
        callback_data=callback,
    )

    return builder


def build_confirm_cancel(
    confirm_callback: str | CallbackData = 'confirm',
    cancel_callback: str | CallbackData = 'cancel',
) -> InlineKeyboardMarkup:
    """Формирует клавиатуру подтверждения и отмены."""
    builder = InlineKeyboardBuilder()

    builder.button(text="✅ Подтвердить", callback_data=confirm_callback)
    builder.attach(cancel_builder(cancel_callback))

    builder.adjust(2)
    return builder.as_markup()


def build_main_keyboard(role: UserRole) -> ReplyKeyboardMarkup:
    """Формирует основную клавиатуру."""
    builder = ReplyKeyboardBuilder()

    if role in (UserRole.CATCHER, UserRole.ADMIN):
        builder.button(
            text="🐶 Добавить животное",
        )

        builder.button(
            text="🐾 Мои животные",
        )

    builder.button(
        text="🐾 Список животных",
    )

    if role == UserRole.ADMIN:
        builder.button(
            text="👥 Пользователи",
        )

    builder.adjust(1)

    if role in (UserRole.CATCHER, UserRole.ADMIN):
        builder.adjust(2, 1)

    return builder.as_markup()
