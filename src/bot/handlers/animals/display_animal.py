from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.media_group import MediaGroupBuilder
from loguru import logger

from bot.callback_factories import AnimalRecordCallbackFactory
from bot.keyboards.animals import display_paginator
from bot.logic import get_animal_display, get_user
from database.models import AnimalRecordRead

router = Router(name=__name__)


async def form_animal_record_text(
    animal_record: AnimalRecordRead,
) -> str:
    """Сформировать текст с информацией о животном."""
    animal = animal_record.model_dump(exclude_none=True)
    animal['created_by'] = await get_user(animal['created_by'])

    text = ""

    text += f"<b>{AnimalRecordRead.model_fields['created_by'].title}</b>: <code>{animal['created_by'].name}</code>\n"

    for field in ("animal_type", "breed", "sex", "color"):
        text += (
            f"<b>{AnimalRecordRead.model_fields[field].title}</b>: <code>{animal[field]}</code>\n"
        )

    if value := animal.get('features'):
        text += f"<b>{AnimalRecordRead.model_fields['features'].title}</b>: <code>{value}</code>\n"

    text += "\n"

    if value := animal.get('chip_id'):
        text += f"<b>{AnimalRecordRead.model_fields['chip_id'].title}</b>: <code>{value}</code>\n"

    for field in ("is_sterilized", "is_vaccinated"):
        text += (
            f"<b>{AnimalRecordRead.model_fields[field].title}</b>: "
            f"{'✅' if animal[field] else '❌'}\n"
        )

    text += "\n"

    for field in ("catch_date", "catch_place"):
        text += (
            f"<b>{AnimalRecordRead.model_fields[field].title}</b>: <code>{animal[field]}</code>\n"
        )

    text += "\n"

    if value := animal.get('transfer_date'):
        text += (
            f"<b>{AnimalRecordRead.model_fields['transfer_date'].title}</b>: <code>{value}</code>\n"
        )

    text += "\n"

    for field in ("return_date", "return_place"):
        if value := animal.get(field):
            text += f"<b>{AnimalRecordRead.model_fields[field].title}</b>: <code>{value}</code>\n"

    text += "\n"

    if value := animal.get('euthanasia_date'):
        text += f"<b>{AnimalRecordRead.model_fields['euthanasia_date'].title}</b>: <code>{value}</code>\n"

    if value := animal.get('comment'):
        text += f"<b>{AnimalRecordRead.model_fields['comment'].title}</b>: <code>{value}</code>\n"

    return text


async def send_animal_record(
    update: CallbackQuery | Message,
    state: FSMContext,
    animal_record: AnimalRecordRead,
    keyboard: InlineKeyboardMarkup | None = None,
):
    if isinstance(update, CallbackQuery):
        update.answer()
        message = update.message
    else:
        message = update

    photos = animal_record.model_dump(
        include={"catch_photo", "transfer_photo", "medical_photo"},
        exclude_none=True,
    )

    if photos:
        media = MediaGroupBuilder()

        for field, value in photos.items():
            if value:
                media.add_photo(
                    media=value,
                )

        media_msgs = await message.answer_media_group(
            media=media.build(),
        )

        await state.update_data(media=[msg.message_id for msg in media_msgs])

    await message.answer(
        text=await form_animal_record_text(animal_record),
        parse_mode="HTML",
        reply_markup=keyboard,
    )


@router.message(F.text == "🐾 Список животных")
async def handle_msg_animal_list(
    message: Message,
    state: FSMContext,
) -> None:
    """Обработка кнопки меню Список Животных."""

    logger.debug(f"Пользователь {message.from_user.id} запросил общий список животных.")
    await state.clear()

    animals = await get_animal_display(animal_id=None, user_filter=None)

    if animals['target'] is None:
        await message.answer("🙀 Список животных пуст.")
        return

    keyboard = display_paginator(
        title=animals['target'].model_dump(include={"id"})["id"],
        prev_item=None,
        next_item=animals['next'].model_dump(include={"id"})["id"] if animals['next'] else None,
    )

    await send_animal_record(
        message,
        state,
        animal_record=animals['target'],
        keyboard=keyboard,
    )


@router.callback_query(AnimalRecordCallbackFactory.filter(F.action == "display"))
async def handle_cb_animal_display(
    callback: CallbackQuery,
    callback_data: AnimalRecordCallbackFactory,
    state: FSMContext,
) -> None:
    """Обработка коллбека на отображение карточки животного."""
    animal_id = callback_data.item_id
    logger.debug(f"Пользователь {callback.from_user.id} запросил животное {animal_id}.")

    animals = await get_animal_display(animal_id=animal_id, user_filter=None)
    logger.debug(animals)

    if animals['target'] is None:
        await callback.answer("🙀 Запись не найдена.")
        return

    keyboard = display_paginator(
        title=animals['target'].model_dump(include={"id"})["id"],
        prev_item=animals['prev'].model_dump(include={"id"})["id"] if animals['prev'] else None,
        next_item=animals['next'].model_dump(include={"id"})["id"] if animals['next'] else None,
    )

    msgs = [callback.message.message_id]
    if media := await state.get_value('media'):
        msgs += media

    await callback.bot.delete_messages(
        callback.from_user.id,
        msgs,
    )

    await send_animal_record(
        callback,
        state,
        animal_record=animals['target'],
        keyboard=keyboard,
    )
