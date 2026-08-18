"""
Точка входа — запуск Telegram бота (без фонового мониторинга)
"""

import asyncio
import sys

from src.config import config
from src.sheets import async_sheet_client
from src.bot import PainBot
from src.logger import setup_logger


logger = setup_logger(name=__name__, log_file='debug.log')


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
    await async_sheet_client.initialize()
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
