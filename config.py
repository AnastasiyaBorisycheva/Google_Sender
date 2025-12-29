"""
Конфигурация приложения с использованием Pydantic V2.
Все настройки загружаются из переменных окружения или .env файла.
"""

import os
import re
import warnings
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Основные настройки приложения.

    Pydantic V2 автоматически:
    1. Загружает значения из .env файла
    2. Приводит к правильным типам
    3. Проверяет обязательные поля
    4. Применяет валидаторы

    Обязательные поля (без значения по умолчанию):
    - TELEGRAM_BOT_TOKEN
    - TELEGRAM_USER_ID
    - SPREADSHEET_ID
    """

    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = Field(
        ...,
        min_length=10,
        description="Токен бота от @BotFather",
        examples=["1234567890:ABCdefGHIjklMnOpQRstUVwxyz"],
    )

    TELEGRAM_USER_ID: int = Field(
        ...,
        gt=0,
        description="ID пользователя для уведомлений",
        examples=[123456789]
    )

    # Google Sheets Configuration
    GOOGLE_CREDENTIALS_PATH: str = Field(
        "credentials.json",
        description="Путь к файлу credentials.json сервисного аккаунта",
    )

    SPREADSHEET_ID: str = Field(
        ...,
        min_length=5,
        description="ID Google таблицы (из URL: /d/SPREADSHEET_ID/edit)",
    )

    SHEET_NAME: str = Field(
        "Sheet1",
        description="Название листа для мониторинга"
    )

    MONITOR_CELL: str = Field(
        "C1",
        description="Ячейка для мониторинга в формате A1",
        pattern=r"^[A-Z]+[1-9]\d*$",
    )

    # Application Settings
    CHECK_INTERVAL_SECONDS: int = Field(
        30,
        ge=5,
        le=3600,
        description="Интервал проверки в секундах"
    )

    LOG_LEVEL: str = Field(
        "INFO",
        description="Уровень логирования",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
    )

    # Optional Settings
    GOOGLE_SHEET_URL: Optional[str] = Field(
        None,
        description=(
            "Ссылка на таблицу ",
            "(если не указана, сгенерируется автоматически)"
        ),
    )

    # Конфигурация Pydantic V2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # TELEGRAM_BOT_TOKEN = telegram_bot_token
        extra="ignore",  # Игнорировать лишние поля в .env
        validate_default=True,  # Валидировать значения по умолчанию
    )

    # Вычисляемые свойства
    @property
    def sheet_url(self) -> str:
        """
        URL таблицы.
        Генерируется автоматически если GOOGLE_SHEET_URL не указан.
        """
        if self.GOOGLE_SHEET_URL:
            return self.GOOGLE_SHEET_URL
        return f"https://docs.google.com/spreadsheets/d/{self.SPREADSHEET_ID}"

    # Валидаторы Pydantic V2
    @field_validator("GOOGLE_CREDENTIALS_PATH")
    @classmethod
    def validate_credentials_file(cls, v: str) -> str:
        """
        Проверяет существование файла credentials.json.

        Raises:
            ValueError: Если файл не найден
        """
        if not os.path.exists(v):
            raise ValueError(
                f"Файл {v} не найден. "
                f"Создайте сервисный аккаунт в Google Cloud."
            )
        return v

    @field_validator("MONITOR_CELL", mode="after")
    @classmethod
    def validate_cell_format(cls, v: str) -> str:
        """
        Проверяет формат ячейки (например, C1, AA100).

        Args:
            v: Значение ячейки для проверки

        Returns:
            Проверенное значение

        Raises:
            ValueError: Если формат неверный
        """
        # Более строгая проверка чем простой regex
        cell_pattern = re.compile(r"^[A-Z]{1,3}[1-9][0-9]*$")
        if not cell_pattern.match(v):
            raise ValueError(
                f"Неверный формат ячейки: '{v}'. "
                f"Используйте формат A1, B2, AA100 и т.д."
            )
        return v

    @field_validator("CHECK_INTERVAL_SECONDS", mode="after")
    @classmethod
    def validate_interval(cls, v: int) -> int:
        """
        Проверяет интервал проверки.
        Выводит предупреждение при слишком частых проверках.

        Args:
            v: Интервал в секундах

        Returns:
            Проверенный интервал
        """
        if v < 30:
            warnings.warn(
                f"Интервал {v} секунд может превысить квоты Google API "
                f"(60 запросов в минуту на пользователя). "
                f"Рекомендуется интервал от 30 секунд.",
                UserWarning,
                stacklevel=2,
            )
        return v

    @field_validator("TELEGRAM_BOT_TOKEN", mode="after")
    @classmethod
    def validate_token_format(cls, v: str) -> str:
        """
        Базовая проверка формата токена Telegram.

        Telegram токен обычно имеет формат:
            1234567890:ABCdefGHIjklMnOpQRstUVwxyz
        """
        if ":" not in v:
            warnings.warn(
                "Telegram токен должен содержать ':' "
                "(обычный формат: bot_token:abc123)",
                UserWarning,
                stacklevel=2,
            )
        return v


def load_config() -> Settings:
    """
    Загружает конфигурацию и выполняет начальную проверку.

    Returns:
        Settings: Загруженная и проверенная конфигурация

    Raises:
        ValidationError: Если конфигурация невалидна
    """
    try:
        config = Settings()
        print("✅ Конфигурация успешно загружена")
        return config
    except Exception as e:
        print("❌ Ошибка загрузки конфигурации:")
        print(f"   {type(e).__name__}: {e}")
        print("\n📋 Проверьте:")
        print("   1. Существует ли файл .env в корне проекта?")
        print("   2. Скопировали ли вы .env.example в .env?")
        print("   3. Заполнили ли вы все обязательные поля?")
        print("   4. Правильные ли типы данных?")
        print("\nОбязательные поля в .env:")
        print("   TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID, SPREADSHEET_ID")
        raise


# Для удобного импорта в других модулях
# Используйте: from config import config
config = load_config()


if __name__ == "__main__":
    """
    Тестирование конфигурации.
    Запустите: python config.py

    Эта функция проверяет:
    1. Загрузку из .env
    2. Валидацию полей
    3. Вычисляемые свойства
    """

    print("\n" + "=" * 50)
    print("ТЕСТ КОНФИГУРАЦИИ PYDANTIC V2")
    print("=" * 50)

    # Показываем загруженные настройки (без секретов)
    print("\n📱 Telegram Configuration:")
    token_preview = (
        f"{config.TELEGRAM_BOT_TOKEN[:10]}..."
        if config.TELEGRAM_BOT_TOKEN
        else "❌ Нет токена"
    )
    print(f"   • Бот токен: {token_preview}")
    print(f"   • User ID: {config.TELEGRAM_USER_ID}")

    print("\n📊 Google Sheets Configuration:")
    print(f"   • Таблица ID: {config.SPREADSHEET_ID[:20]}...")
    print(f"   • Лист: {config.SHEET_NAME}")
    print(f"   • Ячейка: {config.MONITOR_CELL}")
    credentials_exists = (
        "✅ Файл найден"
        if os.path.exists(config.GOOGLE_CREDENTIALS_PATH)
        else "❌ Файл не найден"
    )
    print(f"   • Credentials: {credentials_exists}")

    print("\n⚙️  Application Settings:")
    print(f"   • Интервал: {config.CHECK_INTERVAL_SECONDS} секунд")
    print(f"   • Логирование: {config.LOG_LEVEL}")
    print(f"   • Ссылка на таблицу: {config.sheet_url}")

    print("\n🔧 Pydantic V2 Features:")
    print(f"   • Модель конфигурации: {config.model_config}")
    print(f"   • Поля модели: {list(Settings.model_fields.keys())}")

    print("\n✅ Все проверки пройдены!")
    print("   Конфигурация готова к использованию.")
