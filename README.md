# Google Sheets Monitor 🤖

Асинхронный монитор для отслеживания изменений в Google Sheets с уведомлениями в Telegram.

## 🎯 Функциональность

- Мониторинг конкретной ячейки Google Sheets
- Асинхронные проверки с настраиваемым интервалом
- Уведомления в Telegram при изменениях
- Логирование всех операций
- Восстановление состояния после перезапуска

## 🚀 Быстрый старт

### 1. Клонирование репозитория
```bash
git clone https://github.com/ваш-username/google-sheets-monitor.git
cd google-sheets-monitor


1. Клонировать репозиторий
2. Настроить Google Service Account

Создайте проект в Google Cloud Console

Включите Google Sheets API

Создайте сервисный аккаунт и скачайте credentials.json

Поделитесь таблицей с email сервисного аккаунта

3. Создать Telegram бота

Создайте бота через @BotFather

Получите токен бота

Узнайте свой User ID через @userinfobot

4. Заполнить .env файл
5. Установить зависимости: `pip install -r requirements.txt`
6. Запустить: `python main.py`

## Конфигурация

Скопируйте `.env.example` в `.env` и заполните:

TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_USER_ID=123456789
SPREADSHEET_ID=your_sheet_id


Структура проекта
google-sheets-monitor/
├── bot/           # Telegram бот
├── services/      # Бизнес-логика
├── utils/         # Вспомогательные функции
├── config.py      # Конфигурация приложения
├── main.py        # Точка входа
├── requirements.txt
├── .env.example   # Шаблон конфигурации
└── README.md


## Логика работы

Проверяет ячейку C1 каждые N секунд, при изменении отправляет уведомление.

requirements.txt (начальный набор):

# Основные зависимости
aiogram>=3.0.0
gspread
google-auth
python-dotenv

# Для асинхронности
aiohttp
asyncio

# Утилиты
pydantic  # для валидации конфигурации