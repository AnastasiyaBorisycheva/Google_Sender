from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import config
from src.database.crud import add_headache_record, get_or_create_user
from src.database.engine import AsyncSessionLocal  # Наша фабрика сессий
from src.logger import setup_logger
from src.middlewares.db import DbSessionMiddleware
from src.notifier import Notifier
from src.sheets import sheets_client

logger = setup_logger(name=__name__, log_file='debug.log')


class PainBot:
    def __init__(self):
        self.bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        self.dp = Dispatcher()

        # Регистрируем Middleware для всех обновлений (messages, callback_query и т.д.)
        self.dp.update.middleware(DbSessionMiddleware(session_pool=AsyncSessionLocal))

        self.notifier = Notifier(self.bot)
        self._register_handlers()
    
    def _register_handlers(self):
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message, session: AsyncSession):
            try:
                # Регистрируем или получаем пользователя из базы
                user = await get_or_create_user(
                    session=session,
                    telegram_id=message.from_user.id,
                    first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name,
                    username=message.from_user.username,
                )
                await message.answer(
                    text=f"Привет, {user.first_name}!"
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
        async def cmd_pain(message: Message, session: AsyncSession):
            

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
                    # 1. Получаем или создаем пользователя в БД
                    user = await get_or_create_user(
                        session=session,
                        telegram_id=message.from_user.id,
                        first_name=message.from_user.first_name,
                        last_name=message.from_user.last_name,
                        username=message.from_user.username,
                    )
                    today_date = datetime.now()
                    date_str = today_date.strftime("%d.%m.%Y")

                    # 2. Сохраняем/обновляем запись о боли в PostgreSQL
                    record = await add_headache_record(
                        session=session,
                        user_id=user.id,  # Внутренний ID пользователя из таблицы users
                        pain_date=today_date,
                        is_pain=True,
                    )

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
