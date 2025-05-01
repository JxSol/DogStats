from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.keyboards.basic import build_skip_cancel, cancel_builder
from database.models import AnimalType, Sex


def geo_button() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    geo_btn = KeyboardButton(
        text="📍 Отправить геолокацию",
        request_location=True,
    )

    builder.add(geo_btn)

    return builder.as_markup(one_time_keyboard=True)


def build_input_date(current_dt: str, skip_callback: str | None = None) -> InlineKeyboardMarkup:
    """Формирует клавиатуру для ввода даты отлова."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=f"📆 Вставить {current_dt}",
        callback_data="input_current_date",
    )

    if skip_callback:
        btns = build_skip_cancel(skip_callback=skip_callback).inline_keyboard[0]
        builder.add(*btns)
        builder.adjust(1, 2)
    else:
        builder.attach(cancel_builder())
        builder.adjust(1)

    return builder.as_markup()


def build_choose_animal_type(selected: AnimalType | None = None) -> InlineKeyboardMarkup:
    """Формирует клавиатуру выбора типа животного."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=f"🐕 {'✅' if selected == AnimalType.DOG else AnimalType.DOG}",
        callback_data=f"animal_type_{AnimalType.DOG.name}",
    )
    builder.button(
        text=f"🐈 {'✅' if selected == AnimalType.CAT else AnimalType.CAT}",
        callback_data=f"animal_type_{AnimalType.CAT.name}",
    )
    builder.button(
        text=f"🦕 {'✅' if selected == AnimalType.OTHER else AnimalType.OTHER}",
        callback_data=f"animal_type_{AnimalType.OTHER.name}",
    )

    if selected is None:
        builder.attach(cancel_builder())

    builder.adjust(3, 1)
    return builder.as_markup()


def build_choose_sex(selected: Sex | None = None) -> InlineKeyboardMarkup:
    """Формирует клавиатуру выбора пола животного."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=f"♂️ {'✅' if selected == Sex.MALE else Sex.MALE}",
        callback_data=f"sex_{Sex.MALE.name}",
    )
    builder.button(
        text=f"♀️ {'✅' if selected == Sex.FEMALE else Sex.FEMALE}",
        callback_data=f"sex_{Sex.FEMALE.name}",
    )
    builder.button(
        text=f"❔ {'✅' if selected == Sex.UNDEFINED else Sex.UNDEFINED}",
        callback_data=f"sex_{Sex.UNDEFINED.name}",
    )

    if selected is None:
        builder.attach(cancel_builder())

    builder.adjust(3, 1)
    return builder.as_markup()
