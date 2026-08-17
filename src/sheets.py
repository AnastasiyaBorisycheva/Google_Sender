"""
Асинхронный клиент для работы с Google Sheets
"""
import asyncio
from datetime import datetime
from typing import Optional, Tuple

import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError
from gspread.utils import column_letter_to_index
from gspread_asyncio import AsyncioGspreadClientManager

from src.config import config
from src.logger import setup_logger
from src.models import PainRecord

logger = setup_logger(name=__name__, log_file='debug.log')

def get_creds():
    return Credentials.from_service_account_file(
        config.GOOGLE_SHEETS_CREDENTIALS,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )


class SheetsError(Exception):
    """Ошибка при работе с Google Sheets"""

    pass


class SheetsClient:
    def __init__(self, client=None, spreadsheet=None, worksheet=None):
        self.client: Optional[gspread.Client] = None
        self.spreadsheet = None
        self.worksheet = None

    def initialize(self):
        """
        Инициализация подключения (синхронная часть)
        """

        try:
            # 1. Загрузить credentials из config.GOOGLE_SHEETS_CREDENTIALS
            creds = Credentials.from_service_account_file(
                config.GOOGLE_SHEETS_CREDENTIALS,
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )

            # 2. Авторизоваться через gspread.authorize()
            self.client = gspread.authorize(creds)

            # 3. Открыть таблицу по config.SPREADSHEET_ID
            self.spreadsheet = self.client.open_by_key(config.SPREADSHEET_ID)

            # 4. Получить лист по config.SHEET_NAME
            self.worksheet = self.spreadsheet.worksheet(config.SHEET_NAME)

            logger.info("Подключение установлено")
            logger.info(f"Таблица: {self.spreadsheet.title}")
            logger.info(f"Лист: {config.SHEET_NAME}")
            logger.info(f"Ячейка: {config.MONITOR_CELL}")

        except Exception as e:
            error_msg = f"Ошибка подключения: {type(e).__name__}: {e}"
            logger.error(error_msg)
            raise SheetsError(error_msg) from e

    def find_row_by_date(self, date: datetime) -> Optional[int]:
        """
        Находит номер строки, в которой в столбце DATE_COLUMN
        находится указанная дата.

        Формат даты в таблице: dd.mm.yyyy (например, "16.04.2026")

        Returns:
            Номер строки (1, 2, 3...) или None если не найдена
        """
        # 1. Получить все значения из столбца config.DATE_COLUMN
        #    метод worksheet.col_values(буква_столбца)
        dates = self.worksheet.col_values(column_letter_to_index(config.DATE_COLUMN))

        # 2. Преобразовать дату в строку формата dd.mm.yyyy
        str_date = datetime.strftime(date, "%d.%m.%Y")

        # 3. Пройти по всем значениям, найти совпадение
        try:
            row = dates.index(str_date)

            # 4. Вернуть индекс + 1 (потому что списки в Python с 0)
            return row + 1
        except ValueError:
            logger.warning(f"Дата {str_date} не найдена в столбце {config.DATE_COLUMN}")
            return None

    def write_pain_record(self, row: int) -> None:
        """
        Записывает в указанную строку:
        - В столбец PAIN_COLUMN: значение 1
        - В столбец MEDICATION_COLUMN: "золмитриптан 2.5"

        Если в ячейке PAIN_COLUMN уже есть значение (не пусто) — ничего не делать.
        """
        # 1. Прочитать текущее значение из столбца PAIN_COLUMN для этой строки
        pain_cell_address = f"{config.PAIN_COLUMN}{row}"
        current_pain_value = self.worksheet.acell(pain_cell_address).value
        # 2. Если значение не пустое (не None, не "") → вывести warning и вернуться
        if current_pain_value:
            logger.warning(f"В ячейке {pain_cell_address} уже есть значение")
            return
        # 3. Иначе записать 1 в PAIN_COLUMN и "золмитриптан 2.5" в MEDICATION_COLUMN
        #    Используйте метод worksheet.update(cell, value)
        else:
            self.worksheet.update_acell(pain_cell_address, 1)
            medication_cell_address = f"{config.MEDICATION_COLUMN}{row}"
            self.worksheet.update_acell(medication_cell_address, "золмитриптан 2.5")
            logger.info(
                f"✅ Записано: {pain_cell_address}=1, {medication_cell_address}=золмитриптан 2.5"
            )

    def get_record_at_row(self, row: int) -> PainRecord:
        """
        Получает запись из указанной строки (для мониторинга изменений)
        """
        # Получаем значения
        date_str = self.worksheet.acell(f"{config.DATE_COLUMN}{row}").value
        pain = self.worksheet.acell(f"{config.PAIN_COLUMN}{row}").value
        medication = self.worksheet.acell(f"{config.MEDICATION_COLUMN}{row}").value

        # Преобразуем дату из строки в datetime
        date_obj = datetime.strptime(date_str, "%d.%m.%Y") if date_str else None

        return PainRecord(
            date=date_obj,
            row=row,
            pain_level=int(pain) if pain else None,
            medication=medication,
        )

    def get_all_records(self) -> dict[int, PainRecord]:
        """
        Возвращает словарь {номер_строки: PainRecord} для всех строк
        с непустыми значениями в PAIN_COLUMN
        """
        result = {}

        # Получаем все записи как список словарей
        records = self.worksheet.get_all_records()

        # get_all_records() возвращает список, начиная со строки 2 (если строка 1 - заголовки)
        for i, record in enumerate(records, start=2):
            pain_value = record.get(config.PAIN_COLUMN)
            if pain_value:  # если есть значение в столбце боли
                result[i] = PainRecord(
                    date=(
                        datetime.strptime(
                            record.get(config.DATE_COLUMN, ""), "%d.%m.%Y"
                        )
                        if record.get(config.DATE_COLUMN)
                        else None
                    ),
                    row=i,
                    pain_level=int(pain_value) if str(pain_value).isdigit() else None,
                    medication=record.get(config.MEDICATION_COLUMN),
                )

        return result

class AsyncSheetsClient:
    def __init__(
            self,
            spreadsheet_id: Optional[str] = None,
            sheet_name: Optional[str] = None
        ):
        self.spreadsheet_id = spreadsheet_id or config.SPREADSHEET_ID
        self.sheet_name = sheet_name or config.SHEET_NAME
        self.client = None
        self.spreadsheet = None
        self.worksheet = None

    async def initialize(self) -> None:
        """Инициализация подключения"""

        try:
            client_manager = AsyncioGspreadClientManager(get_creds)
            self.client = await client_manager.authorize()

            self.spreadsheet = await self.client.open_by_key(self.spreadsheet_id)
            self.worksheet = await self.spreadsheet.worksheet(self.sheet_name)

            logger.info("Подключение установлено")
            logger.info(f"Подключились к таблице: {self.spreadsheet.title}")
            logger.info(f"Подключились к листу: {self.sheet_name}")

        except Exception as e:
            error_msg = f"Ошибка подключения: {type(e).__name__}: {e}"
            logger.error(error_msg)
            raise SheetsError(error_msg) from e

    async def find_row_by_date(
            self,
            date: datetime,
            letter: str = config.DATE_COLUMN
        ) -> Optional[int]:
        """
            Находит номер строки, в которой в столбце DATE_COLUMN
            находится указанная дата.
            Формат даты в таблице: dd.mm.yyyy (например, "16.04.2026")
            Returns:
                Номер строки (1, 2, 3...) или None если не найдена
        """

        # 1. Преобразовываем переданную букву в числовое представление
        col_idx = column_letter_to_index(letter)

        # 2. Преобразовываем дату в строку формата dd.mm.yyyy
        str_date = datetime.strftime(date, "%d.%m.%Y")

        # 3. Находим все даты в столбце
        try:
            cell = await self.worksheet.find(str_date, in_column=col_idx)
            return cell.row if cell else None
        except APIError as e:
            logger.warning(f"Ошибка API при поиске даты {str_date}: {e}")
            return None
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при поиске даты: {e}")
            return None

    async def get_record_at_row(self, row: int) -> Optional[PainRecord]:
        """
        Получает запись из указанной строки (для мониторинга изменений)
        """

        col_data_idx = column_letter_to_index(config.DATE_COLUMN) - 1
        col_pain_idx = column_letter_to_index(config.PAIN_COLUMN) - 1
        col_med_idx = column_letter_to_index(config.MEDICATION_COLUMN) - 1

        try:
            row_data = await self.worksheet.row_values(row)
            # Безопасное получение элемента из списка по индексу
            def get_val(idx: int) -> str:
                return row_data[idx].strip() if idx < len(row_data) else ""

            data_info = get_val(col_data_idx)
            pain_info = get_val(col_pain_idx)
            medicine_info = get_val(col_med_idx)

            # Парсим дату
            data_info_as_date = (
                datetime.strptime(data_info, "%d.%m.%Y") if data_info else None
            )

            # Безопасное приведение боли к int (1 или None)
            pain_level = int(pain_info) if pain_info.isdigit() else None

            # Медикамент (возвращаем None, если строка пустая)
            medication = medicine_info if medicine_info else None

            return PainRecord(
                date=data_info_as_date,
                row=row,
                pain_level=pain_level,
                medication=medication
            )
        except APIError as e:
            logger.warning(f"Ошибка API при чтении строки {row}: {e}")
            return None
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при чтении строки {row}: {e}")
            return None


# Глобальный экземпляр
# sheets_client = SheetsClient()
async_sheet_client = AsyncSheetsClient(
    spreadsheet_id='18G0PQZp0z1Cw0XkBFvjXB3YXCOmeMmWHzoVcLvbdV3k',
    sheet_name='2025'
)

async def main():
    await async_sheet_client.initialize()
    test_date = datetime.strptime("2025-01-16", "%Y-%m-%d")
    result_cell = await async_sheet_client.find_row_by_date(test_date)
    line_record = await async_sheet_client.get_record_at_row(result_cell)
    print(line_record)

if __name__ == "__main__":

    asyncio.run(main(), debug=True)

    # sheets_client.initialize()
    # test_date = datetime.strptime("2026-04-17", "%Y-%m-%d")
    # sheets_client.find_row_by_date(test_date)
    