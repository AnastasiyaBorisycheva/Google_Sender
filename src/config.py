"""
Загрузка и валидация конфигурации из .env
"""

import json
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, model_validator


class Settings(BaseSettings):
    # Telegram
    TELEGRAM_BOT_TOKEN: str = Field(..., min_length=10)
    ADMIN_USER_ID: int = Field(..., gt=0)
    USERS_IDS: List[int]  # список всех, кто получает уведомления

    # Google Sheets
    GOOGLE_SHEETS_CREDENTIALS: str = "credentials.json"
    SPREADSHEET_ID: str = Field(..., min_length=5)
    SHEET_NAME: str = "2026"
    MONITOR_CELL: str = "C1"

    # Столбцы
    DATE_COLUMN: str = "B"
    PAIN_COLUMN: str = "C"
    MEDICATION_COLUMN: str = "D"

    # Мониторинг (для фоновой проверки)
    CHECK_INTERVAL: int = Field(60, ge=10, le=3600)
    LOG_LEVEL: str = "INFO"

    # PostgreSQL
    DB_USER: str = Field(..., min_length=1)
    DB_PASSWORD: str = Field(..., min_length=1)
    DB_HOST: str = Field("localhost", min_length=1)
    DB_PORT: str = Field("5432", min_length=1)
    DB_NAME: str = Field(..., min_length=1)

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # имена переменных чувствительны к регистру
        extra="ignore",  # игнорировать лишние поля в .env
    )

    @field_validator("USERS_IDS", mode="before")
    @classmethod
    def parse_users_ids(cls, v):
        """
        Преобразует строку из .env в список int.
        Пример: "[595921273, 111, 222]" → [595921273, 111, 222]
        """

        # Если уже список, возвращаем как есть
        if isinstance(v, list):
            return v

        # Если строка, парсим JSON
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [int(item) for item in parsed]
            except json.JSONDecodeError:
                pass

        return []

    @model_validator(mode="after")
    def validate_admin_in_users(self) -> "Settings":
        """Проверяет, что ADMIN_USER_ID есть в списке USERS_IDS"""
        if self.ADMIN_USER_ID not in self.USERS_IDS:
            print(
                f"ВНИМАНИЕ: ADMIN_USER_ID={self.ADMIN_USER_ID} отсутствует в USERS_IDS"
            )
            print(f"Добавьте его вручную в .env: USERS_IDS=[{self.ADMIN_USER_ID}, ...]")
            print(f"Пока что админ не будет получать уведомления через notifier")
        return self


def load_config() -> Settings:
    """Загружает и возвращает конфигурацию"""
    try:
        config = Settings()
        print("✅ Конфигурация загружена")

        # Выводим информацию для проверки (без токена)
        print(f"Admin ID: {config.ADMIN_USER_ID}")
        print(f"Users для уведомлений: {config.USERS_IDS}")
        print(f"Таблица: {config.SPREADSHEET_ID[:10]}...")
        print(f"Интервал: {config.CHECK_INTERVAL} сек")

        return config
    except Exception as e:
        print(f"Ошибка загрузки конфигурации: {e}")
        raise


# Глобальный экземпляр
config = load_config()


if __name__ == "__main__":
    """Тест конфигурации: python -m src.config"""
    print("\n" + "=" * 50)
    print("ТЕСТ КОНФИГУРАЦИИ")
    print("=" * 50)
    print(f"ADMIN_USER_ID: {config.ADMIN_USER_ID}")
    print(f"USERS_IDS: {config.USERS_IDS}")
    print(f"type(USERS_IDS): {type(config.USERS_IDS)}")
    print(f"SHEET_NAME: {config.SHEET_NAME}")
    print(f"CHECK_INTERVAL: {config.CHECK_INTERVAL}")
