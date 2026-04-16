"""
Загрузка и валидация конфигурации из .env
"""

import json
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,  # имена переменных чувствительны к регистру
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

        # Если ничего не подошло, возвращаем пустой список
        return []

    @field_validator("ADMIN_USER_ID", mode="after")
    @classmethod
    def validate_admin_in_users(cls, v, info):
        """
        Проверяет, что ADMIN_USER_ID есть в списке USERS_IDS
        """
        users_ids = info.data.get("USERS_IDS", [])
        if v not in users_ids:
            # Можно добавить админа в список автоматически
            # Но лучше предупредить
            print(f"ВНИМАНИЕ: ADMIN_USER_ID={v} отсутствует в USERS_IDS")
            print(f"Добавьте его вручную в .env: USERS_IDS=[{v}, ...]")
        return v


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
