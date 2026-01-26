"""
Inline клавіатури для роботи з задачами.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from enum import Enum
from typing import Optional

from bot.locales import t


class TaskAction(str, Enum):
    view = "v"
    complete = "c"
    delete = "d"
    edit = "e"


class TaskCallback(CallbackData, prefix="task"):
    action: TaskAction
    task_id: int


class PriorityCallback(CallbackData, prefix="pri"):
    priority: int
    task_id: Optional[int] = None


class DeadlineCallback(CallbackData, prefix="ddl"):
    option: str  # today, tomorrow, week, custom, none
    task_id: Optional[int] = None


class TimeCallback(CallbackData, prefix="time"):
    hour: Optional[int] = None
    custom: bool = False  # Якщо True — перехід до ручного вводу


class DurationCallback(CallbackData, prefix="dur"):
    minutes: Optional[int] = None
    custom: bool = False  # Якщо True — перехід до ручного вводу


def get_priority_keyboard(lang: str = 'en', task_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Клавіатура вибору пріоритету."""
    builder = InlineKeyboardBuilder()
    priorities = [
        (t("priority_urgent", lang), 0),
        (t("priority_high", lang), 1),
        (t("priority_medium", lang), 2),
        (t("priority_low", lang), 3),
    ]
    for text, priority in priorities:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=PriorityCallback(priority=priority, task_id=task_id).pack()
        ))
    builder.adjust(2)
    return builder.as_markup()


def get_deadline_keyboard(lang: str = 'en', task_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Клавіатура вибору дедлайну з можливістю обрати довільну дату."""
    builder = InlineKeyboardBuilder()
    options = [
        (t("deadline_today", lang), "today"),
        (t("deadline_tomorrow", lang), "tomorrow"),
        (t("deadline_week", lang), "week"),
        (t("deadline_custom", lang), "custom"),  # Обрати дату
        (t("deadline_none", lang), "none"),
    ]
    for text, option in options:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=DeadlineCallback(option=option, task_id=task_id).pack()
        ))
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def get_time_keyboard(lang: str = 'en') -> InlineKeyboardMarkup:
    """Клавіатура вибору часу з можливістю ввести свій."""
    builder = InlineKeyboardBuilder()
    times = [
        ("🌅 08:00", 8), ("🌅 09:00", 9),
        ("☀️ 10:00", 10), ("☀️ 11:00", 11),
        ("☀️ 12:00", 12), ("☀️ 13:00", 13),
        ("🌤 14:00", 14), ("🌤 15:00", 15),
        ("🌤 16:00", 16), ("🌤 17:00", 17),
        ("🌆 18:00", 18), ("🌙 20:00", 20),
    ]
    for text, hour in times:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=TimeCallback(hour=hour).pack()
        ))
    # Кнопка для кастомного часу
    builder.add(InlineKeyboardButton(
        text=t("time_custom", lang),
        callback_data=TimeCallback(custom=True).pack()
    ))
    # Без часу
    builder.add(InlineKeyboardButton(
        text=t("time_none", lang),
        callback_data=TimeCallback(hour=None).pack()
    ))
    builder.adjust(4, 4, 2)
    return builder.as_markup()


def get_duration_keyboard(lang: str = 'en') -> InlineKeyboardMarkup:
    """Клавіатура вибору тривалості з можливістю ввести свою."""
    builder = InlineKeyboardBuilder()
    durations = [
        (t("duration_15m", lang), 15),
        (t("duration_30m", lang), 30),
        (t("duration_45m", lang), 45),
        (t("duration_1h", lang), 60),
        (t("duration_1_5h", lang), 90),
        (t("duration_2h", lang), 120),
        (t("duration_3h", lang), 180),
        (t("duration_4h", lang), 240),
    ]
    for text, minutes in durations:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=DurationCallback(minutes=minutes).pack()
        ))
    # Кнопка для кастомної тривалості
    builder.add(InlineKeyboardButton(
        text=t("duration_custom", lang),
        callback_data=DurationCallback(custom=True).pack()
    ))
    # Без тривалості
    builder.add(InlineKeyboardButton(
        text=t("time_none", lang),
        callback_data=DurationCallback(minutes=None).pack()
    ))
    builder.adjust(4, 4, 2)
    return builder.as_markup()


def get_task_actions_keyboard(task_id: int, lang: str = 'en') -> InlineKeyboardMarkup:
    """Клавіатура дій з конкретною задачею."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=t("btn_done", lang),
            callback_data=TaskCallback(action=TaskAction.complete, task_id=task_id).pack()
        ),
        InlineKeyboardButton(
            text=t("btn_edit", lang),
            callback_data=TaskCallback(action=TaskAction.edit, task_id=task_id).pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn_delete", lang),
            callback_data=TaskCallback(action=TaskAction.delete, task_id=task_id).pack()
        ),
        InlineKeyboardButton(
            text=t("btn_back", lang),
            callback_data="tasks:back"
        )
    )
    return builder.as_markup()


def get_tasks_list_keyboard(tasks: list, lang: str = 'en', page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    """Клавіатура зі списком задач + пагінація."""
    builder = InlineKeyboardBuilder()

    if tasks:
        start = page * per_page
        end = start + per_page
        page_tasks = tasks[start:end]

        for task in page_tasks:
            priority_emoji = ["🔴", "🟠", "🟡", "🟢"][task["priority"]]
            status_emoji = "✅" if task["is_completed"] else "⬜"
            builder.row(InlineKeyboardButton(
                text=f"{status_emoji} {priority_emoji} {task['title'][:30]}",
                callback_data=TaskCallback(action=TaskAction.view, task_id=task["id"]).pack()
            ))

        total_pages = (len(tasks) + per_page - 1) // per_page
        if total_pages > 1:
            nav_buttons = []
            if page > 0:
                nav_buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"page:{page-1}"))
            nav_buttons.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
            if page < total_pages - 1:
                nav_buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"page:{page+1}"))
            builder.row(*nav_buttons)

    # ЗАВЖДИ показуємо кнопку додавання
    builder.row(InlineKeyboardButton(text=t("btn_add_task", lang), callback_data="task:add"))

    return builder.as_markup()


def get_confirm_keyboard(task_id: int, action: str, lang: str = 'en') -> InlineKeyboardMarkup:
    """Клавіатура підтвердження дії."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t("btn_yes", lang), callback_data=f"confirm:{action}:{task_id}"),
        InlineKeyboardButton(text=t("btn_no", lang), callback_data="cancel")
    )
    return builder.as_markup()


def get_what_next_keyboard(lang: str = 'en') -> InlineKeyboardMarkup:
    """Клавіатура 'Що далі?' після створення задачі."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t("btn_add_another", lang), callback_data="task:add"),
        InlineKeyboardButton(text=t("btn_view_tasks", lang), callback_data="tasks:view")
    )
    return builder.as_markup()
