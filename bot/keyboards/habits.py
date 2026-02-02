"""
Inline клавіатури для звичок.
LifeHub Bot v4.0
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict, Any


def get_habits_today(habits: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Список звичок на сьогодні з швидкими діями."""
    builder = InlineKeyboardBuilder()
    
    for habit in habits:
        # Визначаємо статус
        today_status = habit.get('today_status')
        if today_status == 'done':
            status = "✅"
        elif today_status == 'skipped':
            status = "⏭"
        else:
            status = "⬜"
        
        streak = habit.get('current_streak', 0)
        streak_text = f" 🔥{streak}" if streak > 0 else ""
        
        # Час якщо є
        time_text = ""
        if habit.get('reminder_time'):
            time_text = f" {habit['reminder_time']}"
        
        builder.button(
            text=f"{status}{time_text} {habit['title'][:20]}{streak_text}",
            callback_data=f"habit:view:{habit['id']}"
        )
    
    builder.adjust(1)
    
    # Кнопки дій
    builder.row(
        InlineKeyboardButton(text="✅ Всі виконані", callback_data="habit:all_done"),
        InlineKeyboardButton(text="➕ Додати", callback_data="habit:add")
    )
    
    return builder.as_markup()


def get_habit_quick_actions(habit_id: int, is_done: bool = False) -> InlineKeyboardMarkup:
    """Швидкі дії для звички."""
    builder = InlineKeyboardBuilder()
    
    if not is_done:
        builder.button(text="✅ Виконано", callback_data=f"habit:done:{habit_id}")
        builder.button(text="⏭ Пропустити", callback_data=f"habit:skip:{habit_id}")
    else:
        builder.button(text="↩️ Скасувати", callback_data=f"habit:undone:{habit_id}")
    
    builder.adjust(2)
    return builder.as_markup()


def get_habit_actions(habit_id: int) -> InlineKeyboardMarkup:
    """Повні дії для звички."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✅ Виконано", callback_data=f"habit:done:{habit_id}")
    builder.button(text="⏭ Пропустити", callback_data=f"habit:skip:{habit_id}")
    builder.button(text="📊 Статистика", callback_data=f"habit:stats:{habit_id}")
    builder.button(text="✏️ Редагувати", callback_data=f"habit:edit:{habit_id}")
    builder.button(text="🗑 Видалити", callback_data=f"habit:delete:{habit_id}")
    builder.button(text="◀️ Назад", callback_data="habits:today")
    
    builder.adjust(2, 2, 2)
    return builder.as_markup()


def get_frequency_keyboard() -> InlineKeyboardMarkup:
    """Вибір частоти звички."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📅 Щодня", callback_data="habit:freq:daily")
    builder.button(text="📅 По буднях (Пн-Пт)", callback_data="habit:freq:weekdays")
    builder.button(text="📅 Обрати дні", callback_data="habit:freq:custom")
    builder.button(text="❌ Скасувати", callback_data="habit:cancel")
    
    builder.adjust(1)
    return builder.as_markup()


def get_weekdays_keyboard(selected: List[int] = None) -> InlineKeyboardMarkup:
    """Вибір днів тижня."""
    selected = selected or []
    builder = InlineKeyboardBuilder()
    
    days = [
        ("Пн", 1), ("Вт", 2), ("Ср", 3), ("Чт", 4),
        ("Пт", 5), ("Сб", 6), ("Нд", 7)
    ]
    
    for name, num in days:
        mark = "✅" if num in selected else "⬜"
        builder.button(
            text=f"{mark} {name}",
            callback_data=f"habit:day:{num}"
        )
    
    builder.button(text="✅ Готово", callback_data="habit:days:done")
    
    builder.adjust(4, 3, 1)
    return builder.as_markup()


def get_time_keyboard() -> InlineKeyboardMarkup:
    """Вибір часу нагадування."""
    builder = InlineKeyboardBuilder()
    
    times = [
        ("🌅 06:00", "06:00"),
        ("🌅 07:00", "07:00"),
        ("🌅 08:00", "08:00"),
        ("☀️ 12:00", "12:00"),
        ("🌆 18:00", "18:00"),
        ("🌙 21:00", "21:00"),
    ]
    
    for text, time in times:
        builder.button(text=text, callback_data=f"habit:time:{time}")
    
    builder.button(text="⏰ Ввести час", callback_data="habit:time:custom")
    builder.button(text="⏭ Без часу", callback_data="habit:time:none")
    
    builder.adjust(3, 3, 2)
    return builder.as_markup()


def get_duration_keyboard() -> InlineKeyboardMarkup:
    """Вибір тривалості."""
    builder = InlineKeyboardBuilder()
    
    durations = [
        ("5 хв", 5), ("10 хв", 10), ("15 хв", 15),
        ("20 хв", 20), ("30 хв", 30), ("60 хв", 60),
    ]
    
    for text, mins in durations:
        builder.button(text=text, callback_data=f"habit:duration:{mins}")
    
    builder.button(text="⏭ Не вказувати", callback_data="habit:duration:none")
    
    builder.adjust(3, 3, 1)
    return builder.as_markup()


def get_stats_keyboard(habit_id: int) -> InlineKeyboardMarkup:
    """Клавіатура статистики."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📅 Тиждень", callback_data=f"habit:stats_week:{habit_id}")
    builder.button(text="📅 Місяць", callback_data=f"habit:stats_month:{habit_id}")
    builder.button(text="📅 Всі дані", callback_data=f"habit:stats_all:{habit_id}")
    builder.button(text="◀️ Назад", callback_data=f"habit:view:{habit_id}")
    
    builder.adjust(3, 1)
    return builder.as_markup()


def get_delete_confirm(habit_id: int) -> InlineKeyboardMarkup:
    """Підтвердження видалення."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✅ Так, видалити", callback_data=f"habit:delete_confirm:{habit_id}")
    builder.button(text="❌ Скасувати", callback_data=f"habit:view:{habit_id}")
    
    builder.adjust(2)
    return builder.as_markup()
