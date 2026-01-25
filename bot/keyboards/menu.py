"""
Inline клавіатури меню.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.locales import t


def get_main_menu_keyboard(lang: str = 'en') -> InlineKeyboardMarkup:
    """Головне меню бота."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text=t("btn_tasks", lang), callback_data="menu:tasks"),
        InlineKeyboardButton(text=t("btn_goals", lang), callback_data="menu:goals")
    )
    builder.row(
        InlineKeyboardButton(text=t("btn_habits", lang), callback_data="menu:habits"),
        InlineKeyboardButton(text=t("btn_books", lang), callback_data="menu:books")
    )
    builder.row(
        InlineKeyboardButton(text=t("btn_words", lang), callback_data="menu:words"),
        InlineKeyboardButton(text=t("btn_stats", lang), callback_data="menu:stats")
    )
    builder.row(
        InlineKeyboardButton(text=t("btn_settings", lang), callback_data="menu:settings")
    )
    
    return builder.as_markup()


def get_back_to_menu_keyboard(lang: str = 'en') -> InlineKeyboardMarkup:
    """Кнопка повернення до меню."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=t("btn_back_menu", lang),
            callback_data="menu:main"
        )
    )
    return builder.as_markup()
