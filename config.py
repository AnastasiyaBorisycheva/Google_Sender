# config.py
from dotenv import load_dotenv
import os

# Загружает переменные из .env в os.environ
load_dotenv()

# Теперь можно получать значения
token = os.getenv("TELEGRAM_BOT_TOKEN")