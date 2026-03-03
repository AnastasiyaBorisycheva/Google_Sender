"""
Telegram бот для отправки уведомлений о изменениях в Google Sheets.
Использует aiogram 3.x.
"""

import logging
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
import asyncio

from config import config


logger = logging.getLogger(__name__)


class TelegramError(Exception):
    """Базовое исключение для ошибок Telegram"""
    pass


class NotificationBot:
    """
    Бот для отправки уведомлений в Telegram.
    """
    
    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        self.user_id = config.TELEGRAM_USER_ID
        self.bot: Optional[Bot] = None
        self.dp: Optional[Dispatcher] = None
        self._initialized = False
    
    def initialize(self) -> None:
        """
        Инициализирует бота.
        """
        if self._initialized:
            return
        
        logger.info("🤖 Инициализация Telegram бота...")
        
        try:
            # Создаем экземпляр бота
            self.bot = Bot(token=self.token)
            self.dp = Dispatcher()
            
            # Регистрируем обработчики команд
            self._register_handlers()
            
            self._initialized = True
            logger.info(f"✅ Бот инициализирован для user_id: {self.user_id}")
            
        except Exception as e:
            error_msg = f"Ошибка инициализации бота: {e}"
            logger.error(error_msg)
            raise TelegramError(error_msg) from e
    
    def _register_handlers(self) -> None:
        """
        Регистрирует обработчики команд.
        """
        if not self.dp:
            return
        
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message):
            """Обработчик команды /start"""
            logger.info(f"Команда /start от user {message.from_user.id}")
            
            # Проверяем, что это нужный пользователь
            if message.from_user.id != self.user_id:
                await message.answer("⛔ У вас нет доступа к этому боту.")
                return
            
            await message.answer(
                f"👋 Привет! Я бот для мониторинга Google Sheets.\n\n"
                f"📊 Отслеживаю ячейку: {config.MONITOR_CELL}\n"
                f"⏱️ Интервал проверки: {config.CHECK_INTERVAL_SECONDS} сек\n"
                f"📎 Таблица: {config.sheet_url}\n\n"
                f"При изменениях в ячейке {config.MONITOR_CELL} "
                f"я пришлю уведомление."
            )
        
        @self.dp.message(Command("status"))
        async def cmd_status(message: Message):
            """Обработчик команды /status"""
            logger.info(f"Команда /status от user {message.from_user.id}")
            
            if message.from_user.id != self.user_id:
                await message.answer("⛔ Нет доступа.")
                return
            
            await message.answer(
                f"📊 <b>Статус мониторинга</b>\n"
                f"──────────────\n"
                f"• Таблица: активна\n"
                f"• Ячейка: {config.MONITOR_CELL}\n"
                f"• Интервал: {config.CHECK_INTERVAL_SECONDS} сек\n"
                f"• Бот: работает",
                parse_mode="HTML"
            )
        
        @self.dp.message(Command("help"))
        async def cmd_help(message: Message):
            """Обработчик команды /help"""
            if message.from_user.id != self.user_id:
                await message.answer("⛔ Нет доступа.")
                return
            
            await message.answer(
                "📋 <b>Доступные команды</b>\n"
                "──────────────\n"
                "/start - начать работу\n"
                "/status - статус мониторинга\n"
                "/help - это сообщение\n"
                "/test - тестовое уведомление",
                parse_mode="HTML"
            )
        
        @self.dp.message(Command("test"))
        async def cmd_test(message: Message):
            """Обработчик команды /test для проверки"""
            if message.from_user.id != self.user_id:
                await message.answer("⛔ Нет доступа.")
                return
            
            await message.answer("🧪 Тестовое сообщение. Бот работает!")
            
            # Отправляем дополнительную информацию
            await self.send_notification(
                "🔔 <b>Это тестовое уведомление</b>\n"
                f"Если вы это видите, значит бот настроен правильно!\n"
                f"Время: {asyncio.get_event_loop().time():.0f}"
            )
    
    async def send_notification(self, message: str) -> bool:
        """
        Отправляет уведомление пользователю.
        
        Args:
            message: Текст сообщения (можно с HTML разметкой)
            
        Returns:
            True если отправлено успешно, False если ошибка
        """
        if not self._initialized:
            self.initialize()
        
        try:
            logger.info(f"📨 Отправка уведомления пользователю {self.user_id}")
            logger.debug(f"Текст: {message[:100]}...")
            
            await self.bot.send_message(
                chat_id=self.user_id,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            
            logger.info("✅ Уведомление отправлено")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления: {e}")
            return False
    
    async def start_polling(self):
        """
        Запускает поллинг бота (для приема команд).
        """
        if not self._initialized:
            self.initialize()
        
        logger.info("🔄 Запуск поллинга...")
        
        try:
            # Удаляем webhook (на всякий случай)
            await self.bot.delete_webhook(drop_pending_updates=True)
            
            # Запускаем поллинг
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            logger.error(f"❌ Ошибка в поллинге: {e}")
            raise
    
    async def stop(self):
        """
        Останавливает бота.
        """
        if self.bot:
            logger.info("🛑 Остановка бота...")
            await self.bot.session.close()
            self._initialized = False
    
    async def send_welcome(self) -> bool:
        """
        Отправляет приветственное сообщение при запуске.
        """
        welcome_msg = (
            f"🚀 <b>Мониторинг Google Sheets запущен!</b>\n"
            f"──────────────\n"
            f"• Ячейка: {config.MONITOR_CELL}\n"
            f"• Интервал: {config.CHECK_INTERVAL_SECONDS} сек\n"
            f"• Таблица: {config.sheet_url}\n\n"
            f"Бот будет присылать уведомления при изменении значения в ячейке."
        )
        
        return await self.send_notification(welcome_msg)


# Синглтон экземпляр
_bot_instance: Optional[NotificationBot] = None


def get_bot() -> NotificationBot:
    """
    Возвращает экземпляр бота.
    """
    global _bot_instance
    
    if _bot_instance is None:
        _bot_instance = NotificationBot()
    
    return _bot_instance


async def test_bot():
    """
    Тестовая функция для проверки бота.
    Запустите: python -m bot.notification
    """
    print("\n" + "="*50)
    print("ТЕСТ TELEGRAM БОТА")
    print("="*50)
    
    bot = get_bot()
    
    try:
        print("\n1. Инициализация бота...")
        bot.initialize()
        print("   ✅ Бот инициализирован")
        
        print(f"\n2. Проверка токена...")
        bot_info = await bot.bot.get_me()
        print(f"   ✅ Бот: @{bot_info.username}")
        print(f"   🆔 ID: {bot_info.id}")
        
        print(f"\n3. Отправка тестового сообщения...")
        print(f"   👤 Кому: {bot.user_id}")
        success = await bot.send_notification(
            "🧪 <b>Тестовое сообщение от бота</b>\n"
            "Если вы это читаете, значит бот работает!"
        )
        
        if success:
            print("   ✅ Сообщение отправлено! Проверьте Telegram.")
        else:
            print("   ❌ Ошибка отправки")
        
        print("\n4. Отправка приветствия...")
        await bot.send_welcome()
        print("   ✅ Приветствие отправлено")
        
        print("\n5. Бот готов к работе!")
        print("\n📋 Команды для тестирования:")
        print("   /start - приветствие")
        print("   /status - статус")
        print("   /test - тестовое уведомление")
        print("   /help - помощь")
        
        print("\n🔄 Бот запущен и ждет команды...")
        print("   Нажмите Ctrl+C для остановки")
        
        # Запускаем поллинг (будет ждать команды)
        await bot.start_polling()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Остановка по запросу пользователя")
    except Exception as e:
        print(f"\n❌ Ошибка: {type(e).__name__}: {e}")
        print("\n🔧 Проверьте:")
        print("   1. Правильный ли токен в .env?")
        print("   2. Правильный ли TELEGRAM_USER_ID?")
        print("   3. Написали ли вы боту /start?")
    finally:
        await bot.stop()
        print("\n👋 Бот остановлен")


if __name__ == "__main__":
    # Настройка логирования для теста
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    
    # Запуск теста
    asyncio.run(test_bot())