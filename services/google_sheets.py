"""
Упрощенный сервис для работы с Google Sheets.
Пока синхронный, для простоты отладки.
"""

import logging
from typing import Any, Optional

import gspread
from google.oauth2.service_account import Credentials

from config import config

logger = logging.getLogger(__name__)


class GoogleSheetsError(Exception):
    """Базовое исключение для ошибок Google Sheets"""

    pass


class GoogleSheetsService:
    """
    Сервис для работы с Google Sheets.
    Синхронная версия для простоты.
    """

    def __init__(self):
        self._client: Optional[gspread.Client] = None
        self._spreadsheet: Optional[gspread.Spreadsheet] = None
        self._worksheet: Optional[gspread.Worksheet] = None
        self._initialized = False

    def initialize(self) -> None:
        """
        Инициализирует подключение к Google Sheets.
        """
        if self._initialized:
            return

        logger.info("🔗 Инициализация подключения к Google Sheets...")

        try:
            # 1. Загружаем credentials
            logger.debug(
                f"Загрузка credentials из {config.GOOGLE_CREDENTIALS_PATH}"
            )
            creds = Credentials.from_service_account_file(
                config.GOOGLE_CREDENTIALS_PATH,
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )

            # 2. Создаем клиент
            logger.debug("Авторизация в Google Sheets API...")
            self._client = gspread.authorize(creds)

            # 3. Открываем таблицу
            logger.debug(f"Открытие таблицы {config.SPREADSHEET_ID}")
            self._spreadsheet = self._client.open_by_key(config.SPREADSHEET_ID)

            # 4. Получаем лист
            logger.debug(f"Получение листа '{config.SHEET_NAME}'")
            self._worksheet = self._spreadsheet.worksheet(config.SHEET_NAME)

            self._initialized = True

            logger.info("✅ Подключение установлено")
            logger.info(f"   Таблица: {self._spreadsheet.title}")
            logger.info(f"   Лист: {config.SHEET_NAME}")
            logger.info(f"   Ячейка: {config.MONITOR_CELL}")

        except FileNotFoundError as e:
            error_msg = f"Файл {config.GOOGLE_CREDENTIALS_PATH} не найден"
            logger.error(error_msg)
            raise GoogleSheetsError(error_msg) from e

        except gspread.exceptions.SpreadsheetNotFound as e:
            error_msg = f"Таблица с ID {config.SPREADSHEET_ID} не найдена"
            logger.error(error_msg)
            logger.error("Проверьте:")
            logger.error("  1. Правильный ли SPREADSHEET_ID в .env?")
            logger.error("  2. Дал ли доступ сервисному аккаунту к таблице?")
            raise GoogleSheetsError(error_msg) from e

        except gspread.exceptions.WorksheetNotFound as e:
            error_msg = f"Лист '{config.SHEET_NAME}' не найден"
            logger.error(error_msg)
            logger.error("Доступные листы:")
            if self._spreadsheet:
                for sheet in self._spreadsheet.worksheets():
                    logger.error(f"  - {sheet.title}")
            raise GoogleSheetsError(error_msg) from e

        except Exception as e:
            error_msg = f"Ошибка подключения: {type(e).__name__}: {e}"
            logger.error(error_msg)
            raise GoogleSheetsError(error_msg) from e

    def get_cell_value(self, cell: Optional[str] = None) -> Optional[Any]:
        """
        Получает значение ячейки из таблицы.

        Args:
            cell: Адрес ячейки (например, "C1").
            Если None, используется из конфигурации.

        Returns:
            Значение ячейки или None если ячейка пустая.
        """
        if not self._initialized:
            self.initialize()

        target_cell = cell or config.MONITOR_CELL

        try:
            logger.debug(f"📥 Чтение ячейки {target_cell}")

            # Получаем ячейку
            cell_obj = self._worksheet.acell(target_cell)
            value = cell_obj.value

            # Преобразуем пустые значения в None
            if value == "":
                return None

            logger.debug(f"📤 {target_cell} = {repr(value)}")
            return value

        except Exception as e:
            error_msg = f"Ошибка чтения ячейки {target_cell}: {e}"
            logger.error(error_msg)
            raise GoogleSheetsError(error_msg) from e

    def test_connection(self) -> bool:
        """
        Тестирует подключение, читая тестовую ячейку.

        Returns:
            True если подключение работает
        """
        try:
            self.initialize()

            # Читаем ячейку A1
            value = self.get_cell_value("A1")
            logger.info(f"✅ Подключение работает. A1 = {repr(value)}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка подключения: {e}")
            return False

    def get_sheet_info(self) -> dict:
        """
        Возвращает информацию о таблице.
        """
        if not self._initialized:
            self.initialize()

        try:
            info = {
                "title": self._spreadsheet.title,
                "sheet_count": len(self._spreadsheet.worksheets()),
                "current_sheet": config.SHEET_NAME,
                "rows": self._worksheet.row_count,
                "cols": self._worksheet.col_count,
                "monitor_cell": config.MONITOR_CELL,
                "url": config.sheet_url,
            }

            logger.debug(f"Информация о таблице: {info}")
            return info

        except Exception as e:
            error_msg = f"Ошибка получения информации: {e}"
            logger.error(error_msg)
            raise GoogleSheetsError(error_msg) from e

    def get_all_sheets(self) -> list:
        """
        Возвращает список всех листов в таблице.
        """
        if not self._initialized:
            self.initialize()

        sheets = []
        for worksheet in self._spreadsheet.worksheets():
            sheets.append(
                {
                    "title": worksheet.title,
                    "rows": worksheet.row_count,
                    "cols": worksheet.col_count,
                }
            )

        return sheets


# Синглтон экземпляр
_sheets_service: Optional[GoogleSheetsService] = None


def get_sheets_service() -> GoogleSheetsService:
    """
    Возвращает экземпляр сервиса.
    """
    global _sheets_service

    if _sheets_service is None:
        _sheets_service = GoogleSheetsService()

    return _sheets_service


def test_sheets_connection() -> None:
    """
    Тестовая функция.
    Запустите: python -m services.google_sheets
    """
    print("\n" + "=" * 50)
    print("ТЕСТ GOOGLE SHEETS API")
    print("=" * 50)

    try:
        service = get_sheets_service()

        print("\n1. Инициализация...")
        service.initialize()

        print("\n2. Тест подключения...")
        if service.test_connection():
            print("   ✅ Подключение работает")
        else:
            print("   ❌ Подключение не работает")
            return

        print("\n3. Информация о таблице...")
        info = service.get_sheet_info()
        print(f"   • Название: {info['title']}")
        print(f"   • Листов: {info['sheet_count']}")
        print(f"   • Текущий лист: {info['current_sheet']}")
        print(f"   • Размер: {info['rows']}x{info['cols']}")
        print(f"   • URL: {info['url']}")

        print("\n4. Все листы в таблице:")
        sheets = service.get_all_sheets()
        for sheet in sheets:
            print(f"   • {sheet['title']} ({sheet['rows']}x{sheet['cols']})")

        print(f"\n5. Чтение ячейки {config.MONITOR_CELL}...")
        value = service.get_cell_value(config.MONITOR_CELL)
        print(f"   • {config.MONITOR_CELL} = {repr(value)}")

        print("\n6. Чтение ячейки A1...")
        value_a1 = service.get_cell_value("A1")
        print(f"   • A1 = {repr(value_a1)}")

        print("\n" + "=" * 50)
        print("✅ Все тесты пройдены!")
        print("   Google Sheets API готов к работе.")

    except Exception as e:
        print(f"\n❌ Ошибка: {type(e).__name__}: {e}")
        print("\n🔧 Возможные причины:")
        print("   1. Файл credentials.json не найден или поврежден")
        print("   2. Неправильный SPREADSHEET_ID в .env")
        print("   3. Лист Sheet1 не существует (проверьте название)")
        print("   4. Нет доступа у сервисного аккаунта к таблице")
        print("   5. Проблемы с интернет-подключением")
        print("\n📋 Что проверить:")
        print(f"   • Файл: {config.GOOGLE_CREDENTIALS_PATH}")
        print(f"   • ID таблицы: {config.SPREADSHEET_ID}")
        print(f"   • Лист: {config.SHEET_NAME}")
        raise


if __name__ == "__main__":
    # Настройка логирования для теста
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stdout
    )

    # Запуск теста
    test_sheets_connection()
