"""База даних бота."""

from bot.database.models import init_database, get_db

__all__ = ["init_database", "get_db"]
