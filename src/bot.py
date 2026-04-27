from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from src.config import config
from src.logger import logger
from src.notifier import Notifier
from src.sheets import sheets_client


class PainBot:
    def __init__(self):
        self.bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        self.dp = Dispatcher()
        self.notifier = Notifier(self.bot)
        self._register_handlers()
    
    def _register_handlers(self):
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message):
            # TODO: приветствие
            try:
                await message.answer(
                    text=f"Привет, {message.from_user.first_name}!"
                )
                logger.info(
                    f"Поприветствовали пользователя {message.from_user.id}"
                )
            except Exception as e:
                logger.error(
                    f"Ошибка {e} "
                    f"при ответе на команду /start "
                    f"от пользователя {message.from_user.id}"
                )
            
        @self.dp.message(Command("pain"))
        async def cmd_pain(message: Message):
            # TODO: основная логика

            if message.from_user.id != config.ADMIN_USER_ID:
                await message.answer(
                    text="Вы не являетесь пользователем ADMIN"
                )
                logger.warning(
                    f"Пользователь {message.from_user.id} вызвал команду /pain"
                )
                return
            else:
                try:
                    today_date = datetime.now()
                    date_str = today_date.strftime("%d.%m.%Y")
                    row = sheets_client.find_row_by_date(today_date)

                    if not row:
                        await message.answer(
                            f"Дата {date_str} не найдена в таблице"
                        )
                        return

                    pain_info = sheets_client.get_record_at_row(row=row)
                    if pain_info.pain_level:
                        await message.answer(
                            "На сегодня уже есть запись о боли"
                        )
                        return

                    sheets_client.write_pain_record(row=row)
                    msg_text = self.notifier.format_pain_notification(
                        today_date.strftime("%d.%m.%Y")
                    )
                    await self.notifier.notify_all(message=msg_text)
                    logger.info(
                        f"Админ {message.from_user.id} "
                        f"записал боль на {date_str}"
                    )

                except Exception as e:
                    await message.answer(
                        "Произошла ошибка при обработке команды /pain"
                    )
                    logger.error(
                        f"Ошибка при обработке команды /pain: {e}"
                    )

    async def start_polling(self):
        await self.dp.start_polling(self.bot)

    async def stop(self):
        await self.bot.session.close()
