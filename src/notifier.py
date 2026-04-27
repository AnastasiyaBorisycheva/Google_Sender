from aiogram import Bot
from src.config import config
from src.logger import logger


class Notifier:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def notify_all(self, message: str):
        """
        Отправить уведомление всем пользователям
        """
        if not config.USERS_IDS:
            logger.warning(
                "Список USERS_IDS пуст! Уведомления никому не отправятся."
            )

        for user_id in config.USERS_IDS:
            try:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode="HTML"
                )
                logger.info(f"Уведомление отправлено пользователю {user_id}")
            except Exception as e:
                logger.error(
                    f"Ошибка при отправке уведомления пользователю {user_id}:"
                    f"{e}"
                )

    async def notify_admin(self, message: str):
        """
        Отправить уведомление админу
        """
        try:
            await self.bot.send_message(
                chat_id=config.ADMIN_USER_ID,
                text=message,
                parse_mode="HTML"
            )
            logger.info("Уведомление отправлено админу")
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления админу: {e}")

    async def notify_user(self, user_id: int, message: str):
        """
        Отпрвить уведомление конкретному пользователю
        """
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="HTML"
            )
            logger.info(f"Уведомление отправлено пользователю {user_id}")
        except Exception as e:
            logger.error(
                f"Ошибка при отправке уведомления пользователю {user_id}: {e}"
            )

    def format_pain_notification(self, date: str) -> str:
        """Возвращает красивое сообщение с эмодзи и форматированием"""
        return (
            f"📋 <b>Запись в медицинском дневнике</b>\n"
            f"────────────────────\n"
            f"• Дата: {date}\n"
            f"• Боль: есть (1)\n"
            f"• Препарат: золмитриптан 2.5"
        )
