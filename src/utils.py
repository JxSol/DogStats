import datetime


def get_utc_now() -> datetime.datetime:
    """Ленивая функция для получения текущего времени в UTC."""
    return datetime.datetime.now(datetime.UTC)
