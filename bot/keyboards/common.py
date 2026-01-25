"""
Загальні inline клавіатури.
Вибір мови, підтвердження, тощо.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.locales import t


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура вибору мови."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🇺🇦 Українська", callback_data="lang:uk"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
    )
    builder.row(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇩🇪 Deutsch", callback_data="lang:de"),
    )
    
    return builder.as_markup()


def get_confirm_keyboard(lang: str, action_data: str) -> InlineKeyboardMarkup:
    """
    Клавіатура підтвердження дії.
    
    Args:
        lang: Код мови
        action_data: Дані для callback (наприклад, "delete:5")
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=t("btn_yes", lang),
            callback_data=f"confirm:{action_data}"
        ),
        InlineKeyboardButton(
            text=t("btn_no", lang),
            callback_data="cancel"
        )
    )
    return builder.as_markup()


def get_back_keyboard(lang: str, callback_data: str = "menu:main") -> InlineKeyboardMarkup:
    """Кнопка назад."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=t("btn_back", lang),
            callback_data=callback_data
        )
    )
    return builder.as_markup()
