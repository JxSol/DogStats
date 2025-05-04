import enum

from aiogram.filters.callback_data import CallbackData


class UserListAction(enum.StrEnum):
    """Действия для списка пользователей."""

    DISPLAY = 'display'
    DEL_SELECT = 'del_select'
    DEL_CONFIRM = 'del_confirm'


class UserListCallbackFactory(CallbackData, prefix='user_list'):
    """Фабрика коллбеков для управления пользователями."""

    role: str
    action: str = UserListAction.DISPLAY
    selected: int | None = None


class ItemPaginatorCallbackFactory(CallbackData, prefix='item'):
    """Фабрика коллбеков для управления записями о животных."""

    item_id: str


class AnimalRecordCallbackFactory(ItemPaginatorCallbackFactory, prefix='animal'):
    """Фабрика коллбеков для управления записями о животных."""

    action: str = 'display'
