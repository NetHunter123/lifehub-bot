"""
Inline клавіатури для роботи з задачами.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from enum import Enum
from typing import Optional


# ============== CALLBACK DATA ==============

class TaskAction(str, Enum):
    """Дії з задачами."""
    view = "v"
    complete = "c"
    delete = "d"
    edit = "e"
    set_priority = "p"
    set_deadline = "dl"


class TaskCallback(CallbackData, prefix="task"):
    """Callback data для задач."""
    action: TaskAction
    task_id: int


class PriorityCallback(CallbackData, prefix="pri"):
    """Callback data для вибору пріоритету."""
    priority: int
    task_id: Optional[int] = None  # None = нова задача


class DeadlineCallback(CallbackData, prefix="ddl"):
    """Callback data для вибору дедлайну."""
    option: str  # today, tomorrow, week, pick, none
    task_id: Optional[int] = None


# ============== КЛАВІАТУРИ ==============

def get_priority_keyboard(task_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Клавіатура вибору пріоритету."""
    builder = InlineKeyboardBuilder()
    
    priorities = [
        ("🔴 Терміново", 0),
        ("🟠 Високий", 1),
        ("🟡 Середній", 2),
        ("🟢 Низький", 3),
    ]
    
    for text, priority in priorities:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=PriorityCallback(priority=priority, task_id=task_id).pack()
        ))
    
    builder.adjust(2)  # 2 кнопки в ряд
    return builder.as_markup()


def get_deadline_keyboard(task_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Клавіатура вибору дедлайну."""
    builder = InlineKeyboardBuilder()
    
    options = [
        ("📅 Сьогодні", "today"),
        ("📆 Завтра", "tomorrow"),
        ("🗓 Цей тиждень", "week"),
        ("✏️ Обрати дату", "pick"),
        ("❌ Без дедлайну", "none"),
    ]
    
    for text, option in options:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=DeadlineCallback(option=option, task_id=task_id).pack()
        ))
    
    builder.adjust(2)
    return builder.as_markup()


def get_task_actions_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Клавіатура дій з конкретною задачею."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✅ Виконано",
            callback_data=TaskCallback(action=TaskAction.complete, task_id=task_id).pack()
        ),
        InlineKeyboardButton(
            text="✏️ Редагувати",
            callback_data=TaskCallback(action=TaskAction.edit, task_id=task_id).pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑 Видалити",
            callback_data=TaskCallback(action=TaskAction.delete, task_id=task_id).pack()
        )
    )
    
    return builder.as_markup()


def get_tasks_list_keyboard(tasks: list, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    """Клавіатура зі списком задач + пагінація."""
    builder = InlineKeyboardBuilder()
    
    # Задачі на поточній сторінці
    start = page * per_page
    end = start + per_page
    page_tasks = tasks[start:end]
    
    for task in page_tasks:
        # Емодзі пріоритету
        priority_emoji = ["🔴", "🟠", "🟡", "🟢"][task["priority"]]
        status_emoji = "✅" if task["is_completed"] else "⬜"
        
        builder.row(InlineKeyboardButton(
            text=f"{status_emoji} {priority_emoji} {task['title'][:30]}",
            callback_data=TaskCallback(action=TaskAction.view, task_id=task["id"]).pack()
        ))
    
    # Пагінація
    total_pages = (len(tasks) + per_page - 1) // per_page
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"page:{page-1}"))
        nav_buttons.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"page:{page+1}"))
        builder.row(*nav_buttons)
    
    # Кнопка додавання
    builder.row(InlineKeyboardButton(text="➕ Додати задачу", callback_data="task:add"))
    
    return builder.as_markup()


def get_confirm_keyboard(task_id: int, action: str) -> InlineKeyboardMarkup:
    """Клавіатура підтвердження дії."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Так", callback_data=f"confirm:{action}:{task_id}"),
        InlineKeyboardButton(text="❌ Ні", callback_data="cancel")
    )
    
    return builder.as_markup()
