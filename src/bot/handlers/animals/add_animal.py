import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.media_group import MediaGroupBuilder
from loguru import logger

from bot.keyboards.animals import (
    build_choose_animal_type,
    build_choose_sex,
    build_input_date,
    geo_button,
)
from bot.keyboards.basic import build_confirm_cancel, build_main_keyboard, build_skip_cancel, cancel_builder
from bot.logic import add_animal_record
from bot.states import AnimalAddState
from database.models import AnimalRecordCreate, AnimalType, Sex, UserRole
from settings import TZINFO

router = Router(name=__name__)


# * ================================== Добавление животного ================================== * #


@router.message(F.text == "🐶 Добавить животное")
async def handle_msg_add_animal(
    message: Message,
    state: FSMContext,
) -> None:
    """Обработка начала процедуры добавления животного."""
    logger.debug(f"Пользователь {message.from_user.id} начал добавление животного.")
    await state.clear()

    await ask_for_input_catch_photo(message, state)


# * =============================== Добавление фото при отлове =============================== * #


async def ask_for_input_catch_photo(
    message: Message,
    state: FSMContext,
) -> None:
    """Запрашивает отправку фото при отлове."""
    await state.set_state(AnimalAddState.input_catch_photo)

    await message.answer(
        text="📸 Отправьте фото животного, сделанное при отлове.",
        reply_markup=build_skip_cancel(
            skip_callback='input_catch_place',
        ),
    )


@router.message(AnimalAddState.input_catch_photo, F.photo)
async def handle_st_input_catch_photo(
    message: Message,
    state: FSMContext,
) -> None:
    """Обработка фото животного при отлове."""
    logger.debug(f"Пользователь {message.from_user.id} отправил фото животного.")
    await state.update_data(catch_photo=message.photo[-1].file_id)

    await message.bot.edit_message_reply_markup(
        chat_id=message.chat.id,
        message_id=message.message_id - 1,
        reply_markup=None,
    )
    await ask_for_input_catch_place(message, state)


# * ==================================== Ввод места отлова ==================================== * #


async def ask_for_input_catch_place(
    message: Message,
    state: FSMContext,
) -> None:
    """Запрашивает место отлова."""
    await state.set_state(AnimalAddState.input_catch_place)

    await message.answer(
        text="🗺️ Введите место отлова животного.",
        reply_markup=cancel_builder().as_markup(),
    )
    await message.answer(
        text="📍 Или отправьте геолокацию.",
        reply_markup=geo_button(),
    )


@router.callback_query(F.data == "input_catch_place")
async def handle_cb_input_catch_place(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработка ввода места отлова."""
    logger.debug(f"Пользователь {callback.from_user.id} перешёл к этапу ввода места отлова.")

    await callback.answer()
    await callback.message.delete()

    await ask_for_input_catch_place(callback.message, state)


@router.message(AnimalAddState.input_catch_place, (F.location | F.text))
async def handle_st_input_catch_place(
    message: Message,
    state: FSMContext,
    user_role: str,
) -> None:
    """Обработка ввода места отлова."""
    if message.location:
        logger.debug(f"Пользователь {message.from_user.id} отправил геолокацию.")
        location = f"{message.location.latitude}, {message.location.longitude}"
    else:
        logger.debug(f"Пользователь {message.from_user.id} ввёл место отлова.")
        location = message.text.strip()

    await state.update_data(catch_place=location)

    await message.bot.edit_message_reply_markup(
        chat_id=message.chat.id,
        message_id=message.message_id - 2,
        reply_markup=None,
    )
    await message.bot.delete_message(
        chat_id=message.chat.id,
        message_id=message.message_id - 1,
    )

    await message.answer(
        text="📍 Геолокация сохранена",
        reply_markup=build_main_keyboard(UserRole(user_role)),
    )

    await ask_for_input_catch_date(message, state)


# * ==================================== Ввод даты отлова ==================================== * #


async def ask_for_input_catch_date(
    message: Message,
    state: FSMContext,
) -> None:
    """Запрашивает дату отлова."""
    current_date = datetime.datetime.now(TZINFO).strftime("%Y-%m-%d %H:%M")

    await state.set_state(AnimalAddState.input_catch_date)
    await state.update_data(catch_date=current_date)

    await message.answer(
        text="📅 Введите дату отлова животного в формате ГГГГ-ММ-ДД чч:мм",
        reply_markup=build_input_date(current_date),
    )


@router.callback_query(AnimalAddState.input_catch_date, F.data == "input_current_date")
async def handle_cb_input_current_date(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработка выбора текущей даты."""
    logger.debug(f"Пользователь {callback.from_user.id} выбрал текущую дату.")

    await callback.answer()
    await callback.message.edit_reply_markup(
        reply_markup=None,
    )

    await ask_for_input_animal_type(callback.message, state)


@router.message(
    AnimalAddState.input_catch_date,
    F.text.regexp(r"\d{4}-\d{2}-\d{1,2} \d{1,2}:\d{2}"),
)
async def handle_st_input_catch_date(
    message: Message,
    state: FSMContext,
) -> None:
    """Обработка ввода даты отлова."""
    catch_date = message.text
    logger.debug(f"Пользователь {message.from_user.id} ввёл дату отлова {catch_date}.")
    await state.update_data(catch_date=catch_date)

    await message.bot.edit_message_reply_markup(
        chat_id=message.chat.id,
        message_id=message.message_id - 1,
        reply_markup=None,
    )

    await ask_for_input_animal_type(message, state)


# * ================================== Выбор вида животного ================================== * #


async def ask_for_input_animal_type(
    message: Message,
    state: FSMContext,
) -> None:
    """Запрашивает ввод вида животного."""
    await state.set_state(AnimalAddState.input_animal_type)

    await message.answer(
        text="❔ Выберите вид животного.",
        reply_markup=build_choose_animal_type(),
    )


@router.callback_query(F.data == "input_animal_type")
async def handle_cb_input_animal_type(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработка выбора вида животного."""
    logger.debug(f"Пользователь {callback.from_user.id} перешёл к этапу выбора вида животного.")

    await callback.answer()
    await callback.message.delete()

    await ask_for_input_animal_type(callback.message, state)


@router.callback_query(AnimalAddState.input_animal_type, F.data.startswith("animal_type_"))
async def handle_cb_animal_type(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработка выбора вида животного."""
    animal_type = callback.data.split("_")[2]
    logger.debug(f"Пользователь {callback.from_user.id} выбрал тип {animal_type}.")
    await state.update_data(animal_type=AnimalType[animal_type].value)

    await callback.message.edit_reply_markup(
        reply_markup=build_choose_animal_type(AnimalType[animal_type]),
    )

    await ask_for_input_breed(callback.message, state)


# * ================================= Ввод породы животного ================================= * #


async def ask_for_input_breed(
    message: Message,
    state: FSMContext,
) -> None:
    """Запрашивает ввод типа животного."""
    await state.set_state(AnimalAddState.input_breed)

    await message.answer(
        text="🐩 Введите предполагаемую породу животного.",
        reply_markup=cancel_builder().as_markup(),
    )


@router.message(AnimalAddState.input_breed, F.text)
async def handle_st_input_breed(
    message: Message,
    state: FSMContext,
) -> None:
    """Обработка ввода породы животного."""
    breed = message.text.strip()
    logger.debug(f"Пользователь {message.from_user.id} ввёл породу {breed}.")
    await state.update_data(breed=breed)

    await message.bot.edit_message_reply_markup(
        chat_id=message.chat.id,
        message_id=message.message_id - 1,
        reply_markup=None,
    )

    await ask_for_input_color(message, state)


# * ================================= Ввод цвета животного ================================= * #


async def ask_for_input_color(
    message: Message,
    state: FSMContext,
) -> None:
    """Запрашивает ввод типа животного."""
    await state.set_state(AnimalAddState.input_color)

    await message.answer(
        text="🎨 Введите цвет животного, окрас его шерсти.",
        reply_markup=cancel_builder().as_markup(),
    )


@router.message(AnimalAddState.input_color, F.text)
async def handle_st_input_color(
    message: Message,
    state: FSMContext,
) -> None:
    """Обработка ввода цвета животного."""
    color = message.text.strip()
    logger.debug(f"Пользователь {message.from_user.id} ввёл цвет {color}.")
    await state.update_data(color=color)

    await message.bot.edit_message_reply_markup(
        chat_id=message.chat.id,
        message_id=message.message_id - 1,
        reply_markup=None,
    )

    await ask_for_input_sex(message, state)


# * ================================= Выбор пола животного ================================= * #


async def ask_for_input_sex(
    message: Message,
    state: FSMContext,
) -> None:
    """Запрашивает ввод пола животного."""
    await state.set_state(AnimalAddState.input_sex)

    await message.answer(
        text="⚧️ Выберите пол животного.",
        reply_markup=build_choose_sex(),
    )


@router.callback_query(AnimalAddState.input_sex, F.data.startswith("sex_"))
async def handle_cb_sex(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработка выбора пола животного."""
    sex = callback.data.split("_")[1]
    logger.debug(f"Пользователь {callback.from_user.id} выбрал пол {sex}.")
    await state.update_data(sex=Sex[sex].value)

    await callback.message.edit_reply_markup(
        reply_markup=build_choose_sex(Sex[sex]),
    )

    await ask_for_input_features(callback.message, state)


# * =============================== Ввод особенностей животного =============================== * #


async def ask_for_input_features(
    message: Message,
    state: FSMContext,
) -> None:
    """Запрашивает ввод особенностей животного."""
    await state.set_state(AnimalAddState.input_features)

    await message.answer(
        text="🦚 Введите особенности животного.",
        reply_markup=build_skip_cancel(
            skip_callback='input_transfer_photo',
        ),
    )


@router.message(AnimalAddState.input_features, F.text)
async def handle_st_input_features(
    message: Message,
    state: FSMContext,
) -> None:
    """Обработка ввода особенностей животного."""
    features = message.text.strip()
    logger.debug(f"Пользователь {message.from_user.id} ввёл особенности животного.")
    await state.update_data(features=features)

    await message.bot.edit_message_reply_markup(
        chat_id=message.chat.id,
        message_id=message.message_id - 1,
        reply_markup=None,
    )

    await ask_for_input_transfer_photo(message, state)


# * ================================ Добавление фото из приюта ================================ * #


async def ask_for_input_transfer_photo(
    message: Message,
    state: FSMContext,
) -> None:
    """Запрашивает фото из приюта."""
    await state.set_state(AnimalAddState.input_transfer_photo)

    await message.answer(
        text="📸 Отправьте фото животного, сделанное в приюте.",
        reply_markup=build_skip_cancel(
            skip_callback='input_transfer_date',
        ),
    )


@router.callback_query(F.data == 'input_transfer_photo')
async def handle_cb_input_transfer_photo(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработка ввода фото из приюта."""
    logger.debug(f"Пользователь {callback.from_user.id} перешёл к этапу отправки фото из приюта.")

    await callback.answer()
    await callback.message.delete()

    await ask_for_input_transfer_photo(callback.message, state)


@router.message(AnimalAddState.input_transfer_photo, F.photo)
async def handle_st_input_transfer_photo(
    message: Message,
    state: FSMContext,
) -> None:
    """Обработка фото животного из приюта."""
    logger.debug(f"Пользователь {message.from_user.id} отправил фото животного.")
    await state.update_data(transfer_photo=message.photo[-1].file_id)

    await message.bot.edit_message_reply_markup(
        chat_id=message.chat.id,
        message_id=message.message_id - 1,
        reply_markup=None,
    )
    await ask_for_input_transfer_date(message, state)


# * ========================= Добавление даты транспортировки в приют ========================= * #


async def ask_for_input_transfer_date(
    message: Message,
    state: FSMContext,
) -> None:
    """Запрашивает дату транспортировки в приют."""
    current_date = datetime.datetime.now(TZINFO).strftime("%Y-%m-%d %H:%M")

    await state.set_state(AnimalAddState.input_transfer_date)
    await state.update_data(transfer_date=current_date)

    await message.answer(
        text="📅 Введите дату транспортировки в приют в формате ГГГГ-ММ-ДД чч:мм",
        reply_markup=build_input_date(current_date, skip_callback='input_comment'),
    )


@router.callback_query(F.data == "input_transfer_date")
async def handle_cb_input_transfer_date(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработка ввода даты транспортировки в приют."""
    logger.debug(f"Пользователь {callback.from_user.id} перешёл к этапу ввода даты транспортировки в приют.")

    await callback.answer()
    await callback.message.delete()

    await ask_for_input_transfer_date(callback.message, state)


@router.callback_query(AnimalAddState.input_transfer_date, F.data == "input_current_date")
async def handle_st_input_transfer_date_cb_input_current_date(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработка выбора текущей даты."""
    logger.debug(f"Пользователь {callback.from_user.id} выбрал текущую дату.")

    await callback.answer()
    await callback.message.edit_reply_markup(
        reply_markup=None,
    )

    await ask_for_input_comment(callback.message, state)


@router.message(
    AnimalAddState.input_transfer_date,
    F.text.regexp(r"\d{4}-\d{2}-\d{1,2} \d{1,2}:\d{2}"),
)
async def handle_st_input_transfer_date(
    message: Message,
    state: FSMContext,
) -> None:
    """Обработка ввода даты транспортировки в приют."""
    catch_date = message.text
    logger.debug(f"Пользователь {message.from_user.id} ввёл дату транспортировки {catch_date}.")
    await state.update_data(catch_date=catch_date)

    await message.bot.edit_message_reply_markup(
        chat_id=message.chat.id,
        message_id=message.message_id - 1,
        reply_markup=None,
    )

    await ask_for_input_comment(message, state)


# * ================================= Добавление комментария ================================= * #


async def ask_for_input_comment(
    message: Message,
    state: FSMContext,
) -> None:
    """Запрашивает ввод комментарий."""
    await state.set_state(AnimalAddState.input_comment)

    await message.answer(
        text="💬 Введите комментарий с дополнительной информацией.",
        reply_markup=build_skip_cancel(
            skip_callback='confirmation',
        ),
    )


@router.callback_query(F.data == "input_comment")
async def handle_cb_input_comment(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработка ввода комментария."""
    logger.debug(f"Пользователь {callback.from_user.id} перешёл к этапу ввода комментария.")

    await callback.answer()
    await callback.message.delete()

    await ask_for_input_comment(callback.message, state)


@router.message(AnimalAddState.input_comment, F.text)
async def handle_st_input_comment(
    message: Message,
    state: FSMContext,
) -> None:
    """Обработка ввода комментария."""
    comment = message.text.strip()
    logger.debug(f"Пользователь {message.from_user.id} ввёл комментарий.")
    await state.update_data(comment=comment)

    await message.bot.edit_message_reply_markup(
        chat_id=message.chat.id,
        message_id=message.message_id - 1,
        reply_markup=None,
    )

    await ask_for_confirmation(message, state)


# * ================================== Сохранение животного ================================== * #


async def ask_for_confirmation(
    message: Message,
    state: FSMContext,
) -> None:
    """Запрашивает подтверждение сохранения животного."""
    await state.set_state(AnimalAddState.confirm)
    data = await state.get_data()
    data['created_by'] = message.from_user.id
    animal = AnimalRecordCreate(**data)

    text_list = []
    filled_fields = animal.model_dump(
        exclude_none=True,
        exclude={
            'catch_photo',
            'transfer_photo',
            'medical_photo',
            'created_at',
            'updated_at',
            'created_by',
        },
    )

    for field_name, value in filled_fields.items():
        title = AnimalRecordCreate.model_fields[field_name].title
        text_list.append(f"<b>{title}</b>: <code>{value}</code>")

    photos = MediaGroupBuilder()

    if animal.catch_photo:
        photos.add_photo(
            media=animal.catch_photo,
        )

    if animal.transfer_photo:
        photos.add_photo(
            media=animal.transfer_photo,
        )

    if animal.medical_photo:
        photos.add_photo(
            media=animal.medical_photo,
        )

    if animal.catch_photo or animal.transfer_photo or animal.medical_photo:
        await message.answer_media_group(
            media=photos.build(),
        )

    await message.answer(
        text=f"Проверьте введённые данные:\n\n{'\n'.join(text_list)}",
        reply_markup=build_confirm_cancel(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "confirmation")
async def handle_cb_confirmation(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработка подтверждения сохранения животного."""
    logger.debug(f"Пользователь {callback.from_user.id} перешёл к этапу подтверждения.")
    await callback.answer()
    await callback.message.delete()

    logger.debug(f"!!!!!!!!!!!!!!!!!!!!!!!!{callback.message}")
    await ask_for_confirmation(callback.message, state)


@router.callback_query(AnimalAddState.confirm, F.data == "confirm")
async def handle_cb_confirm(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработка подтверждения сохранения животного."""
    logger.debug(f"Пользователь {callback.from_user.id} подтвердил сохранение животного.")

    data = await state.get_data()
    data['created_by'] = callback.from_user.id
    animal = AnimalRecordCreate(**data)

    record = await add_animal_record(animal)

    await callback.answer()
    await callback.message.answer(
        text=f"✅ Животное {record.animal_type} успешно добавлено в базу данных."
    )
