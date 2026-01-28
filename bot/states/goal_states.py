"""
FSM стани для роботи з цілями.
"""

from aiogram.fsm.state import State, StatesGroup


class GoalCreation(StatesGroup):
    """Стани для створення цілі."""
    title = State()           # Назва цілі
    description = State()     # Опис (опціонально)
    goal_type = State()       # Тип: yearly, quarterly, monthly, weekly
    parent = State()          # Батьківська ціль (опціонально)
    deadline = State()        # Дедлайн (опціонально)


class GoalEdit(StatesGroup):
    """Стани для редагування цілі."""
    waiting_for_value = State()  # Очікування нового значення


class GoalProgress(StatesGroup):
    """Стани для оновлення прогресу."""
    enter_progress = State()  # Введення нового прогресу (0-100)
