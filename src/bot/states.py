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


class AnimalAddState(StatesGroup):
    """Состояние для добавления животного."""

    input_catch_photo = State()
    input_catch_place = State()
    input_catch_date = State()
    input_animal_type = State()
    input_breed = State()
    input_color = State()
    input_sex = State()
    input_features = State()
    input_transfer_photo = State()
    input_transfer_date = State()
    input_comment = State()
    confirm = State()
