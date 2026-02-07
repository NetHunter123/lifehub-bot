"""
Inline клавіатури для задач.
LifeHub Bot v4.0
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict, Any


def get_task_actions(task_id: int, is_completed: bool = False) -> InlineKeyboardMarkup:
    """Дії для задачі."""
    builder = InlineKeyboardBuilder()
    
    if not is_completed:
        builder.button(text="✅ Виконати", callback_data=f"task:done:{task_id}")
    else:
        builder.button(text="↩️ Повернути", callback_data=f"task:undone:{task_id}")
    
    builder.button(text="✏️", callback_data=f"task:edit:{task_id}")
    builder.button(text="🗑", callback_data=f"task:delete:{task_id}")
    
    builder.adjust(1, 2)
    return builder.as_markup()


def get_tasks_list(tasks: List[Dict[str, Any]], page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    """Список задач з пагінацією."""
    builder = InlineKeyboardBuilder()
    
    # Визначаємо діапазон
    start = page * per_page
    end = start + per_page
    page_tasks = tasks[start:end]
    
    # Кнопки задач
    for task in page_tasks:
        status = "✅" if task['is_completed'] else "⬜"
        priority_icons = ["🔴", "🟠", "🟡", "🟢"]
        priority = priority_icons[task.get('priority', 2)]
        
        text = f"{status} {priority} {task['title'][:30]}"
        builder.button(text=text, callback_data=f"task:view:{task['id']}")
    
    builder.adjust(1)
    
    # Пагінація
    pagination = []
    total_pages = (len(tasks) + per_page - 1) // per_page
    
    if page > 0:
        pagination.append(
            InlineKeyboardButton(text="◀️", callback_data=f"tasks:page:{page-1}")
        )
    
    pagination.append(
        InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="tasks:page:current")
    )
    
    if page < total_pages - 1:
        pagination.append(
            InlineKeyboardButton(text="▶️", callback_data=f"tasks:page:{page+1}")
        )
    
    if total_pages > 1:
        builder.row(*pagination)
    
    # Кнопка додавання
    builder.row(InlineKeyboardButton(text="➕ Додати задачу", callback_data="task:add"))
    
    return builder.as_markup()


def get_priority_keyboard() -> InlineKeyboardMarkup:
    """Вибір пріоритету."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🔴 Терміново", callback_data="task:priority:0")
    builder.button(text="🟠 Високий", callback_data="task:priority:1")
    builder.button(text="🟡 Середній", callback_data="task:priority:2")
    builder.button(text="🟢 Низький", callback_data="task:priority:3")
    
    builder.adjust(2)
    return builder.as_markup()


def get_deadline_keyboard() -> InlineKeyboardMarkup:
    """Вибір дедлайну."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📅 Сьогодні", callback_data="task:deadline:today")
    builder.button(text="📅 Завтра", callback_data="task:deadline:tomorrow")
    builder.button(text="📅 Цей тиждень", callback_data="task:deadline:week")
    builder.button(text="📅 Без дедлайну", callback_data="task:deadline:none")
    builder.button(text="📅 Ввести дату", callback_data="task:deadline:custom")
    builder.button(text="❌ Скасувати", callback_data="task:cancel")
    
    builder.adjust(2, 2, 2)
    return builder.as_markup()


def get_time_keyboard() -> InlineKeyboardMarkup:
    """Вибір часу."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🌅 09:00", callback_data="task:time:09:00")
    builder.button(text="☀️ 14:00", callback_data="task:time:14:00")
    builder.button(text="🌆 18:00", callback_data="task:time:18:00")
    builder.button(text="⏰ Ввести час", callback_data="task:time:custom")
    builder.button(text="⏭ Без часу", callback_data="task:time:none")
    
    builder.adjust(3, 2)
    return builder.as_markup()


def get_goal_keyboard(projects: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Вибір проєкту для прив'язки."""
    builder = InlineKeyboardBuilder()
    
    for project in projects[:10]:
        builder.button(
            text=f"📁 {project['title'][:25]}",
            callback_data=f"task:goal:{project['id']}"
        )
    
    builder.button(text="⏭ Без проєкту", callback_data="task:goal:none")
    
    builder.adjust(1)
    return builder.as_markup()


def get_recurring_keyboard() -> InlineKeyboardMarkup:
    """Вибір типу повторення."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📅 Щодня", callback_data="task:recurring:daily")
    builder.button(text="📅 По буднях", callback_data="task:recurring:weekdays")
    builder.button(text="📅 Обрати дні", callback_data="task:recurring:custom")
    builder.button(text="⏭ Не повторювати", callback_data="task:recurring:none")
    
    builder.adjust(2, 2)
    return builder.as_markup()


def get_weekdays_inline(selected: List[int] = None) -> InlineKeyboardMarkup:
    """Inline вибір днів тижня."""
    selected = selected or []
    builder = InlineKeyboardBuilder()
    
    days = [
        ("Пн", 1), ("Вт", 2), ("Ср", 3), ("Чт", 4),
        ("Пт", 5), ("Сб", 6), ("Нд", 7)
    ]
    
    for name, num in days:
        mark = "✅" if num in selected else "⬜"
        builder.button(text=f"{mark} {name}", callback_data=f"task:day:{num}")
    
    builder.button(text="✅ Готово", callback_data="task:days:done")
    
    builder.adjust(4, 3, 1)
    return builder.as_markup()


def get_delete_confirm(task_id: int) -> InlineKeyboardMarkup:
    """Підтвердження видалення."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✅ Так, видалити", callback_data=f"task:delete_confirm:{task_id}")
    builder.button(text="❌ Скасувати", callback_data=f"task:view:{task_id}")
    
    builder.adjust(2)
    return builder.as_markup()
