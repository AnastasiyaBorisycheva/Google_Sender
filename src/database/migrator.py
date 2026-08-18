import asyncio
from datetime import date, datetime

import gspread
from gspread_asyncio import AsyncioGspreadClientManager
from sqlalchemy import select

from src.config import config
from src.database.crud import get_or_create_user
from src.database.engine import AsyncSessionLocal
from src.database.models import HeadacheRecord
from src.logger import setup_logger
from src.sheets import get_creds

logger = setup_logger(__name__)

sheets_list = ['2021', '2022', '2023', '2024', '2025', '2026']


async def migrate_data():
    logger.info("Старт миграции данных...")

    # 1. Инициализируем клиент Google Sheets
    client_manager = AsyncioGspreadClientManager(get_creds)
    client = await client_manager.authorize()
    spreadsheet = await client.open_by_key(key=config.SPREADSHEET_ID)

    # 2. Открываем ЕДИНУЮ сессию для всей миграции
    async with AsyncSessionLocal() as session:
        
        # Гарантируем наличие пользователя-админа в БД 
        admin_user = await get_or_create_user(
            session=session,
            telegram_id=config.ADMIN_USER_ID
        )
        logger.info(f"Нашли пользователя: ID={admin_user.id}")

        # --- Загружаем существующие даты из базы ---
        stmt = select(HeadacheRecord.pain_date).where(HeadacheRecord.user_id == admin_user.id)
        result = await session.execute(stmt)
        existing_dates = set(result.scalars().all())
        logger.info(f"Найдено {len(existing_dates)} ранее сохраненных дат в БД.")
        # --------------------------------------------------

        headache_records = []

        # Получаем все данные из Google Таблицы
        for sheet_name in sheets_list:
            try:
                worksheet = await spreadsheet.worksheet(sheet_name)
                logger.info(f"Обработка листа: {sheet_name}")

                rows = await worksheet.batch_get(['B3:C'])

                for row in rows[0]:
                    if len(row) == 2:
                        try:
                            pain_date = datetime.strptime(row[0], "%d.%m.%Y").date()

                            # Проверяем, есть ли дата в множестве уже существующих
                            if pain_date in existing_dates:
                                continue
                            
                            medicine = 'золмитриптан 2.5' if pain_date.year in (2025, 2026) else None
                            
                            headache_records.append(
                                HeadacheRecord(
                                    user_id=admin_user.id,
                                    pain_date=pain_date,
                                    medicine=medicine,
                                    comment='Запись из архива'
                                )
                            )
                        except ValueError:
                            logger.warning(f"Не удалось распарсить дату из строки: {row}")

            except gspread.exceptions.WorksheetNotFound:
                logger.warning(f"Лист {sheet_name} не найден в Google Таблице, пропускаем.")

        # 3. Сохраняем все собранные записи пачкой
        if headache_records:
            session.add_all(headache_records)
            await session.commit()
            logger.info(f"Успешно сохранено {len(headache_records)} записей в БД!")
        else:
            logger.info("Новых записей для сохранения не найдено.")


if __name__ == "__main__":
    asyncio.run(migrate_data())