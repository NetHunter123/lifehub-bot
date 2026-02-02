"""
LifeHub Bot — Entry Point.
Version 4.0

Запуск: python -m bot.main
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from bot.config import config
from bot.database.models import init_database

# Handlers
from bot.handlers import common, tasks, goals, habits, today


# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Головна функція запуску бота."""
    
    # Перевіряємо конфігурацію
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return
    
    # Ініціалізуємо базу даних
    logger.info("Initializing database...")
    await init_database()
    
    # Створюємо бота та диспетчер
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Реєструємо handlers
    dp.include_router(common.router)
    dp.include_router(tasks.router)
    dp.include_router(goals.router)
    dp.include_router(habits.router)
    dp.include_router(today.router)
    
    # Видаляємо webhook (якщо був) і запускаємо polling
    logger.info("Starting bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
