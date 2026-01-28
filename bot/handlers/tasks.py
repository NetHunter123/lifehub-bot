"""
Обробники команд для роботи з задачами.
"""

import re
from datetime import datetime, date, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.states.task_states import TaskCreation, TaskEdit
from bot.keyboards.tasks import (
    get_priority_keyboard,
    get_deadline_keyboard,
    get_time_keyboard,
    get_duration_keyboard,
    get_task_actions_keyboard,
    get_tasks_list_keyboard,
    get_confirm_keyboard,
    get_what_next_keyboard,
    get_edit_field_keyboard,
    TaskCallback,
    TaskAction,
    PriorityCallback,
    DeadlineCallback,
    TimeCallback,
    DurationCallback,
    EditCallback,
    EditField,
)
from bot.keyboards.reply import get_main_reply_keyboard, get_cancel_keyboard, get_skip_cancel_keyboard
from bot.locales import t, get_user_lang
from bot.database import queries

router = Router()


# ============== ДОПОМІЖНІ ФУНКЦІЇ ==============

def get_priority_text(priority: int, lang: str) -> str:
    priority_keys = ["priority_urgent", "priority_high", "priority_medium", "priority_low"]
    return t(priority_keys[priority], lang)


def parse_date(text: str) -> date | None:
    """Парсинг дати з тексту (підтримує різні формати)."""
    text = text.strip()
    
    # Формати: 28.01.2026, 28/01/2026, 28-01-2026, 2026-01-28
    patterns = [
        (r'^(\d{1,2})\.(\d{1,2})\.(\d{4})$', '%d.%m.%Y'),
        (r'^(\d{1,2})/(\d{1,2})/(\d{4})$', '%d/%m/%Y'),
        (r'^(\d{1,2})-(\d{1,2})-(\d{4})$', '%d-%m-%Y'),
        (r'^(\d{4})-(\d{1,2})-(\d{1,2})$', '%Y-%m-%d'),
        (r'^(\d{1,2})\.(\d{1,2})$', '%d.%m'),  # Без року — поточний рік
    ]
    
    for pattern, fmt in patterns:
        if re.match(pattern, text):
            try:
                if fmt == '%d.%m':
                    # Додаємо поточний рік
                    parsed = datetime.strptime(text, fmt)
                    return parsed.replace(year=date.today().year).date()
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
    
    return None


def parse_time(text: str) -> tuple[int, int] | None:
    """Парсинг часу з тексту (HH:MM або HH.MM)."""
    text = text.strip()
    
    # Формати: 12:30, 12.30, 12 30, 1230
    patterns = [
        r'^(\d{1,2}):(\d{2})$',
        r'^(\d{1,2})\.(\d{2})$',
        r'^(\d{1,2})\s(\d{2})$',
        r'^(\d{2})(\d{2})$',
    ]
    
    for pattern in patterns:
        match = re.match(pattern, text)
        if match:
            hour, minute = int(match.group(1)), int(match.group(2))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return (hour, minute)
    
    # Просто година: "14" -> 14:00
    if re.match(r'^\d{1,2}$', text):
        hour = int(text)
        if 0 <= hour <= 23:
            return (hour, 0)
    
    return None


def parse_duration(text: str) -> int | None:
    """Парсинг тривалості з тексту (хвилини або години)."""
    text = text.strip().lower()
    
    # Формати: "45", "45хв", "45m", "1.5год", "1.5h", "1год 30хв"
    
    # Просто число — хвилини
    if re.match(r'^\d+$', text):
        return int(text)
    
    # Хвилини: 45хв, 45m, 45 хв
    match = re.match(r'^(\d+)\s*(хв|m|min|мин)$', text)
    if match:
        return int(match.group(1))
    
    # Години: 2год, 2h, 1.5год
    match = re.match(r'^(\d+(?:\.\d+)?)\s*(год|h|hour|час)$', text)
    if match:
        hours = float(match.group(1))
        return int(hours * 60)
    
    # Комбінація: 1год 30хв
    match = re.match(r'^(\d+)\s*(год|h)\s*(\d+)\s*(хв|m)?$', text)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(3))
        return hours * 60 + minutes
    
    return None


def format_task(task: dict, lang: str) -> str:
    """Форматування задачі для відображення."""
    priority_emoji = ["🔴", "🟠", "🟡", "🟢"][task["priority"]]
    status_emoji = "✅" if task["is_completed"] else "⬜"
    
    text = f"{status_emoji} {priority_emoji} <b>{task['title']}</b>"
    
    if task.get("description"):
        text += f"\n{t('task_view_description', lang, description=task['description'])}"
    
    if task.get("deadline"):
        deadline = datetime.fromisoformat(task["deadline"])
        text += f"\n{t('task_view_deadline', lang, deadline=deadline.strftime('%d.%m.%Y'))}"
        if not task["is_completed"] and deadline < datetime.now():
            text += t("task_view_overdue", lang)
    
    if task.get("scheduled_start"):
        start = datetime.fromisoformat(task["scheduled_start"])
        text += f"\n⏰ {t('task_view_time', lang)}: {start.strftime('%H:%M')}"
    
    if task.get("estimated_duration"):
        hours = task["estimated_duration"] // 60
        mins = task["estimated_duration"] % 60
        if hours and mins:
            text += f"\n⏱ {t('task_view_duration', lang)}: {hours}{t('hour_short', lang)} {mins}{t('min_short', lang)}"
        elif hours:
            text += f"\n⏱ {t('task_view_duration', lang)}: {hours}{t('hour_short', lang)}"
        else:
            text += f"\n⏱ {t('task_view_duration', lang)}: {mins}{t('min_short', lang)}"
    
    return text


def format_tasks_list(tasks: list, title: str, lang: str) -> str:
    """Форматування списку задач."""
    if not tasks:
        return f"{title}\n\n{t('tasks_empty', lang)}"
    
    priority_keys = ["priority_urgent", "priority_high", "priority_medium", "priority_low"]
    grouped = {i: [] for i in range(4)}
    
    for task in tasks:
        grouped[task["priority"]].append(task)
    
    text = f"{title}\n"
    
    for priority, priority_tasks in grouped.items():
        if priority_tasks:
            text += f"\n<b>{t(priority_keys[priority], lang)}:</b>\n"
            for task in priority_tasks:
                status = "✅" if task["is_completed"] else "•"
                time_str = ""
                if task.get("scheduled_start"):
                    start = datetime.fromisoformat(task["scheduled_start"])
                    time_str = f" [{start.strftime('%H:%M')}]"
                text += f"  {status} [{task['id']}] {task['title']}{time_str}\n"
    
    completed = sum(1 for task in tasks if task["is_completed"])
    text += f"\n{t('tasks_completed', lang, done=completed, total=len(tasks))}"
    
    return text


def format_duration(minutes: int, lang: str) -> str:
    """Форматування тривалості."""
    hours = minutes // 60
    mins = minutes % 60
    if hours and mins:
        return f"{hours}{t('hour_short', lang)} {mins}{t('min_short', lang)}"
    elif hours:
        return f"{hours}{t('hour_short', lang)}"
    else:
        return f"{mins}{t('min_short', lang)}"


# ============== КОМАНДИ ==============

@router.message(Command("tasks"))
async def cmd_tasks(message: Message) -> None:
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    tasks = await queries.get_tasks_today(user_id)
    
    today = date.today().strftime("%d.%m.%Y")
    title = t("tasks_today_title", lang, date=today)
    text = format_tasks_list(tasks, title, lang)
    
    await message.answer(text, reply_markup=get_tasks_list_keyboard(tasks, lang, filter_type="today"))


@router.message(F.text.in_(["📋 Задачі", "📋 Tasks"]))
async def btn_tasks(message: Message) -> None:
    await cmd_tasks(message)


@router.message(Command("tasks_all"))
async def cmd_tasks_all(message: Message) -> None:
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    tasks = await queries.get_all_tasks(user_id)
    title = t("tasks_all_title", lang)
    text = format_tasks_list(tasks, title, lang)
    await message.answer(text, reply_markup=get_tasks_list_keyboard(tasks, lang, filter_type="all"))


@router.message(Command("inbox"))
async def cmd_inbox(message: Message) -> None:
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    tasks = await queries.get_tasks_inbox(user_id)
    title = t("tasks_inbox_title", lang)
    text = format_tasks_list(tasks, title, lang)
    await message.answer(text, reply_markup=get_tasks_list_keyboard(tasks, lang, filter_type="inbox"))


@router.message(Command("tasks_history"))
async def cmd_tasks_history(message: Message) -> None:
    """Показати історію задач (виконані + архівні, без активних)."""
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    tasks = await queries.get_tasks_history(user_id)
    title = t("tasks_history_title", lang)
    text = format_tasks_list(tasks, title, lang)
    await message.answer(text, reply_markup=get_tasks_list_keyboard(tasks, lang, filter_type="history"))


# ============== ФІЛЬТРИ ЗАДАЧ ==============

@router.callback_query(F.data == "filter:today")
async def filter_today(callback: CallbackQuery) -> None:
    """Фільтр: задачі на сьогодні."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    tasks = await queries.get_tasks_today(user_id)
    today = date.today().strftime("%d.%m.%Y")
    title = t("tasks_today_title", lang, date=today)
    text = format_tasks_list(tasks, title, lang)
    await callback.message.edit_text(text, reply_markup=get_tasks_list_keyboard(tasks, lang, filter_type="today"))
    await callback.answer()


@router.callback_query(F.data == "filter:all")
async def filter_all(callback: CallbackQuery) -> None:
    """Фільтр: всі активні задачі."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    tasks = await queries.get_all_tasks(user_id)
    title = t("tasks_all_title", lang)
    text = format_tasks_list(tasks, title, lang)
    await callback.message.edit_text(text, reply_markup=get_tasks_list_keyboard(tasks, lang, filter_type="all"))
    await callback.answer()


@router.callback_query(F.data == "filter:history")
async def filter_history(callback: CallbackQuery) -> None:
    """Фільтр: історія задач (виконані + архівні)."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    tasks = await queries.get_tasks_history(user_id)
    title = t("tasks_history_title", lang)
    text = format_tasks_list(tasks, title, lang)
    await callback.message.edit_text(text, reply_markup=get_tasks_list_keyboard(tasks, lang, filter_type="history"))
    await callback.answer()


# ============== СТВОРЕННЯ ЗАДАЧІ (FSM) ==============

@router.message(Command("task_add"))
async def start_task_creation_cmd(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    await state.set_state(TaskCreation.title)
    await state.update_data(lang=lang)
    await message.answer(t("task_add_title", lang), reply_markup=get_cancel_keyboard(lang))


@router.callback_query(F.data == "task:add")
async def start_task_creation_cb(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    await state.set_state(TaskCreation.title)
    await state.update_data(lang=lang)
    await callback.message.answer(t("task_add_title", lang), reply_markup=get_cancel_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data == "tasks:view")
async def callback_view_tasks(callback: CallbackQuery) -> None:
    """Перегляд списку задач через callback."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    tasks = await queries.get_tasks_today(user_id)
    today = date.today().strftime("%d.%m.%Y")
    title = t("tasks_today_title", lang, date=today)
    text = format_tasks_list(tasks, title, lang)
    await callback.message.answer(text, reply_markup=get_tasks_list_keyboard(tasks, lang, filter_type="today"))
    await callback.answer()


# --- Крок 1: Назва ---
@router.message(TaskCreation.title)
async def process_title(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    
    if message.text in ["❌ Скасувати", "❌ Cancel"]:
        await state.clear()
        await message.answer(t("cancelled", lang), reply_markup=get_main_reply_keyboard(lang))
        return
    
    await state.update_data(title=message.text)
    await state.set_state(TaskCreation.description)
    await message.answer(t("task_add_description", lang), reply_markup=get_skip_cancel_keyboard(lang))


# --- Крок 2: Опис ---
@router.message(TaskCreation.description)
async def process_description(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    
    if message.text in ["❌ Скасувати", "❌ Cancel"]:
        await state.clear()
        await message.answer(t("cancelled", lang), reply_markup=get_main_reply_keyboard(lang))
        return
    
    skip_texts = ["⏭ Пропустити", "⏭ Skip"]
    description = None if message.text in skip_texts else message.text
    
    await state.update_data(description=description)
    await state.set_state(TaskCreation.priority)
    
    # Прибираємо Reply клавіатуру — далі тільки inline
    await message.answer(
        t("task_add_priority", lang),
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer("⬇️", reply_markup=get_priority_keyboard(lang))


# --- Крок 3: Пріоритет ---
@router.callback_query(TaskCreation.priority, PriorityCallback.filter())
async def process_priority(callback: CallbackQuery, callback_data: PriorityCallback, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    await state.update_data(priority=callback_data.priority)
    await state.set_state(TaskCreation.deadline)
    await callback.message.edit_text(t("task_add_deadline", lang), reply_markup=get_deadline_keyboard(lang))
    await callback.answer()


# --- Крок 4: Дедлайн ---
@router.callback_query(TaskCreation.deadline, DeadlineCallback.filter())
async def process_deadline(callback: CallbackQuery, callback_data: DeadlineCallback, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    
    if callback_data.option == "custom":
        # Перехід до ручного вводу дати
        await state.set_state(TaskCreation.deadline_custom)
        await callback.message.edit_text(t("task_add_deadline_custom", lang))
        await callback.answer()
        return
    
    deadline = None
    if callback_data.option == "today":
        deadline = datetime.combine(date.today(), datetime.max.time())
    elif callback_data.option == "tomorrow":
        deadline = datetime.combine(date.today() + timedelta(days=1), datetime.max.time())
    elif callback_data.option == "week":
        deadline = datetime.combine(date.today() + timedelta(days=7), datetime.max.time())
    
    await state.update_data(deadline=deadline.isoformat() if deadline else None)
    await state.set_state(TaskCreation.time)
    await callback.message.edit_text(t("task_add_time", lang), reply_markup=get_time_keyboard(lang))
    await callback.answer()


# --- Крок 4.1: Кастомна дата ---
@router.message(TaskCreation.deadline_custom)
async def process_deadline_custom(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    
    parsed_date = parse_date(message.text)
    if not parsed_date:
        await message.answer(t("error_invalid_date", lang))
        return
    
    deadline = datetime.combine(parsed_date, datetime.max.time())
    await state.update_data(deadline=deadline.isoformat())
    await state.set_state(TaskCreation.time)
    await message.answer(t("task_add_time", lang), reply_markup=get_time_keyboard(lang))


# --- Крок 5: Час ---
@router.callback_query(TaskCreation.time, TimeCallback.filter())
async def process_time(callback: CallbackQuery, callback_data: TimeCallback, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    
    if callback_data.custom:
        # Перехід до ручного вводу часу
        await state.set_state(TaskCreation.time_custom)
        await callback.message.edit_text(t("task_add_time_custom", lang))
        await callback.answer()
        return
    
    scheduled_start = None
    if callback_data.hour is not None:
        base_date = date.today()
        if data.get("deadline"):
            base_date = datetime.fromisoformat(data["deadline"]).date()
        scheduled_start = datetime.combine(base_date, datetime.min.time().replace(hour=callback_data.hour))
    
    await state.update_data(scheduled_start=scheduled_start.isoformat() if scheduled_start else None)
    await state.set_state(TaskCreation.duration)
    await callback.message.edit_text(t("task_add_duration", lang), reply_markup=get_duration_keyboard(lang))
    await callback.answer()


# --- Крок 5.1: Кастомний час ---
@router.message(TaskCreation.time_custom)
async def process_time_custom(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    
    parsed_time = parse_time(message.text)
    if not parsed_time:
        await message.answer(t("error_invalid_time", lang))
        return
    
    hour, minute = parsed_time
    base_date = date.today()
    if data.get("deadline"):
        base_date = datetime.fromisoformat(data["deadline"]).date()
    
    scheduled_start = datetime.combine(base_date, datetime.min.time().replace(hour=hour, minute=minute))
    await state.update_data(scheduled_start=scheduled_start.isoformat())
    await state.set_state(TaskCreation.duration)
    await message.answer(t("task_add_duration", lang), reply_markup=get_duration_keyboard(lang))


# --- Крок 6: Тривалість ---
@router.callback_query(TaskCreation.duration, DurationCallback.filter())
async def process_duration(callback: CallbackQuery, callback_data: DurationCallback, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    
    if callback_data.custom:
        # Перехід до ручного вводу тривалості
        await state.set_state(TaskCreation.duration_custom)
        await callback.message.edit_text(t("task_add_duration_custom", lang))
        await callback.answer()
        return
    
    duration = callback_data.minutes
    await finish_task_creation(callback.message, state, duration, lang, is_callback=True)
    await callback.answer()


# --- Крок 6.1: Кастомна тривалість ---
@router.message(TaskCreation.duration_custom)
async def process_duration_custom(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    
    parsed_duration = parse_duration(message.text)
    if not parsed_duration:
        await message.answer(t("error_invalid_duration", lang))
        return
    
    await finish_task_creation(message, state, parsed_duration, lang, is_callback=False)


# --- Фінальне створення задачі ---
async def finish_task_creation(message: Message, state: FSMContext, duration: int | None, lang: str, is_callback: bool = False) -> None:
    """Завершення створення задачі."""
    data = await state.get_data()
    user_id = message.chat.id
    
    task_id = await queries.create_task(
        user_id=user_id,
        title=data["title"],
        description=data.get("description"),
        priority=data["priority"],
        deadline=data.get("deadline"),
        scheduled_start=data.get("scheduled_start"),
        estimated_duration=duration
    )
    
    await state.clear()
    
    # Формуємо підтвердження
    priority_text = get_priority_text(data["priority"], lang)
    
    deadline_line = ""
    if data.get("deadline"):
        deadline_dt = datetime.fromisoformat(data["deadline"])
        deadline_line = t("task_created_deadline", lang, deadline=deadline_dt.strftime('%d.%m.%Y'))
    
    time_line = ""
    if data.get("scheduled_start"):
        start_dt = datetime.fromisoformat(data["scheduled_start"])
        time_line = t("task_created_time", lang, time=start_dt.strftime('%H:%M'))
    
    duration_line = ""
    if duration:
        duration_line = t("task_created_duration", lang, duration=format_duration(duration, lang))
    
    text = t("task_created_full", lang,
             title=data["title"],
             priority=priority_text,
             deadline=deadline_line,
             time=time_line,
             duration=duration_line,
             task_id=task_id)
    
    if is_callback:
        await message.edit_text(text)
    else:
        await message.answer(text)
    
    # Кнопки "Що далі?"
    await message.answer(
        t("what_next", lang),
        reply_markup=get_what_next_keyboard(lang)
    )
    
    # Повертаємо основну Reply клавіатуру
    await message.answer("👇", reply_markup=get_main_reply_keyboard(lang))


# ============== ДІЇ З ЗАДАЧАМИ ==============

@router.callback_query(TaskCallback.filter(F.action == TaskAction.view))
async def view_task(callback: CallbackQuery, callback_data: TaskCallback) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    task = await queries.get_task_by_id(callback_data.task_id, user_id)
    
    if not task:
        await callback.answer(t("task_not_found", lang), show_alert=True)
        return
    
    await callback.message.edit_text(
        format_task(task, lang), 
        reply_markup=get_task_actions_keyboard(task["id"], lang, is_completed=bool(task["is_completed"]))
    )
    await callback.answer()


@router.callback_query(TaskCallback.filter(F.action == TaskAction.complete))
async def complete_task(callback: CallbackQuery, callback_data: TaskCallback) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    success = await queries.complete_task(callback_data.task_id, user_id)
    
    if success:
        stats = await queries.get_tasks_stats(user_id)
        await callback.answer(f"{t('task_done', lang, task_id=callback_data.task_id)}", show_alert=True)
        tasks = await queries.get_tasks_today(user_id)
        today = date.today().strftime("%d.%m.%Y")
        text = format_tasks_list(tasks, t("tasks_today_title", lang, date=today), lang)
        await callback.message.edit_text(text, reply_markup=get_tasks_list_keyboard(tasks, lang, filter_type="today"))
    else:
        await callback.answer(t("error_general", lang), show_alert=True)


@router.callback_query(TaskCallback.filter(F.action == TaskAction.undo))
async def undo_task(callback: CallbackQuery, callback_data: TaskCallback) -> None:
    """Скасувати виконання задачі (повернути в активні)."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    success = await queries.uncomplete_task(callback_data.task_id, user_id)
    
    if success:
        await callback.answer(t("task_undo_done", lang), show_alert=True)
        # Показуємо оновлену задачу
        task = await queries.get_task_by_id(callback_data.task_id, user_id)
        if task:
            await callback.message.edit_text(
                format_task(task, lang),
                reply_markup=get_task_actions_keyboard(task["id"], lang, is_completed=False)
            )
    else:
        await callback.answer(t("error_general", lang), show_alert=True)


@router.callback_query(TaskCallback.filter(F.action == TaskAction.delete))
async def delete_task_confirm(callback: CallbackQuery, callback_data: TaskCallback) -> None:
    lang = get_user_lang(callback.from_user.id)
    await callback.message.edit_text(t("task_delete_confirm", lang), reply_markup=get_confirm_keyboard(callback_data.task_id, "delete", lang))
    await callback.answer()


# ============== РЕДАГУВАННЯ ЗАДАЧІ ==============

@router.callback_query(TaskCallback.filter(F.action == TaskAction.edit))
async def edit_task_menu(callback: CallbackQuery, callback_data: TaskCallback) -> None:
    """Показати меню вибору поля для редагування."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    task = await queries.get_task_by_id(callback_data.task_id, user_id)
    
    if not task:
        await callback.answer(t("task_not_found", lang), show_alert=True)
        return
    
    await callback.message.edit_text(
        t("task_edit_choose_field", lang, title=task["title"]),
        reply_markup=get_edit_field_keyboard(callback_data.task_id, lang)
    )
    await callback.answer()


@router.callback_query(EditCallback.filter())
async def edit_field_selected(callback: CallbackQuery, callback_data: EditCallback, state: FSMContext) -> None:
    """Обробка вибору поля для редагування."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    task_id = callback_data.task_id
    field = callback_data.field
    
    # Зберігаємо контекст редагування
    await state.update_data(edit_task_id=task_id, edit_field=field.value, lang=lang)
    
    if field == EditField.priority:
        await state.set_state(TaskEdit.waiting_for_value)
        await callback.message.edit_text(
            t("task_edit_priority", lang),
            reply_markup=get_priority_keyboard(lang, task_id)
        )
    elif field == EditField.deadline:
        await state.set_state(TaskEdit.waiting_for_value)
        await callback.message.edit_text(
            t("task_edit_deadline", lang),
            reply_markup=get_deadline_keyboard(lang, task_id)
        )
    elif field == EditField.time:
        await state.set_state(TaskEdit.waiting_for_value)
        await callback.message.edit_text(
            t("task_edit_time", lang),
            reply_markup=get_time_keyboard(lang)
        )
    elif field == EditField.duration:
        await state.set_state(TaskEdit.waiting_for_value)
        await callback.message.edit_text(
            t("task_edit_duration", lang),
            reply_markup=get_duration_keyboard(lang)
        )
    else:
        # Текстовий ввід (title, description)
        await state.set_state(TaskEdit.waiting_for_value)
        prompt_key = f"task_edit_{field.value}"
        await callback.message.edit_text(t(prompt_key, lang))
    
    await callback.answer()


# --- Текстовий ввід для редагування ---
@router.message(TaskEdit.waiting_for_value)
async def process_edit_text_value(message: Message, state: FSMContext) -> None:
    """Обробка текстового вводу при редагуванні."""
    data = await state.get_data()
    lang = data.get("lang", "en")
    task_id = data.get("edit_task_id")
    field = data.get("edit_field")
    user_id = message.from_user.id
    
    if not task_id or not field:
        await state.clear()
        await message.answer(t("error_general", lang), reply_markup=get_main_reply_keyboard(lang))
        return
    
    # Обробка залежно від поля
    update_data = {}
    
    if field == EditField.title.value:
        update_data["title"] = message.text
    elif field == EditField.description.value:
        update_data["description"] = message.text
    elif field == EditField.deadline.value:
        # Кастомна дата
        parsed_date = parse_date(message.text)
        if not parsed_date:
            await message.answer(t("error_invalid_date", lang))
            return
        deadline = datetime.combine(parsed_date, datetime.max.time())
        update_data["deadline"] = deadline.isoformat()
    elif field == EditField.time.value:
        # Кастомний час
        parsed_time = parse_time(message.text)
        if not parsed_time:
            await message.answer(t("error_invalid_time", lang))
            return
        hour, minute = parsed_time
        task = await queries.get_task_by_id(task_id, user_id)
        base_date = date.today()
        if task and task.get("deadline"):
            base_date = datetime.fromisoformat(task["deadline"]).date()
        scheduled_start = datetime.combine(base_date, datetime.min.time().replace(hour=hour, minute=minute))
        update_data["scheduled_start"] = scheduled_start.isoformat()
    elif field == EditField.duration.value:
        # Кастомна тривалість
        parsed_duration = parse_duration(message.text)
        if not parsed_duration:
            await message.answer(t("error_invalid_duration", lang))
            return
        update_data["estimated_duration"] = parsed_duration
    
    # Оновлюємо задачу
    success = await queries.update_task(task_id, user_id, **update_data)
    await state.clear()
    
    if success:
        await message.answer(t("task_updated", lang), reply_markup=get_main_reply_keyboard(lang))
        # Показуємо оновлену задачу
        task = await queries.get_task_by_id(task_id, user_id)
        if task:
            await message.answer(
                format_task(task, lang),
                reply_markup=get_task_actions_keyboard(task_id, lang)
            )
    else:
        await message.answer(t("error_general", lang), reply_markup=get_main_reply_keyboard(lang))


# --- Inline вибір при редагуванні (пріоритет) ---
@router.callback_query(TaskEdit.waiting_for_value, PriorityCallback.filter())
async def process_edit_priority(callback: CallbackQuery, callback_data: PriorityCallback, state: FSMContext) -> None:
    """Редагування пріоритету."""
    data = await state.get_data()
    lang = data.get("lang", "en")
    task_id = data.get("edit_task_id")
    user_id = callback.from_user.id
    
    success = await queries.update_task(task_id, user_id, priority=callback_data.priority)
    await state.clear()
    
    if success:
        await callback.answer(t("task_updated", lang))
        task = await queries.get_task_by_id(task_id, user_id)
        if task:
            await callback.message.edit_text(
                format_task(task, lang),
                reply_markup=get_task_actions_keyboard(task_id, lang)
            )
    else:
        await callback.answer(t("error_general", lang), show_alert=True)


# --- Inline вибір при редагуванні (дедлайн) ---
@router.callback_query(TaskEdit.waiting_for_value, DeadlineCallback.filter())
async def process_edit_deadline(callback: CallbackQuery, callback_data: DeadlineCallback, state: FSMContext) -> None:
    """Редагування дедлайну."""
    data = await state.get_data()
    lang = data.get("lang", "en")
    task_id = data.get("edit_task_id")
    user_id = callback.from_user.id
    
    if callback_data.option == "custom":
        # Перехід до текстового вводу
        await state.update_data(edit_field="deadline")
        await callback.message.edit_text(t("task_add_deadline_custom", lang))
        await callback.answer()
        return
    
    deadline = None
    if callback_data.option == "today":
        deadline = datetime.combine(date.today(), datetime.max.time())
    elif callback_data.option == "tomorrow":
        deadline = datetime.combine(date.today() + timedelta(days=1), datetime.max.time())
    elif callback_data.option == "week":
        deadline = datetime.combine(date.today() + timedelta(days=7), datetime.max.time())
    
    success = await queries.update_task(task_id, user_id, deadline=deadline.isoformat() if deadline else None)
    await state.clear()
    
    if success:
        await callback.answer(t("task_updated", lang))
        task = await queries.get_task_by_id(task_id, user_id)
        if task:
            await callback.message.edit_text(
                format_task(task, lang),
                reply_markup=get_task_actions_keyboard(task_id, lang)
            )
    else:
        await callback.answer(t("error_general", lang), show_alert=True)


# --- Inline вибір при редагуванні (час) ---
@router.callback_query(TaskEdit.waiting_for_value, TimeCallback.filter())
async def process_edit_time(callback: CallbackQuery, callback_data: TimeCallback, state: FSMContext) -> None:
    """Редагування часу."""
    data = await state.get_data()
    lang = data.get("lang", "en")
    task_id = data.get("edit_task_id")
    user_id = callback.from_user.id
    
    if callback_data.custom:
        await state.update_data(edit_field="time")
        await callback.message.edit_text(t("task_add_time_custom", lang))
        await callback.answer()
        return
    
    scheduled_start = None
    if callback_data.hour is not None:
        task = await queries.get_task_by_id(task_id, user_id)
        base_date = date.today()
        if task and task.get("deadline"):
            base_date = datetime.fromisoformat(task["deadline"]).date()
        scheduled_start = datetime.combine(base_date, datetime.min.time().replace(hour=callback_data.hour))
    
    success = await queries.update_task(task_id, user_id, scheduled_start=scheduled_start.isoformat() if scheduled_start else None)
    await state.clear()
    
    if success:
        await callback.answer(t("task_updated", lang))
        task = await queries.get_task_by_id(task_id, user_id)
        if task:
            await callback.message.edit_text(
                format_task(task, lang),
                reply_markup=get_task_actions_keyboard(task_id, lang)
            )
    else:
        await callback.answer(t("error_general", lang), show_alert=True)


# --- Inline вибір при редагуванні (тривалість) ---
@router.callback_query(TaskEdit.waiting_for_value, DurationCallback.filter())
async def process_edit_duration(callback: CallbackQuery, callback_data: DurationCallback, state: FSMContext) -> None:
    """Редагування тривалості."""
    data = await state.get_data()
    lang = data.get("lang", "en")
    task_id = data.get("edit_task_id")
    user_id = callback.from_user.id
    
    if callback_data.custom:
        await state.update_data(edit_field="duration")
        await callback.message.edit_text(t("task_add_duration_custom", lang))
        await callback.answer()
        return
    
    success = await queries.update_task(task_id, user_id, estimated_duration=callback_data.minutes)
    await state.clear()
    
    if success:
        await callback.answer(t("task_updated", lang))
        task = await queries.get_task_by_id(task_id, user_id)
        if task:
            await callback.message.edit_text(
                format_task(task, lang),
                reply_markup=get_task_actions_keyboard(task_id, lang)
            )
    else:
        await callback.answer(t("error_general", lang), show_alert=True)


@router.callback_query(F.data.startswith("confirm:delete:"))
async def delete_task_execute(callback: CallbackQuery) -> None:
    task_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    
    success = await queries.delete_task(task_id, user_id)
    if success:
        await callback.answer(t("task_deleted", lang, task_id=task_id), show_alert=True)
        tasks = await queries.get_tasks_today(user_id)
        today = date.today().strftime("%d.%m.%Y")
        text = format_tasks_list(tasks, t("tasks_today_title", lang, date=today), lang)
        await callback.message.edit_text(text, reply_markup=get_tasks_list_keyboard(tasks, lang, filter_type="today"))
    else:
        await callback.answer(t("error_general", lang), show_alert=True)


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    tasks = await queries.get_tasks_today(user_id)
    today = date.today().strftime("%d.%m.%Y")
    text = format_tasks_list(tasks, t("tasks_today_title", lang, date=today), lang)
    await callback.message.edit_text(text, reply_markup=get_tasks_list_keyboard(tasks, lang, filter_type="today"))
    await callback.answer(t("cancelled", lang))


@router.callback_query(F.data == "tasks:back")
async def back_to_tasks(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    tasks = await queries.get_tasks_today(user_id)
    today = date.today().strftime("%d.%m.%Y")
    text = format_tasks_list(tasks, t("tasks_today_title", lang, date=today), lang)
    await callback.message.edit_text(text, reply_markup=get_tasks_list_keyboard(tasks, lang, filter_type="today"))
    await callback.answer()


# ============== ШВИДКІ КОМАНДИ ==============

@router.message(Command("task_done"))
async def cmd_task_done(message: Message) -> None:
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    args = message.text.split()
    
    if len(args) < 2:
        await message.answer(t("task_done_usage", lang))
        return
    
    try:
        task_id = int(args[1])
    except ValueError:
        await message.answer(t("task_id_invalid", lang))
        return
    
    success = await queries.complete_task(task_id, user_id)
    if success:
        stats = await queries.get_tasks_stats(user_id)
        await message.answer(f"{t('task_done', lang, task_id=task_id)}\n{t('task_done_stats', lang, count=stats['completed_today'])}")
    else:
        await message.answer(t("task_not_found", lang))


@router.message(Command("task_delete"))
async def cmd_task_delete(message: Message) -> None:
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    args = message.text.split()
    
    if len(args) < 2:
        await message.answer(t("task_delete_usage", lang))
        return
    
    try:
        task_id = int(args[1])
    except ValueError:
        await message.answer(t("task_id_invalid", lang))
        return
    
    success = await queries.delete_task(task_id, user_id)
    if success:
        await message.answer(t("task_deleted", lang, task_id=task_id))
    else:
        await message.answer(t("task_not_found", lang))


# ============== СКАСУВАННЯ FSM ==============

@router.message(F.text.in_(["❌ Скасувати", "❌ Cancel"]))
async def cancel_fsm(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    lang = get_user_lang(message.from_user.id)
    if current_state:
        await state.clear()
        await message.answer(t("action_cancelled", lang), reply_markup=get_main_reply_keyboard(lang))
