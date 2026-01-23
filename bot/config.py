"""
Конфігурація бота.
Завантажує змінні середовища з .env файлу.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Завантажуємо .env файл
load_dotenv()

# Базова директорія проєкту
BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Налаштування бота."""
    
    # Telegram
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
    
    # База даних
    DATABASE_PATH: Path = BASE_DIR / os.getenv("DATABASE_PATH", "data/lifehub.db")
    
    # Часовий пояс
    TIMEZONE: str = os.getenv("TIMEZONE", "Europe/Berlin")
    
    # Нагадування (години)
    MORNING_REMINDER_HOUR: int = 8
    EVENING_REMINDER_HOUR: int = 21
    
    @classmethod
    def validate(cls) -> bool:
        """Перевіряє наявність обов'язкових налаштувань."""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не встановлено! Додай його в .env файл.")
        if not cls.ADMIN_ID:
            raise ValueError("ADMIN_ID не встановлено! Додай його в .env файл.")
        return True


# Експортуємо для зручності
config = Config()
