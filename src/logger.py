"""
Настройка логирования для приложения.
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str = __name__,  # Используем имя текущего модуля
    level: str = "INFO",
    log_file: Optional[str] = None,
) -> logging.Logger:
    logger = logging.getLogger(name)

    log_level = getattr(logging, level.upper())
    logger.setLevel(log_level)

    # 1. Запрещаем передачу логов корневому (root) логгеру, чтобы исключить дублирование
    logger.propagate = False

    # 2. Если хендлеры уже настроены — возвращаем логгер
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%d.%m.%Y %H:%M:%S",
    )

    # Консольный хендлер (уровень наследуется от logger)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Файловый хендлер (опционально)
    if log_file:
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Глобальный логгер для импорта в проекте
logger = setup_logger(level="DEBUG", log_file="debug.log")


if __name__ == "__main__":
    # Тестирование логирования
    logger.debug("Это сообщение уровня DEBUG")
    logger.info("Это сообщение уровня INFO")
    logger.warning("Это сообщение уровня WARNING")
    logger.error("Это сообщение уровня ERROR")
    logger.critical("Это сообщение уровня CRITICAL")

    print("\nЛоггер настроен правильно!")