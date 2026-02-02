"""
Конфігурація бота.
LifeHub Bot v4.0
"""

import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Конфігурація застосунку."""
    
    # Telegram
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
    
    # Database
    DATABASE_PATH: Path = Path(os.getenv("DATABASE_PATH", "data/lifehub.db"))
    
    # Timezone
    TIMEZONE: str = os.getenv("TIMEZONE", "Europe/Berlin")
    
    # Default language
    DEFAULT_LANGUAGE: str = "uk"
    
    # Reminders
    MORNING_TIME: str = "08:00"
    EVENING_TIME: str = "21:00"
    
    def validate(self) -> None:
        """Перевірка обов'язкових параметрів."""
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не встановлено! Додай його в .env файл.")
        if not self.ADMIN_ID:
            raise ValueError("ADMIN_ID не встановлено! Додай його в .env файл.")


config = Config()
