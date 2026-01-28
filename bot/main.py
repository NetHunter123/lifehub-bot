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
from bot.handlers import common, tasks, goals
from bot.database.models import init_database
from bot.database import queries
from bot.locales import set_user_lang

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot) -> None:
    """Виконується при запуску бота."""
    # Завантажуємо мову адміна
    admin_lang = await queries.get_user_language(config.ADMIN_ID)
    set_user_lang(config.ADMIN_ID, admin_lang)
    logger.info(f"✅ Мова адміна: {admin_lang}")


async def main() -> None:
    """Головна функція запуску бота."""
    
    # Перевіряємо конфігурацію
    config.validate()
    
    # Ініціалізуємо базу даних
    await init_database()
    logger.info("✅ База даних ініціалізована")
    
    # Створюємо бота
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Створюємо диспетчер
    dp = Dispatcher()
    
    # Реєструємо startup callback
    dp.startup.register(on_startup)
    
    # Реєструємо роутери
    dp.include_router(common.router)
    dp.include_router(tasks.router)
    dp.include_router(goals.router)
    
    # Запускаємо
    logger.info("🚀 Запускаємо бота...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
