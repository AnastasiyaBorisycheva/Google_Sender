"""
Точка входа — запуск Telegram бота (без фонового мониторинга)
"""

import asyncio
import logging
import sys

from src.config import config
from src.sheets import sheets_client
from src.bot import PainBot


# Настройка логирования
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


async def main():
    """Запуск бота"""
    
    logger.info("=" * 50)
    logger.info("ЗАПУСК МЕДИЦИНСКОГО ДНЕВНИКА")
    logger.info("=" * 50)
    logger.info(f"Admin ID: {config.ADMIN_USER_ID}")
    logger.info(f"Users для уведомлений: {config.USERS_IDS}")
    logger.info(f"Таблица: {config.SPREADSHEET_ID[:10]}...")
    logger.info("=" * 50)

    # 1. Инициализация Google Sheets (один раз при старте)
    logger.info("Инициализация Google Sheets...")
    sheets_client.initialize()
    logger.info("Google Sheets готов")

    # 2. Создаем и запускаем бота
    bot = PainBot()

    try:
        logger.info("Бот запущен. Жду команды...")
        await bot.start_polling()
    except KeyboardInterrupt:
        logger.info("Остановка по Ctrl+C")
    finally:
        await bot.stop()
        logger.info("До свидания!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
