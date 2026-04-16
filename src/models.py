"""
Pydantic модели для данных приложения
"""

from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class PainRecord(BaseModel):
    """
    Модель записи о боли
    """
    date: datetime           # дата события
    row: int                 # номер строки в Google Sheets
    pain_level: Optional[int] = None  # 1 или None
    medication: Optional[str] = None   # название препарата или None


class SheetCell(BaseModel):
    """
    Позиция ячейки в Google Sheets
    """
    column: str   # буква столбца (A, B, C...)
    row: int      # номер строки (1, 2, 3...)
    
    @property
    def a1_notation(self) -> str:
        """Возвращает адрес в формате A1 (например, 'C5')"""
        # TODO: вернуть строку вида f"{column}{row}"
        ...