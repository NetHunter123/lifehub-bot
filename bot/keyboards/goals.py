"""
Inline клавіатури для цілей.
LifeHub Bot v4.0
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict, Any


def get_goals_list(goals: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Список цілей згрупований по типу."""
    builder = InlineKeyboardBuilder()
    
    # Групуємо по типу
    projects = [g for g in goals if g['goal_type'] == 'project']
    targets = [g for g in goals if g['goal_type'] == 'target']
    metrics = [g for g in goals if g['goal_type'] == 'metric']
    
    # Проєкти
    if projects:
        builder.button(text="📁 ПРОЄКТИ", callback_data="goals:header:project")
        for goal in projects[:5]:
            progress = goal.get('progress', 0)
            builder.button(
                text=f"  📁 {goal['title'][:25]} [{progress}%]",
                callback_data=f"goal:view:{goal['id']}"
            )
    
    # Targets
    if targets:
        builder.button(text="🎯 ЦІЛІ", callback_data="goals:header:target")
        for goal in targets[:5]:
            current = goal.get('current_value', 0)
            target = goal.get('target_value', 1)
            unit = goal.get('unit', '')
            builder.button(
                text=f"  🎯 {goal['title'][:20]} ({current}/{target} {unit})",
                callback_data=f"goal:view:{goal['id']}"
            )
    
    # Metrics
    if metrics:
        builder.button(text="📊 МЕТРИКИ", callback_data="goals:header:metric")
        for goal in metrics[:5]:
            builder.button(
                text=f"  📊 {goal['title'][:25]}",
                callback_data=f"goal:view:{goal['id']}"
            )
    
    builder.adjust(1)
    
    # Кнопка додавання
    builder.row(InlineKeyboardButton(text="➕ Додати ціль", callback_data="goal:add"))
    
    return builder.as_markup()


def get_goal_type_keyboard() -> InlineKeyboardMarkup:
    """Вибір типу цілі."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📁 Проєкт", callback_data="goal:type:project")
    builder.button(text="🎯 Ціль (Target)", callback_data="goal:type:target")
    builder.button(text="📊 Метрика", callback_data="goal:type:metric")
    builder.button(text="❌ Скасувати", callback_data="goal:cancel")
    
    builder.adjust(1)
    return builder.as_markup()


def get_goal_actions(goal_id: int, goal_type: str) -> InlineKeyboardMarkup:
    """Дії для цілі."""
    builder = InlineKeyboardBuilder()
    
    if goal_type == 'project':
        builder.button(text="📋 Задачі", callback_data=f"goal:tasks:{goal_id}")
        builder.button(text="🎯 Дочірні цілі", callback_data=f"goal:children:{goal_id}")
    elif goal_type in ('target', 'metric'):
        builder.button(text="➕ Додати запис", callback_data=f"goal:entry:{goal_id}")
        builder.button(text="📊 Історія", callback_data=f"goal:history:{goal_id}")
    
    builder.button(text="✅ Завершити", callback_data=f"goal:complete:{goal_id}")
    builder.button(text="✏️ Редагувати", callback_data=f"goal:edit:{goal_id}")
    builder.button(text="🗑 Видалити", callback_data=f"goal:delete:{goal_id}")
    builder.button(text="◀️ Назад", callback_data="goals:list")
    
    builder.adjust(2, 2, 2)
    return builder.as_markup()


def get_parent_keyboard(projects: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Вибір батьківського проєкту."""
    builder = InlineKeyboardBuilder()
    
    for project in projects[:10]:
        builder.button(
            text=f"📁 {project['title'][:25]}",
            callback_data=f"goal:parent:{project['id']}"
        )
    
    builder.button(text="⏭ Без батьківського", callback_data="goal:parent:none")
    
    builder.adjust(1)
    return builder.as_markup()


def get_domain_tags_keyboard(selected: List[str] = None) -> InlineKeyboardMarkup:
    """Вибір тегів доменів."""
    selected = selected or []
    builder = InlineKeyboardBuilder()
    
    domains = [
        ("🏃 Health", "health"),
        ("📚 Learning", "learning"),
        ("💼 Career", "career"),
        ("💰 Finance", "finance"),
        ("👥 Relationships", "relationships"),
        ("🌱 Growth", "growth"),
    ]
    
    for name, tag in domains:
        mark = "✅" if tag in selected else "⬜"
        builder.button(text=f"{mark} {name}", callback_data=f"goal:tag:{tag}")
    
    builder.button(text="✅ Готово", callback_data="goal:tags:done")
    
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def get_deadline_keyboard() -> InlineKeyboardMarkup:
    """Вибір дедлайну для цілі."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📅 Цей місяць", callback_data="goal:deadline:month")
    builder.button(text="📅 Квартал", callback_data="goal:deadline:quarter")
    builder.button(text="📅 Рік", callback_data="goal:deadline:year")
    builder.button(text="📅 Ввести дату", callback_data="goal:deadline:custom")
    builder.button(text="⏭ Без дедлайну", callback_data="goal:deadline:none")
    
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def get_delete_confirm(goal_id: int) -> InlineKeyboardMarkup:
    """Підтвердження видалення."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✅ Так, видалити", callback_data=f"goal:delete_confirm:{goal_id}")
    builder.button(text="❌ Скасувати", callback_data=f"goal:view:{goal_id}")
    
    builder.adjust(2)
    return builder.as_markup()
