"""
Reply клавіатури (постійне меню внизу екрану).
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Головне меню (постійне внизу екрану)."""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text="📋 Задачі"),
        KeyboardButton(text="🎯 Цілі")
    )
    builder.row(
        KeyboardButton(text="✅ Звички"),
        KeyboardButton(text="📚 Книги")
    )
    builder.row(
        KeyboardButton(text="🇩🇪 Слова"),
        KeyboardButton(text="📊 Статистика")
    )
    
    return builder.as_markup(resize_keyboard=True, is_persistent=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавіатура з кнопкою скасування."""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Скасувати"))
    return builder.as_markup(resize_keyboard=True)


def get_skip_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавіатура з кнопками пропустити та скасувати."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="⏭ Пропустити"),
        KeyboardButton(text="❌ Скасувати")
    )
    return builder.as_markup(resize_keyboard=True)
