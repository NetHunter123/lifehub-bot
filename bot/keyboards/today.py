"""
Inline клавіатури для /today dashboard.
LifeHub Bot v4.0
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_today_keyboard(sort_mode: str = 'time') -> InlineKeyboardMarkup:
    """Головна клавіатура /today."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="➕ Задача", callback_data="task:add")
    builder.button(text="✅ Звички", callback_data="habits:today")
    
    if sort_mode == 'time':
        builder.button(text="📊 По типу", callback_data="today:sort:type")
    else:
        builder.button(text="🕐 По часу", callback_data="today:sort:time")
    
    builder.button(text="🔄", callback_data="today:refresh")
    
    builder.adjust(2, 2)
    return builder.as_markup()


def get_recurring_task_actions(task_id: int, occurrence_status: str) -> InlineKeyboardMarkup:
    """Дії для recurring task."""
    builder = InlineKeyboardBuilder()
    
    if occurrence_status == 'pending':
        builder.button(text="✅ Виконано", callback_data=f"recurring:done:{task_id}")
        builder.button(text="⏭ Пропустити", callback_data=f"recurring:skip:{task_id}")
    elif occurrence_status == 'done':
        builder.button(text="↩️ Скасувати", callback_data=f"recurring:undone:{task_id}")
    elif occurrence_status == 'skipped':
        builder.button(text="↩️ Повернути", callback_data=f"recurring:unskip:{task_id}")
    
    builder.button(text="📊 Статистика", callback_data=f"recurring:stats:{task_id}")
    
    builder.adjust(2, 1)
    return builder.as_markup()


def get_today_item_actions(item_type: str, item_id: int, status: str = None) -> InlineKeyboardMarkup:
    """Універсальні дії для елемента в /today."""
    builder = InlineKeyboardBuilder()
    
    if item_type == 'habit':
        if status != 'done':
            builder.button(text="✅", callback_data=f"habit:done:{item_id}")
            builder.button(text="⏭", callback_data=f"habit:skip:{item_id}")
        else:
            builder.button(text="↩️", callback_data=f"habit:undone:{item_id}")
    elif item_type == 'task':
        if status != 'completed':
            builder.button(text="✅", callback_data=f"task:done:{item_id}")
        else:
            builder.button(text="↩️", callback_data=f"task:undone:{item_id}")
    elif item_type == 'recurring':
        if status == 'pending':
            builder.button(text="✅", callback_data=f"recurring:done:{item_id}")
            builder.button(text="⏭", callback_data=f"recurring:skip:{item_id}")
        elif status == 'done':
            builder.button(text="↩️", callback_data=f"recurring:undone:{item_id}")
        elif status == 'skipped':
            builder.button(text="↩️", callback_data=f"recurring:unskip:{item_id}")
    
    builder.adjust(2)
    return builder.as_markup()


def get_morning_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура ранкового огляду."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="💪 Почати день", callback_data="today:start_day")
    builder.button(text="⏰ Відкласти 30 хв", callback_data="today:snooze:30")
    
    builder.adjust(2)
    return builder.as_markup()


def get_evening_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура вечірнього підсумку."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📝 Нотатка дня", callback_data="today:note")
    builder.button(text="📅 Планувати завтра", callback_data="today:plan_tomorrow")
    
    builder.adjust(2)
    return builder.as_markup()
