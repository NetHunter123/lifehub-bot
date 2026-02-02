"""
Базові обробники: /start, /help, /menu, /language.
LifeHub Bot v4.0
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from bot.database import queries
from bot.keyboards.reply import get_main_menu
from bot.locales import uk


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обробник /start."""
    await state.clear()
    
    user_id = message.from_user.id
    
    # Створюємо налаштування якщо немає
    settings = await queries.get_user_settings(user_id)
    if not settings:
        await queries.upsert_user_settings(user_id, language='uk')
    
    await message.answer(
        uk.WELCOME,
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обробник /help."""
    await message.answer(
        uk.HELP,
        parse_mode="HTML"
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    """Обробник /menu."""
    await state.clear()
    await message.answer(
        "🏠 <b>Головне меню</b>",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )


# ═══════════════════════════════════════════════════════════════════════════════
#                         ОБРОБКА КНОПОК МЕНЮ
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(F.text == "📅 Сьогодні")
async def btn_today(message: Message):
    """Кнопка Сьогодні → /today."""
    from bot.handlers.today import cmd_today
    await cmd_today(message)


@router.message(F.text == "📋 Задачі")
async def btn_tasks(message: Message):
    """Кнопка Задачі → /tasks."""
    from bot.handlers.tasks import cmd_tasks
    await cmd_tasks(message)


@router.message(F.text == "🎯 Цілі")
async def btn_goals(message: Message):
    """Кнопка Цілі → /goals."""
    from bot.handlers.goals import cmd_goals
    await cmd_goals(message)


@router.message(F.text == "✅ Звички")
async def btn_habits(message: Message):
    """Кнопка Звички → /habits."""
    from bot.handlers.habits import cmd_habits
    await cmd_habits(message)


@router.message(F.text == "📚 Книги")
async def btn_books(message: Message):
    """Кнопка Книги → /books."""
    await message.answer("📚 <b>Книги</b>\n\n<i>В розробці...</i>", parse_mode="HTML")


@router.message(F.text == "⚙️ Налаштування")
async def btn_settings(message: Message):
    """Кнопка Налаштування → /settings."""
    await message.answer("⚙️ <b>Налаштування</b>\n\n<i>В розробці...</i>", parse_mode="HTML")


# ═══════════════════════════════════════════════════════════════════════════════
#                         ОБРОБКА СКАСУВАННЯ
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(F.text == "❌ Скасувати")
async def cancel_action(message: Message, state: FSMContext):
    """Скасування поточної дії."""
    current_state = await state.get_state()
    
    if current_state is not None:
        await state.clear()
        await message.answer(
            uk.CANCELLED,
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            "Немає активної дії для скасування.",
            reply_markup=get_main_menu()
        )


@router.callback_query(F.data.endswith(":cancel"))
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    """Скасування через inline кнопку."""
    await state.clear()
    await callback.message.edit_text(uk.CANCELLED)
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════════
#                         МОВА
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(Command("language"))
async def cmd_language(message: Message):
    """Вибір мови."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇦 Українська", callback_data="lang:uk")
    builder.button(text="🇬🇧 English", callback_data="lang:en")
    builder.adjust(2)
    
    await message.answer(
        "🌐 <b>Оберіть мову / Choose language:</b>",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("lang:"))
async def callback_language(callback: CallbackQuery):
    """Зміна мови."""
    lang = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    await queries.upsert_user_settings(user_id, language=lang)
    
    lang_names = {'uk': 'Українська', 'en': 'English'}
    await callback.message.edit_text(
        f"✅ Мову змінено на: {lang_names.get(lang, lang)}"
    )
    await callback.answer()
