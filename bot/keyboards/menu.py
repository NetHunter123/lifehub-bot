"""
Клавіатури для бота.
Inline та Reply клавіатури.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Головне меню бота."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📋 Задачі", callback_data="menu:tasks"),
        InlineKeyboardButton(text="🎯 Цілі", callback_data="menu:goals")
    )
    builder.row(
        InlineKeyboardButton(text="✅ Звички", callback_data="menu:habits"),
        InlineKeyboardButton(text="📚 Книги", callback_data="menu:books")
    )
    builder.row(
        InlineKeyboardButton(text="🇩🇪 Слова", callback_data="menu:words"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="menu:stats")
    )
    builder.row(
        InlineKeyboardButton(text="⚙️ Налаштування", callback_data="menu:settings")
    )
    
    return builder.as_markup()


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Кнопка повернення до меню."""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="◀️ Назад до меню", callback_data="menu:main"))
    return builder.as_markup()
