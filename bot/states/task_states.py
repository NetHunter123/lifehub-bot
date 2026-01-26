"""
FSM стани для роботи з задачами.
"""

from aiogram.fsm.state import State, StatesGroup


class TaskCreation(StatesGroup):
    """Стани для створення нової задачі."""

    title = State()              # Крок 1: Назва
    description = State()        # Крок 2: Опис (можна пропустити)
    priority = State()           # Крок 3: Пріоритет (inline)
    deadline = State()           # Крок 4: Дедлайн (inline)
    deadline_custom = State()    # Крок 4.1: Кастомна дата (текст)
    time = State()               # Крок 5: Час початку (inline)
    time_custom = State()        # Крок 5.1: Кастомний час (текст)
    duration = State()           # Крок 6: Тривалість (inline)
    duration_custom = State()    # Крок 6.1: Кастомна тривалість (текст)
    goal = State()               # Крок 7: Прив'язка до цілі (майбутнє)


class TaskEdit(StatesGroup):
    """Стани для редагування задачі."""

    waiting_for_field = State()
    waiting_for_value = State()
