import datetime

import settings


def get_utc_now() -> datetime.datetime:
    """Ленивая функция для получения текущего времени в UTC."""
    return datetime.datetime.now(datetime.UTC)


def generate_invite_link(password: str) -> str:
    """Генерирует ссылку для приглашения."""
    return f"https://t.me/{settings.tg.bot_username}?start={password}"
