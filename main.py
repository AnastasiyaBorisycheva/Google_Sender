"""
Главная точка входа в приложение.
АСИНХРОННАЯ ВЕРСИЯ (совместимая с Windows)
"""

import asyncio
import logging
import sys
import os

from config import config
from core.monitor import CellMonitor
from utils.logger import setup_logger


logger = setup_logger(level=config.LOG_LEVEL)


class Application:
    """Основное приложение."""
    
    def __init__(self):
        self.monitor = CellMonitor()
        self.running = False
        self._monitor_task = None
    
    async def start(self):
        """Запускает приложение."""
        self.running = True
        
        logger.info("="*50)
        logger.info("🚀 ЗАПУСК МОНИТОРИНГА GOOGLE SHEETS")
        logger.info("="*50)
        logger.info(f"📊 Ячейка: {config.MONITOR_CELL}")
        logger.info(f"⏱️  Интервал: {config.CHECK_INTERVAL_SECONDS} сек")
        logger.info(f"👤 Telegram ID: {config.TELEGRAM_USER_ID}")
        logger.info(f"📎 Таблица: {config.sheet_url}")
        logger.info("="*50)
        
        try:
            # Запускаем мониторинг
            self._monitor_task = asyncio.create_task(
                self.monitor.run_forever()
            )
            
            # Ждем завершения задачи (или Ctrl+C)
            await self._monitor_task
            
        except asyncio.CancelledError:
            logger.info("Задача мониторинга отменена")
        except Exception as e:
            logger.critical(f"Критическая ошибка: {e}", exc_info=True)
        finally:
            await self.stop()
    
    async def stop(self):
        """Останавливает приложение."""
        if not self.running:
            return
        
        logger.info("🛑 Остановка приложения...")
        self.running = False
        
        if self.monitor:
            self.monitor.stop()
        
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("👋 До свидания!")


async def main():
    """Точка входа."""
    app = Application()
    
    # Создаем задачу для мониторинга
    monitor_task = asyncio.create_task(app.start())
    
    # В Windows просто ждем с обработкой KeyboardInterrupt
    try:
        await monitor_task
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки (Ctrl+C)")
        await app.stop()
        # Отменяем все задачи
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                task.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Это на случай, если KeyboardInterrupt произошел до asyncio.run
        logger.info("Программа остановлена пользователем")
    except Exception as e:
        logger.critical(f"Необработанная ошибка: {e}", exc_info=True)