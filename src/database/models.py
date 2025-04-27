import abc
import datetime
import enum
from typing import Annotated

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer

from utils import get_utc_now

TgFileID = str
TgUserID = Annotated[int, Field(gt=0)]


class MongoBase(BaseModel, abc.ABC):
    """Абстрактная модель для документов MongoDB."""

    model_config = ConfigDict(use_enum_values=True)


class MongoRead(MongoBase, abc.ABC):
    """Абстрактная модель для чтения документов MongoDB."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

    id: ObjectId = Field(alias="_id")
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @field_serializer('id')
    @classmethod
    def serialize_objectid(cls, v):
        return str(v)


class MongoCreate(MongoBase, abc.ABC):
    """Абстрактная модель для создания документов MongoDB."""

    created_at: datetime.datetime = Field(
        default_factory=get_utc_now,
        title="Дата создания записи",
    )
    updated_at: datetime.datetime = Field(
        default_factory=get_utc_now,
        title="Дата последнего обновления записи",
    )


class MongoUpdate(MongoBase, abc.ABC):
    """Абстрактная модель для обновления документов MongoDB."""

    updated_at: datetime.datetime = Field(
        default_factory=get_utc_now,
        title="Дата создания записи",
    )


class AccessRole(enum.StrEnum):
    """Роли доступа."""

    ADMIN = "admin"
    CATHER = "catcher"
    GUEST = "guest"


class UserBase(MongoBase):
    """Модель для пользователя."""

    tg_id: TgUserID
    name: str
    access_role: AccessRole


class UserRead(UserBase, MongoRead):
    """Модель для чтения пользователя."""

    pass


class UserCreate(UserBase, MongoCreate):
    """Модель для чтения пользователя."""

    pass


class UserUpdate(MongoUpdate):
    """Модель для чтения пользователя."""

    access_role: AccessRole | None = None


class AnimalType(enum.StrEnum):
    """Тип животного."""

    CAT = "Кошка"
    DOG = "Собака"
    OTHER = "Другое"


class Sex(enum.StrEnum):
    """Пол животного."""

    MALE = "Самец"
    FEMALE = "Самка"
    UNKNOWN = "Неопределенно"


class AnimalRecordBase(MongoBase):
    """Базовая модель для записи о животном."""

    chip_id: str | None = Field(
        None,
        title="ID чипа",
    )
    medical_photo: TgFileID | None = Field(
        None,
        title="Фото из медкарты",
    )

    catch_photo: TgFileID | None = Field(
        None,
        title="Фото отлова",
    )

    transfer_date: datetime.datetime | None = Field(
        None,
        title="Дата передачи в приют",
    )
    transfer_photo: TgFileID | None = Field(
        None,
        title="Фото при передаче в приют",
    )

    return_date: datetime.datetime | None = Field(
        None,
        title="Дата выпуска",
    )
    return_place: str | None = Field(
        None,
        title="Место выпуска ",
    )

    euthanasia_date: datetime.datetime | None = Field(
        None,
        title="Дата эвтаназии",
    )
    comment: str | None = Field(
        None,
        title="Комментарий",
    )


class AnimalRecordRead(AnimalRecordBase, MongoRead):
    """Модель для чтения записи о животном."""

    animal_type: AnimalType = Field(
        title="Вид животного",
    )
    sex: Sex = Field(
        title="Пол",
    )
    breed: str = Field(
        title="Порода",
    )
    color: str = Field(
        title="Окрас",
    )
    features: str = Field(
        title="Особенности",
    )

    is_sterilized: bool = Field(
        False,
        title="Стерилизовано",
    )
    is_vaccinated: bool = Field(
        False,
        title="Вакцинировано",
    )

    catch_date: datetime.datetime = Field(
        title="Дата отлова",
    )
    catch_place: str = Field(
        title="Место отлова",
    )


class AnimalRecordCreate(AnimalRecordBase, MongoCreate):
    """Модель для создания записи о животном."""

    animal_type: AnimalType = Field(
        title="Вид животного",
    )
    sex: Sex = Field(
        title="Пол",
    )
    breed: str = Field(
        title="Порода",
    )
    color: str = Field(
        title="Окрас",
    )
    features: str = Field(
        title="Особенности",
    )

    is_sterilized: bool = Field(
        False,
        title="Стерилизовано",
    )
    is_vaccinated: bool = Field(
        False,
        title="Вакцинировано",
    )

    catch_date: datetime.datetime = Field(
        title="Дата отлова",
    )
    catch_place: str = Field(
        title="Место отлова",
    )


class AnimalRecordUpdate(AnimalRecordBase, MongoUpdate):
    """Модель для обновления записи о животном."""

    animal_type: AnimalType | None = Field(
        None,
        title="Вид животного",
    )
    sex: Sex | None = Field(
        None,
        title="Пол",
    )
    breed: str | None = Field(
        None,
        title="Порода",
    )
    color: str | None = Field(
        None,
        title="Окрас",
    )
    features: str | None = Field(
        None,
        title="Особенности",
    )

    is_sterilized: bool | None = Field(
        None,
        title="Стерилизовано",
    )
    is_vaccinated: bool | None = Field(
        None,
        title="Вакцинировано",
    )

    catch_date: datetime.datetime | None = Field(
        None,
        title="Дата отлова",
    )
    catch_place: str | None = Field(
        None,
        title="Место отлова",
    )
