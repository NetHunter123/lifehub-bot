"""
LifeHub Bot v4.0
Telegram бот для управління задачами, цілями та звичками.

Архітектура:
- Tasks: one-time + recurring (is_fixed для фіксованого часу)
- Goals: project, target, metric (БЕЗ task!)
- Habits: окремо від recurring tasks (streak tracking)

Запуск:
    python -m bot.main
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import config
from bot.database.models import init_database
from bot.handlers import common, tasks, goals, habits, today


# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Головна функція запуску бота."""
    
    # Валідація конфігурації
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"❌ Помилка конфігурації: {e}")
        return
    
    # Ініціалізація бази даних
    logger.info("📦 Ініціалізація бази даних...")
    await init_database()
    
    # Створення бота
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Створення диспетчера
    dp = Dispatcher()
    
    # Реєстрація роутерів
    dp.include_router(common.router)
    dp.include_router(tasks.router)
    dp.include_router(goals.router)
    dp.include_router(habits.router)
    dp.include_router(today.router)
    
    # Запуск
    logger.info("🚀 Бот запускається...")
    
    try:
        # Видаляємо webhook якщо є
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Запускаємо polling
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    finally:
        await bot.session.close()
        logger.info("👋 Бот зупинено.")


if __name__ == "__main__":
    asyncio.run(main())
