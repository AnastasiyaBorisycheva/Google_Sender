"""
Асинхронный клиент для работы с Google Sheets
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from typing import Optional, Tuple
from gspread.utils import column_letter_to_index
from src.logger import logger

from src.config import config
from src.models import PainRecord


class SheetsError(Exception):
    """Ошибка при работе с Google Sheets"""

    pass


class SheetsClient:
    def __init__(self):
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


# Глобальный экземпляр
sheets_client = SheetsClient()


if __name__ == "__main__":
    sheets_client.initialize()
    test_date = datetime.strptime("2026-04-17", "%Y-%m-%d")
    sheets_client.find_row_by_date(test_date)
