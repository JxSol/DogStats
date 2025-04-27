from aiogram.fsm.state import State, StatesGroup


class InviteUserState(StatesGroup):
    """Состояние для приглашения нового пользователя."""

    input_role = State()
    input_name = State()
    confirm = State()


class UserDeleteState(StatesGroup):
    """Состояние для удаления пользователя."""

    select = State()
    confirm = State()
