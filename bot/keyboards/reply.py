"""
Reply клавіатури (постійне меню внизу екрану).
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from bot.locales import t


def get_main_reply_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    """Головне меню (постійне внизу екрану)."""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text=t("btn_tasks", lang)),
        KeyboardButton(text=t("btn_goals", lang))
    )
    builder.row(
        KeyboardButton(text=t("btn_habits", lang)),
        KeyboardButton(text=t("btn_books", lang))
    )
    builder.row(
        KeyboardButton(text=t("btn_words", lang)),
        KeyboardButton(text=t("btn_stats", lang))
    )
    
    return builder.as_markup(resize_keyboard=True, is_persistent=True)


def get_cancel_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    """Клавіатура з кнопкою скасування."""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=t("btn_cancel", lang)))
    return builder.as_markup(resize_keyboard=True)


def get_skip_cancel_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    """Клавіатура з кнопками пропустити та скасувати."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=t("btn_skip", lang)),
        KeyboardButton(text=t("btn_cancel", lang))
    )
    return builder.as_markup(resize_keyboard=True)
