"""
Мониторинг изменений в Google Sheets и отправка уведомлений.
АСИНХРОННАЯ ВЕРСИЯ
"""

import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from config import config
from services.google_sheets import get_sheets_service, GoogleSheetsError
from bot.notification import get_bot, TelegramError


logger = logging.getLogger(__name__)


class MonitorError(Exception):
    """Базовое исключение для ошибок мониторинга"""
    pass


class CellMonitor:
    """
    Мониторит изменения в ячейке Google Sheets и отправляет уведомления.
    Асинхронная версия.
    """
    
    def __init__(self, state_file: str = "storage/state.json"):
        """
        Args:
            state_file: Файл для хранения последнего значения
        """
        self.sheets = get_sheets_service()
        self.bot = get_bot()
        self.cell = config.MONITOR_CELL
        self.interval = config.CHECK_INTERVAL_SECONDS
        self.state_file = Path(state_file)
        self.last_value: Optional[Any] = None
        self.last_check: Optional[datetime] = None
        self.running = False
        
        # Создаем папку для state если нет
        self.state_file.parent.mkdir(exist_ok=True)
    
    def load_state(self) -> None:
        """
        Загружает последнее сохраненное значение из файла.
        (Синхронный - работа с файлом)
        """
        if not self.state_file.exists():
            logger.info("Файл состояния не найден. Начинаем с чистого листа.")
            return
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.last_value = data.get('last_value')
                logger.info(f"📂 Загружено последнее значение: {self.last_value}")
        except Exception as e:
            logger.warning(f"Не удалось загрузить состояние: {e}")
    
    def save_state(self) -> None:
        """
        Сохраняет текущее значение в файл.
        (Синхронный - работа с файлом)
        """
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'last_value': self.last_value,
                    'last_check': datetime.now().isoformat() if self.last_check else None
                }, f, indent=2, ensure_ascii=False)
            logger.debug(f"💾 Сохранено значение: {self.last_value}")
        except Exception as e:
            logger.error(f"Не удалось сохранить состояние: {e}")
    
    def values_are_different(self, old: Any, new: Any) -> bool:
        """
        Сравнивает два значения.
        """
        # Приводим к строкам для сравнения
        old_str = str(old).strip() if old is not None else ""
        new_str = str(new).strip() if new is not None else ""
        
        # Пробуем сравнить как числа
        try:
            old_num = float(old_str) if old_str else None
            new_num = float(new_str) if new_str else None
            
            if old_num is not None and new_num is not None:
                return old_num != new_num
        except ValueError:
            pass  # Не числа, сравниваем как строки
        
        return old_str != new_str
    
    def format_change_message(self, old: Any, new: Any) -> str:
        """
        Форматирует сообщение об изменении.
        """
        old_str = str(old) if old is not None else "пусто"
        new_str = str(new) if new is not None else "пусто"
        
        # Пробуем вычислить разницу для чисел
        diff_text = ""
        try:
            old_num = float(old) if old else 0
            new_num = float(new) if new else 0
            diff = new_num - old_num
            if diff != 0:
                diff_text = f"\n• Изменение: {'+' if diff > 0 else ''}{diff:.2f}"
        except (ValueError, TypeError):
            pass
        
        return (
            f"🔔 <b>Изменение в Google Sheets!</b>\n"
            f"──────────────\n"
            f"• Ячейка: <code>{self.cell}</code>\n"
            f"• Было: {old_str}\n"
            f"• Стало: {new_str}{diff_text}\n"
            f"• Время: {datetime.now().strftime('%H:%M:%S')}\n"
            f"• Таблица: {config.sheet_url}"
        )
    
    async def check_cell(self) -> bool:
        """
        Асинхронно проверяет ячейку на изменения.
        
        Returns:
            True если были изменения и отправлено уведомление
        """
        try:
            # Инициализируем сервисы если нужно
            if not self.sheets._initialized:
                # sheets у нас пока синхронный, но initialize() синхронный
                self.sheets.initialize()
            
            if not self.bot._initialized:
                self.bot.initialize()
            
            # Читаем текущее значение
            current_value = self.sheets.get_cell_value(self.cell)
            self.last_check = datetime.now()
            
            logger.debug(f"Текущее значение: {current_value}")
            
            # Сравниваем с последним
            if self.last_value is None:
                # Первый запуск - просто запоминаем
                logger.info(f"Первое значение: {current_value}")
                self.last_value = current_value
                self.save_state()
                return False
            
            if self.values_are_different(self.last_value, current_value):
                # Значение изменилось!
                logger.info(f"🔄 Изменение: {self.last_value} → {current_value}")
                
                # Отправляем уведомление (АСИНХРОННО!)
                message = self.format_change_message(self.last_value, current_value)
                await self.bot.send_notification(message)  # ✅ Вот здесь был await!
                
                # Обновляем состояние
                self.last_value = current_value
                self.save_state()
                return True
            else:
                logger.debug("Значение не изменилось")
                return False
                
        except GoogleSheetsError as e:
            logger.error(f"Ошибка Google Sheets: {e}")
            return False
        except TelegramError as e:
            logger.error(f"Ошибка Telegram: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}", exc_info=True)
            return False
    
    async def run_once(self) -> None:
        """
        Однократная проверка (для тестирования).
        """
        logger.info(f"🔍 Проверка ячейки {self.cell}...")
        changed = await self.check_cell()
        if changed:
            logger.info("✅ Уведомление отправлено")
        else:
            logger.info("⏭️ Изменений нет")
    
    async def run_forever(self) -> None:
        """
        Бесконечный асинхронный цикл мониторинга.
        """
        self.running = True
        logger.info(f"🚀 Запуск мониторинга ячейки {self.cell}")
        logger.info(f"⏱️ Интервал проверки: {self.interval} сек")
        
        # Загружаем последнее состояние
        self.load_state()
        
        # Отправляем приветствие (АСИНХРОННО!)
        await self.bot.send_notification(
            f"🚀 <b>Мониторинг запущен!</b>\n"
            f"• Ячейка: {self.cell}\n"
            f"• Интервал: {self.interval} сек"
        )
        
        check_count = 0
        error_count = 0
        
        while self.running:
            try:
                check_count += 1
                logger.info(f"📊 Проверка #{check_count}")
                
                changed = await self.check_cell()
                
                if changed:
                    error_count = 0
                else:
                    error_count = 0
                
                # Асинхронное ожидание
                logger.info(f"⏳ Ожидание {self.interval} сек...")
                await asyncio.sleep(self.interval)
                
            except asyncio.CancelledError:
                logger.info("🛑 Задача мониторинга отменена")
                break
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Ошибка в цикле мониторинга: {e}")
                
                if error_count >= 3:
                    logger.critical("⚠️ Слишком много ошибок подряд. Остановка.")
                    await self.bot.send_notification(
                        "⚠️ <b>Мониторинг остановлен из-за ошибок</b>"
                    )
                    break
                
                # При ошибке ждем дольше
                logger.info(f"⏳ Ожидание 60 сек перед повтором...")
                await asyncio.sleep(60)
    
    def stop(self) -> None:
        """
        Останавливает мониторинг.
        """
        self.running = False
        logger.info("🛑 Мониторинг остановлен")
        
        # Сохраняем состояние на всякий случай
        self.save_state()


# Для тестирования
async def test_monitor():
    """
    Тест мониторинга (однократная проверка).
    Запустите: python -m core.monitor
    """
    print("\n" + "="*50)
    print("ТЕСТ МОНИТОРИНГА")
    print("="*50)
    
    monitor = CellMonitor()
    
    print(f"\n1. Ячейка для мониторинга: {monitor.cell}")
    print(f"2. Интервал: {monitor.interval} сек")
    
    print("\n3. Загрузка предыдущего состояния...")
    monitor.load_state()
    print(f"   Последнее значение: {monitor.last_value}")
    
    print("\n4. Проверка текущего значения...")
    await monitor.run_once()
    
    print("\n✅ Тест завершен")


if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    asyncio.run(test_monitor())