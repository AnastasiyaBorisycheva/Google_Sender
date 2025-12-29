"""
Настройка логирования для приложения.
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str = "sheets_monitor",
    level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Настраивает и возвращает логгер.

    Args:
        name: Имя логгера
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Путь к файлу для записи логов (опционально)

    Returns:
        Настроенный логгер
    """
    # Создаем логгер
    logger = logging.getLogger(name)

    # Устанавливаем уровень
    log_level = getattr(logging, level.upper())
    logger.setLevel(log_level)

    # Проверяем, нет ли уже обработчиков (чтобы не дублировать)
    if logger.handlers:
        return logger

    # Форматтер для сообщений
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%d.%m.%Y %H:%M:%S",
    )

    # Обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Обработчик для файла (если указан)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Глобальный логгер для импорта
logger = setup_logger()


if __name__ == "__main__":
    """Тестирование логирования"""
    logger.debug("Это сообщение уровня DEBUG")
    logger.info("Это сообщение уровня INFO")
    logger.warning("Это сообщение уровня WARNING")
    logger.error("Это сообщение уровня ERROR")
    logger.critical("Это сообщение уровня CRITICAL")

    print("\n✅ Логгер настроен правильно!")
