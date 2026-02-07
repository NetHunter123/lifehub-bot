"""
Reply клавіатури (постійне меню).
LifeHub Bot v4.0
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def get_main_menu() -> ReplyKeyboardMarkup:
    """Головне меню."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📅 Сьогодні"),
                KeyboardButton(text="📋 Задачі"),
            ],
            [
                KeyboardButton(text="🎯 Цілі"),
                KeyboardButton(text="✅ Звички"),
            ],
            [
                KeyboardButton(text="📚 Книги"),
                KeyboardButton(text="⚙️ Налаштування"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Обери дію..."
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавіатура зі скасуванням."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Скасувати")]
        ],
        resize_keyboard=True
    )


def get_skip_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавіатура з пропуском і скасуванням."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="⏭ Пропустити"),
                KeyboardButton(text="❌ Скасувати")
            ]
        ],
        resize_keyboard=True
    )


def get_confirm_keyboard() -> ReplyKeyboardMarkup:
    """Клавіатура підтвердження."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="✅ Підтвердити"),
                KeyboardButton(text="❌ Скасувати")
            ]
        ],
        resize_keyboard=True
    )


def get_yes_no_keyboard() -> ReplyKeyboardMarkup:
    """Клавіатура Так/Ні."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Так"),
                KeyboardButton(text="Ні")
            ]
        ],
        resize_keyboard=True
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    """Видалити клавіатуру."""
    return ReplyKeyboardRemove()
