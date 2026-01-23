"""
Загальні обробники команд.
/start, /help, /menu
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from bot.keyboards.menu import get_main_menu_keyboard, get_back_to_menu_keyboard
from bot.keyboards.reply import get_main_reply_keyboard

router = Router()


# ============== КОМАНДИ ==============

@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Обробник команди /start."""
    # Спочатку показуємо ReplyKeyboard (постійне меню)
    await message.answer(
        f"👋 <b>Привіт!</b>\n\n"
        f"Я <b>LifeHub Bot</b> — твій персональний асистент для:\n\n"
        f"📋 Управління задачами та цілями\n"
        f"✅ Трекінгу звичок\n"
        f"📚 Бібліотеки книг\n"
        f"🇩🇪 Вивчення мов\n\n"
        f"Використовуй меню нижче 👇",
        reply_markup=get_main_reply_keyboard()
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Обробник команди /help."""
    help_text = """
📖 <b>Команди бота</b>

<b>Загальні:</b>
/start — Привітання
/help — Ця довідка
/menu — Головне меню

<b>Задачі:</b>
/tasks — Задачі на сьогодні
/task_add — Додати задачу
/task_done &lt;id&gt; — Виконати задачу

<b>Цілі:</b>
/goals — Всі цілі
/goal_add — Додати ціль

<b>Звички:</b>
/habits — Звички на сьогодні
/habit_add — Додати звичку
/habit_done &lt;id&gt; — Відмітити

<b>Книги:</b>
/books — Бібліотека
/book_add — Додати книгу

<b>Слова:</b>
/learn — Почати тренування
/words — Статистика

<b>Інше:</b>
/stats — Статистика
/settings — Налаштування
"""
    await message.answer(help_text, reply_markup=get_back_to_menu_keyboard())


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    """Обробник команди /menu."""
    await message.answer(
        "🏠 <b>Головне меню</b>\n\nОбери розділ:",
        reply_markup=get_main_menu_keyboard()
    )


# ============== CALLBACK HANDLERS ==============

@router.callback_query(F.data == "menu:main")
async def callback_main_menu(callback: CallbackQuery) -> None:
    """Повернення до головного меню."""
    await callback.message.edit_text(
        "🏠 <b>Головне меню</b>\n\nОбери розділ:",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "menu:tasks")
async def callback_tasks(callback: CallbackQuery) -> None:
    """Розділ задач."""
    await callback.message.edit_text(
        "📋 <b>Задачі</b>\n\n"
        "🚧 Цей розділ у розробці...\n\n"
        "Скористайся командою /task_add",
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "menu:goals")
async def callback_goals(callback: CallbackQuery) -> None:
    """Розділ цілей."""
    await callback.message.edit_text(
        "🎯 <b>Цілі</b>\n\n"
        "🚧 Цей розділ у розробці...",
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "menu:habits")
async def callback_habits(callback: CallbackQuery) -> None:
    """Розділ звичок."""
    await callback.message.edit_text(
        "✅ <b>Звички</b>\n\n"
        "🚧 Цей розділ у розробці...",
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "menu:books")
async def callback_books(callback: CallbackQuery) -> None:
    """Розділ книг."""
    await callback.message.edit_text(
        "📚 <b>Книги</b>\n\n"
        "🚧 Цей розділ у розробці...",
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "menu:words")
async def callback_words(callback: CallbackQuery) -> None:
    """Розділ вивчення слів."""
    await callback.message.edit_text(
        "🇩🇪 <b>Вивчення слів</b>\n\n"
        "🚧 Цей розділ у розробці...",
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "menu:stats")
async def callback_stats(callback: CallbackQuery) -> None:
    """Розділ статистики."""
    await callback.message.edit_text(
        "📊 <b>Статистика</b>\n\n"
        "🚧 Цей розділ у розробці...",
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "menu:settings")
async def callback_settings(callback: CallbackQuery) -> None:
    """Розділ налаштувань."""
    await callback.message.edit_text(
        "⚙️ <b>Налаштування</b>\n\n"
        "🚧 Цей розділ у розробці...",
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()
