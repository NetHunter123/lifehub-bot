"""
Точка входу для LifeHub Bot.
Запуск: python -m bot.main
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from bot.config import config
from bot.handlers import common, tasks
from bot.database.models import init_database

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Головна функція запуску бота."""
    
    # Перевіряємо конфігурацію
    config.validate()
    
    # Ініціалізуємо базу даних
    await init_database()
    logger.info("✅ База даних ініціалізована")
    
    # Створюємо бота з налаштуваннями за замовчуванням
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Створюємо диспетчер
    dp = Dispatcher()
    
    # Реєструємо роутери (handlers)
    dp.include_router(common.router)
    dp.include_router(tasks.router)
    
    # Видаляємо старі webhook (якщо є) і запускаємо polling
    logger.info("🚀 Запускаємо бота...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
