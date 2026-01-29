"""Точка входу для LifeHub Bot."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from bot.config import config
from bot.handlers import common, tasks, goals, today
from bot.database.models import init_database
from bot.locales import set_user_lang

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main() -> None:
    config.validate()
    
    await init_database()
    logger.info("✅ База даних ініціалізована")
    
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    
    # Реєструємо роутери
    dp.include_router(common.router)
    dp.include_router(tasks.router)
    dp.include_router(goals.router)
    dp.include_router(today.router)
    
    logger.info("🚀 Запускаємо бота...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
