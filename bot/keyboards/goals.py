"""
Клавіатури для роботи з цілями.
"""

from enum import Enum
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

from bot.locales import t


# ============== ТИПИ ЦІЛЕЙ ==============

class GoalType(str, Enum):
    """Типи цілей за періодом."""
    yearly = "yearly"
    quarterly = "quarterly"
    monthly = "monthly"
    weekly = "weekly"


GOAL_TYPE_EMOJI = {
    GoalType.yearly: "🎯",
    GoalType.quarterly: "📊",
    GoalType.monthly: "📅",
    GoalType.weekly: "📋",
}


# ============== CALLBACK DATA ==============

class GoalAction(str, Enum):
    """Дії з цілями."""
    view = "v"
    edit = "e"
    delete = "d"
    progress = "p"
    complete = "c"
    restore = "r"


class GoalCallback(CallbackData, prefix="goal"):
    """Callback для дій з ціллю."""
    action: GoalAction
    goal_id: int


class GoalTypeCallback(CallbackData, prefix="gtype"):
    """Callback для вибору типу цілі."""
    goal_type: GoalType


class GoalParentCallback(CallbackData, prefix="gparent"):
    """Callback для вибору батьківської цілі."""
    parent_id: int  # 0 = без батьківської


class GoalEditField(str, Enum):
    """Поля для редагування цілі."""
    title = "title"
    description = "description"
    deadline = "deadline"
    goal_type = "goal_type"


class GoalEditCallback(CallbackData, prefix="gedit"):
    """Callback для редагування поля цілі."""
    field: GoalEditField
    goal_id: int


# ============== КЛАВІАТУРИ ==============

def get_goal_type_keyboard(lang: str = 'en') -> InlineKeyboardMarkup:
    """Клавіатура вибору типу цілі."""
    builder = InlineKeyboardBuilder()
    
    types = [
        (f"🎯 {t('goal_type_yearly', lang)}", GoalType.yearly),
        (f"📊 {t('goal_type_quarterly', lang)}", GoalType.quarterly),
        (f"📅 {t('goal_type_monthly', lang)}", GoalType.monthly),
        (f"📋 {t('goal_type_weekly', lang)}", GoalType.weekly),
    ]
    
    for text, goal_type in types:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=GoalTypeCallback(goal_type=goal_type).pack()
        ))
    
    builder.adjust(2)
    return builder.as_markup()


def get_goal_parent_keyboard(goals: list, lang: str = 'en') -> InlineKeyboardMarkup:
    """Клавіатура вибору батьківської цілі."""
    builder = InlineKeyboardBuilder()
    
    # Кнопка "Без батьківської"
    builder.row(InlineKeyboardButton(
        text=t("goal_no_parent", lang),
        callback_data=GoalParentCallback(parent_id=0).pack()
    ))
    
    # Список існуючих цілей
    for goal in goals:
        emoji = GOAL_TYPE_EMOJI.get(GoalType(goal["goal_type"]), "🎯")
        builder.row(InlineKeyboardButton(
            text=f"{emoji} {goal['title'][:40]}",
            callback_data=GoalParentCallback(parent_id=goal["id"]).pack()
        ))
    
    return builder.as_markup()


def get_goal_deadline_keyboard(lang: str = 'en') -> InlineKeyboardMarkup:
    """Клавіатура вибору дедлайну для цілі."""
    builder = InlineKeyboardBuilder()
    
    options = [
        (t("deadline_end_week", lang), "end_week"),
        (t("deadline_end_month", lang), "end_month"),
        (t("deadline_end_quarter", lang), "end_quarter"),
        (t("deadline_end_year", lang), "end_year"),
        (t("deadline_custom", lang), "custom"),
        (t("deadline_none", lang), "none"),
    ]
    
    for text, option in options:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=f"goal_deadline:{option}"
        ))
    
    builder.adjust(2)
    return builder.as_markup()


def get_goals_list_keyboard(goals: list, lang: str = 'en', filter_type: str = "active") -> InlineKeyboardMarkup:
    """Клавіатура зі списком цілей."""
    builder = InlineKeyboardBuilder()
    
    if goals:
        for goal in goals:
            emoji = GOAL_TYPE_EMOJI.get(GoalType(goal["goal_type"]), "🎯")
            status = "✅" if goal.get("status") == "completed" else ""
            progress = goal.get("progress", 0)
            
            # Показуємо прогрес для активних цілей
            progress_bar = f" [{progress}%]" if goal.get("status") != "completed" else ""
            
            builder.row(InlineKeyboardButton(
                text=f"{status}{emoji} {goal['title'][:30]}{progress_bar}",
                callback_data=GoalCallback(action=GoalAction.view, goal_id=goal["id"]).pack()
            ))
    
    # Фільтри
    filters = []
    if filter_type != "active":
        filters.append(InlineKeyboardButton(
            text=t("filter_active", lang),
            callback_data="goals_filter:active"
        ))
    if filter_type != "completed":
        filters.append(InlineKeyboardButton(
            text=t("filter_completed", lang),
            callback_data="goals_filter:completed"
        ))
    if filter_type != "all":
        filters.append(InlineKeyboardButton(
            text=t("filter_all", lang),
            callback_data="goals_filter:all"
        ))
    
    if filters:
        builder.row(*filters)
    
    # Кнопка додавання
    builder.row(InlineKeyboardButton(
        text=t("btn_add_goal", lang),
        callback_data="goal:add"
    ))
    
    return builder.as_markup()


def get_goal_actions_keyboard(goal_id: int, lang: str = 'en', is_completed: bool = False) -> InlineKeyboardMarkup:
    """Клавіатура дій з ціллю."""
    builder = InlineKeyboardBuilder()
    
    if is_completed:
        # Для завершених цілей
        builder.row(
            InlineKeyboardButton(
                text=t("btn_restore", lang),
                callback_data=GoalCallback(action=GoalAction.restore, goal_id=goal_id).pack()
            )
        )
    else:
        # Для активних цілей
        builder.row(
            InlineKeyboardButton(
                text=t("btn_progress", lang),
                callback_data=GoalCallback(action=GoalAction.progress, goal_id=goal_id).pack()
            ),
            InlineKeyboardButton(
                text=t("btn_complete", lang),
                callback_data=GoalCallback(action=GoalAction.complete, goal_id=goal_id).pack()
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=t("btn_edit", lang),
                callback_data=GoalCallback(action=GoalAction.edit, goal_id=goal_id).pack()
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text=t("btn_delete", lang),
            callback_data=GoalCallback(action=GoalAction.delete, goal_id=goal_id).pack()
        ),
        InlineKeyboardButton(
            text=t("btn_back", lang),
            callback_data="goals:back"
        )
    )
    
    return builder.as_markup()


def get_goal_edit_keyboard(goal_id: int, lang: str = 'en') -> InlineKeyboardMarkup:
    """Клавіатура вибору поля для редагування цілі."""
    builder = InlineKeyboardBuilder()
    
    fields = [
        (t("edit_field_title", lang), GoalEditField.title),
        (t("edit_field_description", lang), GoalEditField.description),
        (t("edit_field_deadline", lang), GoalEditField.deadline),
        (t("edit_field_type", lang), GoalEditField.goal_type),
    ]
    
    for text, field in fields:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=GoalEditCallback(field=field, goal_id=goal_id).pack()
        ))
    
    builder.adjust(2)
    builder.row(InlineKeyboardButton(
        text=t("btn_back", lang),
        callback_data=GoalCallback(action=GoalAction.view, goal_id=goal_id).pack()
    ))
    
    return builder.as_markup()


def get_goal_confirm_keyboard(goal_id: int, action: str, lang: str = 'en') -> InlineKeyboardMarkup:
    """Клавіатура підтвердження дії з ціллю."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=t("btn_confirm", lang),
            callback_data=f"goal_confirm:{action}:{goal_id}"
        ),
        InlineKeyboardButton(
            text=t("btn_cancel", lang),
            callback_data="goals:back"
        )
    )
    return builder.as_markup()


def get_progress_keyboard(lang: str = 'en') -> InlineKeyboardMarkup:
    """Клавіатура швидкого вибору прогресу."""
    builder = InlineKeyboardBuilder()
    
    # Швидкі кнопки прогресу
    for progress in [10, 25, 50, 75, 100]:
        builder.add(InlineKeyboardButton(
            text=f"{progress}%",
            callback_data=f"goal_progress_quick:{progress}"
        ))
    
    builder.adjust(5)
    
    # Кнопка для ручного вводу
    builder.row(InlineKeyboardButton(
        text=t("progress_custom", lang),
        callback_data="goal_progress_custom"
    ))
    
    return builder.as_markup()
