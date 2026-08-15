from typing import Callable, Awaitable, Dict, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker[AsyncSession]):
        # Сохраняем фабрику сессий, которую создали в engine.py
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Открываем сессию на время обработки одного события
        async with self.session_pool() as session:
            # Кладем сессию в data["session"] — теперь aiogram сможет передать ее в аргументы хендлера!
            data["session"] = session
            # Передаем управление дальше хендлеру
            return await handler(event, data)