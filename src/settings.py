from typing import ClassVar

from pydantic import MongoDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    """Общие настройки для всего приложения."""

    model_config = SettingsConfigDict(
        env_file='../.env',  # ! Приоритет у переменных среды!
        env_file_encoding='utf-8',
        env_ignore_empty=True,
        extra='ignore',
    )


class DatabaseSettings(BaseConfig):
    """Настройки локальной базы данных."""

    model_config = SettingsConfigDict(env_prefix='db_')

    scheme: ClassVar[str] = 'mongodb'

    host: str = 'localhost'
    port: int = 27017
    user: str
    password: str

    @property
    def db_dsn(self) -> str:
        return MongoDsn.build(
            scheme=self.scheme,
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
        ).unicode_string()


class TelegramSettings(BaseConfig):
    """Настройки Telegram."""

    model_config = SettingsConfigDict(env_prefix='tg_')

    bot_token: str
    bot_username: str
    admin_ids: list[int]


db = DatabaseSettings()
tg = TelegramSettings()
