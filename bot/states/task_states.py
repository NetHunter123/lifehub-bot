"""
FSM стани для роботи з задачами.
Використовуються для багатокрокових діалогів.
"""

from aiogram.fsm.state import State, StatesGroup


class TaskCreation(StatesGroup):
    """Стани для створення нової задачі."""
    
    # Крок 1: Введення назви
    title = State()
    
    # Крок 2: Опис (опціонально)
    description = State()
    
    # Крок 3: Пріоритет
    priority = State()
    
    # Крок 4: Дедлайн
    deadline = State()
    
    # Крок 5: Прив'язка до цілі (опціонально)
    goal = State()


class TaskEdit(StatesGroup):
    """Стани для редагування задачі."""
    
    waiting_for_field = State()  # Вибір поля для редагування
    waiting_for_value = State()  # Введення нового значення
