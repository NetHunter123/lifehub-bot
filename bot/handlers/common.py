"""
Загальні обробники команд.
/start, /help, /menu, /language
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from bot.keyboards.menu import get_main_menu_keyboard, get_back_to_menu_keyboard
from bot.keyboards.reply import get_main_reply_keyboard
from bot.keyboards.common import get_language_keyboard
from bot.locales import t, get_user_lang, set_user_lang
from bot.database import queries

router = Router()


# ============== КОМАНДИ ==============

@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Обробник команди /start."""
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    
    await message.answer(
        t("welcome", lang),
        reply_markup=get_main_reply_keyboard(lang)
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Обробник команди /help."""
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    
    help_text = f"{t('help_title', lang)}\n\n"
    help_text += f"{t('help_general', lang)}\n\n"
    help_text += f"{t('help_tasks', lang)}\n\n"
    help_text += f"{t('help_goals', lang)}\n\n"
    help_text += f"{t('help_habits', lang)}"
    
    await message.answer(
        help_text,
        reply_markup=get_back_to_menu_keyboard(lang)
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    """Обробник команди /menu."""
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    
    await message.answer(
        t("menu_title", lang),
        reply_markup=get_main_menu_keyboard(lang)
    )


@router.message(Command("language"))
async def cmd_language(message: Message) -> None:
    """Вибір мови."""
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    
    await message.answer(
        t("language_select", lang),
        reply_markup=get_language_keyboard()
    )


@router.callback_query(F.data.startswith("lang:"))
async def callback_set_language(callback: CallbackQuery) -> None:
    """Встановлення мови."""
    lang_code = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    # Оновлюємо в кеші
    set_user_lang(user_id, lang_code)
    
    # Оновлюємо в БД
    await queries.update_user_language(user_id, lang_code)
    
    # Відповідаємо новою мовою
    await callback.message.edit_text(t("language_changed", lang_code))
    
    # Оновлюємо reply клавіатуру
    await callback.message.answer(
        t("welcome", lang_code),
        reply_markup=get_main_reply_keyboard(lang_code)
    )
    await callback.answer()


# ============== CALLBACK HANDLERS ==============

@router.callback_query(F.data == "menu:main")
async def callback_main_menu(callback: CallbackQuery) -> None:
    """Повернення до головного меню."""
    lang = get_user_lang(callback.from_user.id)
    
    await callback.message.edit_text(
        t("menu_title", lang),
        reply_markup=get_main_menu_keyboard(lang)
    )
    await callback.answer()


@router.callback_query(F.data == "menu:tasks")
async def callback_tasks(callback: CallbackQuery) -> None:
    """Розділ задач."""
    lang = get_user_lang(callback.from_user.id)
    await callback.message.edit_text(
        f"{t('btn_tasks', lang)}\n\n{t('section_in_dev', lang)}\n\n"
        f"Скористайся командою /task_add",
        reply_markup=get_back_to_menu_keyboard(lang)
    )
    await callback.answer()


@router.callback_query(F.data == "menu:goals")
async def callback_goals(callback: CallbackQuery) -> None:
    """Розділ цілей."""
    lang = get_user_lang(callback.from_user.id)
    await callback.message.edit_text(
        f"{t('btn_goals', lang)}\n\n{t('section_in_dev', lang)}",
        reply_markup=get_back_to_menu_keyboard(lang)
    )
    await callback.answer()


@router.callback_query(F.data == "menu:habits")
async def callback_habits(callback: CallbackQuery) -> None:
    """Розділ звичок."""
    lang = get_user_lang(callback.from_user.id)
    await callback.message.edit_text(
        f"{t('btn_habits', lang)}\n\n{t('section_in_dev', lang)}",
        reply_markup=get_back_to_menu_keyboard(lang)
    )
    await callback.answer()


@router.callback_query(F.data == "menu:books")
async def callback_books(callback: CallbackQuery) -> None:
    """Розділ книг."""
    lang = get_user_lang(callback.from_user.id)
    await callback.message.edit_text(
        f"{t('btn_books', lang)}\n\n{t('section_in_dev', lang)}",
        reply_markup=get_back_to_menu_keyboard(lang)
    )
    await callback.answer()


@router.callback_query(F.data == "menu:words")
async def callback_words(callback: CallbackQuery) -> None:
    """Розділ вивчення слів."""
    lang = get_user_lang(callback.from_user.id)
    await callback.message.edit_text(
        f"{t('btn_words', lang)}\n\n{t('section_in_dev', lang)}",
        reply_markup=get_back_to_menu_keyboard(lang)
    )
    await callback.answer()


@router.callback_query(F.data == "menu:stats")
async def callback_stats(callback: CallbackQuery) -> None:
    """Розділ статистики."""
    lang = get_user_lang(callback.from_user.id)
    await callback.message.edit_text(
        f"{t('btn_stats', lang)}\n\n{t('section_in_dev', lang)}",
        reply_markup=get_back_to_menu_keyboard(lang)
    )
    await callback.answer()


@router.callback_query(F.data == "menu:settings")
async def callback_settings(callback: CallbackQuery) -> None:
    """Розділ налаштувань."""
    lang = get_user_lang(callback.from_user.id)
    await callback.message.edit_text(
        f"{t('btn_settings', lang)}\n\n{t('section_in_dev', lang)}",
        reply_markup=get_back_to_menu_keyboard(lang)
    )
    await callback.answer()
