"""
FSM States — всі стани діалогів в одному місці.
LifeHub Bot v4.0

ВАЖЛИВО: Всі стани тут, не створювати окремих файлів!
"""

from aiogram.fsm.state import State, StatesGroup


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                              TASKS                                           ║
# ╚════════════════════════════════════════════════════════════════════════════╝

class TaskCreation(StatesGroup):
    """Створення задачі."""
    title = State()           # Введення назви
    priority = State()        # Вибір пріоритету
    deadline = State()        # Вибір дедлайну
    deadline_custom = State() # Введення кастомної дати
    time = State()            # Вибір часу (опціонально)
    time_custom = State()     # Введення кастомного часу
    goal = State()            # Прив'язка до проєкту
    recurring = State()       # Чи повторювана?
    recurring_days = State()  # Вибір днів (для custom)
    confirm = State()         # Підтвердження


class TaskEdit(StatesGroup):
    """Редагування задачі."""
    select_field = State()    # Вибір поля для редагування
    new_value = State()       # Введення нового значення


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                              GOALS                                           ║
# ╚════════════════════════════════════════════════════════════════════════════╝

class GoalCreation(StatesGroup):
    """Створення цілі (project/target/metric)."""
    title = State()           # Назва
    goal_type = State()       # Тип: project, target, metric
    description = State()     # Опис (опціонально)
    parent = State()          # Батьківський проєкт
    deadline = State()        # Дедлайн
    deadline_custom = State()
    # Для Target
    target_value = State()    # Цільове значення
    unit = State()            # Одиниця виміру
    # Для Metric
    target_range = State()    # Діапазон (min-max)
    # Загальне
    domain_tags = State()     # Теги доменів
    confirm = State()


class GoalEdit(StatesGroup):
    """Редагування цілі."""
    select_field = State()
    new_value = State()


class GoalEntry(StatesGroup):
    """Додавання запису для Target/Metric."""
    value = State()           # Значення
    notes = State()           # Нотатки (опціонально)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                              HABITS                                          ║
# ╚════════════════════════════════════════════════════════════════════════════╝

class HabitCreation(StatesGroup):
    """Створення звички."""
    title = State()           # Назва
    frequency = State()       # Частота: daily, weekdays, custom
    schedule_days = State()   # Конкретні дні (для custom)
    reminder_time = State()   # Час нагадування
    time_custom = State()     # Кастомний час
    duration = State()        # Тривалість (хвилини)
    parent = State()          # Батьківський проєкт
    confirm = State()


class HabitEdit(StatesGroup):
    """Редагування звички."""
    select_field = State()
    new_value = State()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                          RECURRING TASKS                                     ║
# ╚════════════════════════════════════════════════════════════════════════════╝

class RecurringTaskCreation(StatesGroup):
    """Створення повторюваної задачі (без streak)."""
    title = State()
    recurrence = State()      # daily, weekdays, custom
    recurrence_days = State() # Дні для custom
    time_start = State()      # Час початку
    time_end = State()        # Час завершення
    is_fixed = State()        # Фіксований час?
    goal = State()            # Прив'язка до проєкту
    confirm = State()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                              BOOKS                                           ║
# ╚════════════════════════════════════════════════════════════════════════════╝

class BookCreation(StatesGroup):
    """Додавання книги."""
    input_type = State()      # Файл або вручну
    file = State()            # Завантаження файлу
    title = State()           # Назва
    author = State()          # Автор
    pages = State()           # Кількість сторінок
    tags = State()            # Теги
    confirm = State()


class BookEdit(StatesGroup):
    """Редагування книги."""
    select_field = State()
    new_value = State()


class BookProgress(StatesGroup):
    """Оновлення прогресу читання."""
    current_page = State()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                              WORDS                                           ║
# ╚════════════════════════════════════════════════════════════════════════════╝

class WordCreation(StatesGroup):
    """Додавання слова."""
    word = State()            # Слово
    translation = State()     # Переклад
    example = State()         # Приклад використання
    tags = State()            # Теги
    confirm = State()


class LearningSession(StatesGroup):
    """Сесія вивчення слів (SM-2)."""
    show_word = State()       # Показ слова
    answer = State()          # Відповідь користувача
    rate = State()            # Оцінка (0-5)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                             SETTINGS                                         ║
# ╚════════════════════════════════════════════════════════════════════════════╝

class Settings(StatesGroup):
    """Налаштування."""
    select_option = State()
    morning_time = State()
    evening_time = State()
    timezone = State()
