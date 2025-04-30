################################################################
#                         Этап сборки
################################################################

FROM python:3.13-bullseye AS build
LABEL authors="JxSol"

# Настройки Python
ENV \
  # Запрещает питону создавать внутри контейнера файлы с кэшем
  PYTHONDONTWRITEBYTECODE=1 \
  # Запрещает буферизировать stdout
  PYTHONUNBUFFERED=1 \
  # Выводит трассировку стека в случае segfault
  PYTHONFAULTHANDLER=1 \
  # Запрещает проверять установленную версию pip
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  # Устанавливает таймаут ожидания соединения для pip
  PIP_DEFAULT_TIMEOUT=60

# Устанавливаем Poetry
RUN pip install poetry==2.1.0

# Настройки Poetry
ENV \
  # Запрещает задавать интерактивные вопросы во время установки
  POETRY_NO_INTERACTION=1 \
  # Разрешает создавать виртуальное окружение внутри проекта
  POETRY_VIRTUALENVS_IN_PROJECT=1 \
  # Разрешает создавать окружение, если оно не было найдено
  POETRY_VIRTUALENVS_CREATE=1 \
  # Устанавливает директорию для кэша
  POETRY_CACHE_DIR="/tmp/poetry_cache"

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml ./

# Устанавливаем зависимости, используя кэш для ускорения сборки
RUN poetry --version
RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

################################################################
#                       Основной этап
################################################################

FROM python:3.13-slim AS stage

WORKDIR /app

# Настройки venv
ENV \
  VIRTUAL_ENV="/app/.venv" \
  PATH="/app/.venv/bin:$PATH"

# Копируем виртуальное окружение с предыдущего этапа
COPY --from=build ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Копируем файлы проекта
COPY src .

CMD ["python", "main.py"]