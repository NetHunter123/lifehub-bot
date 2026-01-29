"""
Клавіатури для роботи з цілями v3.
5 структурних типів: task, project, habit, target, metric.
"""

from enum import Enum
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from bot.locales import t


# ============== ТИПИ ==============

class GoalType(str, Enum):
    """Структурні типи цілей."""
    task = "task"
    project = "project"
    habit = "habit"
    target = "target"
    metric = "metric"


GOAL_TYPE_EMOJI = {
    GoalType.task: "📝",
    GoalType.project: "📋",
    GoalType.habit: "✅",
    GoalType.target: "🎯",
    GoalType.metric: "📊",
}


class GoalAction(str, Enum):
    view = "v"
    edit = "e"
    delete = "d"
    progress = "p"
    complete = "c"
    restore = "r"
    log = "l"       # Для habit
    entry = "n"     # Для target/metric


# ============== CALLBACK DATA ==============

class GoalCallback(CallbackData, prefix="g"):
    action: GoalAction
    goal_id: int


class GoalTypeCallback(CallbackData, prefix="gt"):
    goal_type: GoalType


class GoalParentCallback(CallbackData, prefix="gp"):
    parent_id: int


class FrequencyCallback(CallbackData, prefix="gf"):
    frequency: str


class GoalEditField(str, Enum):
    title = "title"
    description = "description"
    deadline = "deadline"
    target_value = "target_value"


class GoalEditCallback(CallbackData, prefix="ge"):
    field: GoalEditField
    goal_id: int


# ============== КЛАВІАТУРИ ==============

def get_goal_type_keyboard(lang: str = 'uk') -> InlineKeyboardMarkup:
    """Вибір типу цілі."""
    builder = InlineKeyboardBuilder()
    
    types = [
        (f"📝 {t('goal_type_task', lang)}", GoalType.task),
        (f"📋 {t('goal_type_project', lang)}", GoalType.project),
        (f"✅ {t('goal_type_habit', lang)}", GoalType.habit),
        (f"🎯 {t('goal_type_target', lang)}", GoalType.target),
        (f"📊 {t('goal_type_metric', lang)}", GoalType.metric),
    ]
    
    for text, gtype in types:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=GoalTypeCallback(goal_type=gtype).pack()
        ))
    
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def get_frequency_keyboard(lang: str = 'uk') -> InlineKeyboardMarkup:
    """Вибір частоти для звички."""
    builder = InlineKeyboardBuilder()
    
    options = [
        (t('freq_daily', lang), "daily"),
        (t('freq_weekdays', lang), "weekdays"),
        (t('freq_3_per_week', lang), "3_per_week"),
        (t('freq_custom', lang), "custom"),
    ]
    
    for text, freq in options:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=FrequencyCallback(frequency=freq).pack()
        ))
    
    builder.adjust(2)
    return builder.as_markup()


def get_parent_keyboard(projects: list, lang: str = 'uk') -> InlineKeyboardMarkup:
    """Вибір батьківського проєкту."""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text=t("goal_no_parent", lang),
        callback_data=GoalParentCallback(parent_id=0).pack()
    ))
    
    for proj in projects[:10]:  # Максимум 10
        builder.row(InlineKeyboardButton(
            text=f"📋 {proj['title'][:35]}",
            callback_data=GoalParentCallback(parent_id=proj['id']).pack()
        ))
    
    return builder.as_markup()


def get_deadline_keyboard(lang: str = 'uk') -> InlineKeyboardMarkup:
    """Вибір дедлайну."""
    builder = InlineKeyboardBuilder()
    
    options = [
        (t("deadline_end_week", lang), "end_week"),
        (t("deadline_end_month", lang), "end_month"),
        (t("deadline_end_quarter", lang), "end_quarter"),
        (t("deadline_end_year", lang), "end_year"),
        (t("deadline_custom", lang), "custom"),
        (t("deadline_none", lang), "none"),
    ]
    
    for text, opt in options:
        builder.add(InlineKeyboardButton(text=text, callback_data=f"goal_ddl:{opt}"))
    
    builder.adjust(2)
    return builder.as_markup()


def get_goals_list_keyboard(goals: list, lang: str = 'uk', filter_type: str = "active") -> InlineKeyboardMarkup:
    """Список цілей з фільтрами."""
    builder = InlineKeyboardBuilder()
    
    for goal in goals[:15]:  # Максимум 15
        emoji = GOAL_TYPE_EMOJI.get(GoalType(goal['goal_type']), "🎯")
        status = "✅" if goal.get('status') == 'completed' else ""
        progress = f" [{goal.get('progress', 0)}%]" if goal.get('status') != 'completed' else ""
        
        # Для звичок показуємо streak
        if goal['goal_type'] == 'habit':
            streak = goal.get('current_streak', 0)
            progress = f" 🔥{streak}" if streak > 0 else ""
        
        builder.row(InlineKeyboardButton(
            text=f"{status}{emoji} {goal['title'][:30]}{progress}",
            callback_data=GoalCallback(action=GoalAction.view, goal_id=goal['id']).pack()
        ))
    
    # Фільтри
    filters = []
    if filter_type != "active":
        filters.append(InlineKeyboardButton(text=t("filter_active", lang), callback_data="goals_f:active"))
    if filter_type != "completed":
        filters.append(InlineKeyboardButton(text=t("filter_completed", lang), callback_data="goals_f:completed"))
    if filter_type != "all":
        filters.append(InlineKeyboardButton(text=t("filter_all", lang), callback_data="goals_f:all"))
    
    if filters:
        builder.row(*filters)
    
    builder.row(InlineKeyboardButton(text=t("btn_add_goal", lang), callback_data="goal:add"))
    
    return builder.as_markup()


def get_goal_actions_keyboard(goal: dict, lang: str = 'uk') -> InlineKeyboardMarkup:
    """Дії з ціллю залежно від типу."""
    builder = InlineKeyboardBuilder()
    goal_id = goal['id']
    goal_type = goal['goal_type']
    is_completed = goal.get('status') == 'completed'
    
    if is_completed:
        builder.row(InlineKeyboardButton(
            text=t("btn_restore", lang),
            callback_data=GoalCallback(action=GoalAction.restore, goal_id=goal_id).pack()
        ))
    else:
        # Дії залежно від типу
        if goal_type == 'habit':
            builder.row(
                InlineKeyboardButton(
                    text="✅ " + t("btn_done", lang),
                    callback_data=GoalCallback(action=GoalAction.log, goal_id=goal_id).pack()
                ),
                InlineKeyboardButton(
                    text="⏭ " + t("btn_skip", lang),
                    callback_data=f"habit_skip:{goal_id}"
                )
            )
        elif goal_type in ('target', 'metric'):
            builder.row(InlineKeyboardButton(
                text="➕ " + t("btn_add_entry", lang),
                callback_data=GoalCallback(action=GoalAction.entry, goal_id=goal_id).pack()
            ))
        
        if goal_type != 'task':
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
        else:
            builder.row(InlineKeyboardButton(
                text=t("btn_complete", lang),
                callback_data=GoalCallback(action=GoalAction.complete, goal_id=goal_id).pack()
            ))
        
        builder.row(InlineKeyboardButton(
            text=t("btn_edit", lang),
            callback_data=GoalCallback(action=GoalAction.edit, goal_id=goal_id).pack()
        ))
    
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


def get_goal_edit_keyboard(goal_id: int, goal_type: str, lang: str = 'uk') -> InlineKeyboardMarkup:
    """Вибір поля для редагування."""
    builder = InlineKeyboardBuilder()
    
    fields = [
        (t("edit_field_title", lang), GoalEditField.title),
        (t("edit_field_description", lang), GoalEditField.description),
        (t("edit_field_deadline", lang), GoalEditField.deadline),
    ]
    
    if goal_type in ('target', 'metric'):
        fields.append((t("edit_field_target", lang), GoalEditField.target_value))
    
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


def get_confirm_keyboard(goal_id: int, action: str, lang: str = 'uk') -> InlineKeyboardMarkup:
    """Підтвердження дії."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t("btn_yes", lang), callback_data=f"goal_confirm:{action}:{goal_id}"),
        InlineKeyboardButton(text=t("btn_no", lang), callback_data="goals:back")
    )
    return builder.as_markup()


def get_habits_today_keyboard(habits: list, lang: str = 'uk') -> InlineKeyboardMarkup:
    """Звички на сьогодні."""
    builder = InlineKeyboardBuilder()
    
    for habit in habits:
        done = habit.get('today_status') == 'done'
        skipped = habit.get('today_status') == 'skipped'
        streak = habit.get('current_streak', 0)
        
        if done:
            status = "✅"
        elif skipped:
            status = "⏭"
        else:
            status = "⬜"
        
        streak_text = f" 🔥{streak}" if streak > 0 else ""
        
        builder.row(InlineKeyboardButton(
            text=f"{status} {habit['title'][:25]}{streak_text}",
            callback_data=GoalCallback(action=GoalAction.view, goal_id=habit['id']).pack()
        ))
    
    builder.row(
        InlineKeyboardButton(text=t("btn_add_habit", lang), callback_data="habit:add"),
        InlineKeyboardButton(text=t("btn_back", lang), callback_data="menu:main")
    )
    
    return builder.as_markup()


def get_domain_tags_keyboard(lang: str = 'uk') -> InlineKeyboardMarkup:
    """Вибір тегів доменів."""
    builder = InlineKeyboardBuilder()
    
    tags = [
        ("🏃 " + t("domain_health", lang), "health"),
        ("📚 " + t("domain_learning", lang), "learning"),
        ("💼 " + t("domain_career", lang), "career"),
        ("💰 " + t("domain_finance", lang), "finance"),
        ("👥 " + t("domain_relationships", lang), "relationships"),
        ("🌱 " + t("domain_growth", lang), "growth"),
    ]
    
    for text, tag in tags:
        builder.add(InlineKeyboardButton(text=text, callback_data=f"tag:{tag}"))
    
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text=t("btn_skip", lang), callback_data="tag:skip"))
    
    return builder.as_markup()
