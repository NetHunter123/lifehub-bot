"""
Обробники команд для роботи з задачами.
"""

from datetime import datetime, date, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.states.task_states import TaskCreation
from bot.keyboards.tasks import (
    get_priority_keyboard,
    get_deadline_keyboard,
    get_time_keyboard,
    get_duration_keyboard,
    get_task_actions_keyboard,
    get_tasks_list_keyboard,
    get_confirm_keyboard,
    TaskCallback,
    TaskAction,
    PriorityCallback,
    DeadlineCallback,
    TimeCallback,
    DurationCallback,
)
from bot.keyboards.reply import get_main_reply_keyboard, get_cancel_keyboard, get_skip_cancel_keyboard
from bot.locales import t, get_user_lang
from bot.database import queries

router = Router()


def get_priority_text(priority: int, lang: str) -> str:
    priority_keys = ["priority_urgent", "priority_high", "priority_medium", "priority_low"]
    return t(priority_keys[priority], lang)


def format_task(task: dict, lang: str) -> str:
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
        text += f"\n⏰ Час: {start.strftime('%H:%M')}"

    if task.get("estimated_duration"):
        hours = task["estimated_duration"] // 60
        mins = task["estimated_duration"] % 60
        if hours and mins:
            text += f"\n⏱ Тривалість: {hours}год {mins}хв"
        elif hours:
            text += f"\n⏱ Тривалість: {hours}год"
        else:
            text += f"\n⏱ Тривалість: {mins}хв"

    return text


def format_tasks_list(tasks: list, title: str, lang: str) -> str:
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


@router.message(Command("tasks"))
async def cmd_tasks(message: Message) -> None:
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    tasks = await queries.get_tasks_today(user_id)

    today = date.today().strftime("%d.%m.%Y")
    title = t("tasks_today_title", lang, date=today)
    text = format_tasks_list(tasks, title, lang)

    await message.answer(text, reply_markup=get_tasks_list_keyboard(tasks, lang))


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
    await message.answer(text, reply_markup=get_tasks_list_keyboard(tasks, lang))


@router.message(Command("inbox"))
async def cmd_inbox(message: Message) -> None:
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    tasks = await queries.get_tasks_inbox(user_id)
    title = t("tasks_inbox_title", lang)
    text = format_tasks_list(tasks, title, lang)
    await message.answer(text, reply_markup=get_tasks_list_keyboard(tasks, lang))


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
    await message.answer(t("task_add_priority", lang), reply_markup=get_priority_keyboard(lang))


@router.callback_query(TaskCreation.priority, PriorityCallback.filter())
async def process_priority(callback: CallbackQuery, callback_data: PriorityCallback, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    await state.update_data(priority=callback_data.priority)
    await state.set_state(TaskCreation.deadline)
    await callback.message.edit_text(t("task_add_deadline", lang), reply_markup=get_deadline_keyboard(lang))
    await callback.answer()


@router.callback_query(TaskCreation.deadline, DeadlineCallback.filter())
async def process_deadline(callback: CallbackQuery, callback_data: DeadlineCallback, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")

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


@router.callback_query(TaskCreation.time, TimeCallback.filter())
async def process_time(callback: CallbackQuery, callback_data: TimeCallback, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")

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


@router.callback_query(TaskCreation.duration, DurationCallback.filter())
async def process_duration(callback: CallbackQuery, callback_data: DurationCallback, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    user_id = callback.from_user.id

    duration = callback_data.minutes if callback_data.minutes else None

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

    priority_text = get_priority_text(data["priority"], lang)
    deadline_line = ""
    if data.get("deadline"):
        deadline_dt = datetime.fromisoformat(data["deadline"])
        deadline_line = t("task_created_deadline", lang, deadline=deadline_dt.strftime('%d.%m.%Y'))

    time_line = ""
    if data.get("scheduled_start"):
        start_dt = datetime.fromisoformat(data["scheduled_start"])
        time_line = t("task_created_time", lang, time=start_dt.strftime('%H:%M'))

    text = t("task_created", lang, title=data["title"], priority=priority_text, deadline=deadline_line, time=time_line, task_id=task_id)

    if duration:
        hours = duration // 60
        mins = duration % 60
        if hours and mins:
            text += f"\n⏱ Тривалість: {hours}год {mins}хв"
        elif hours:
            text += f"\n⏱ Тривалість: {hours}год"
        else:
            text += f"\n⏱ Тривалість: {mins}хв"

    await callback.message.edit_text(text)
    await callback.message.answer(t("what_next", lang), reply_markup=get_main_reply_keyboard(lang))
    await callback.answer()


@router.callback_query(TaskCallback.filter(F.action == TaskAction.view))
async def view_task(callback: CallbackQuery, callback_data: TaskCallback) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    task = await queries.get_task_by_id(callback_data.task_id, user_id)

    if not task:
        await callback.answer(t("task_not_found", lang), show_alert=True)
        return

    await callback.message.edit_text(format_task(task, lang), reply_markup=get_task_actions_keyboard(task["id"], lang))
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
        await callback.message.edit_text(text, reply_markup=get_tasks_list_keyboard(tasks, lang))
    else:
        await callback.answer(t("error_general", lang), show_alert=True)


@router.callback_query(TaskCallback.filter(F.action == TaskAction.delete))
async def delete_task_confirm(callback: CallbackQuery, callback_data: TaskCallback) -> None:
    lang = get_user_lang(callback.from_user.id)
    await callback.message.edit_text(t("task_delete_confirm", lang), reply_markup=get_confirm_keyboard(callback_data.task_id, "delete", lang))
    await callback.answer()


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
        await callback.message.edit_text(text, reply_markup=get_tasks_list_keyboard(tasks, lang))
    else:
        await callback.answer(t("error_general", lang), show_alert=True)


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    tasks = await queries.get_tasks_today(user_id)
    today = date.today().strftime("%d.%m.%Y")
    text = format_tasks_list(tasks, t("tasks_today_title", lang, date=today), lang)
    await callback.message.edit_text(text, reply_markup=get_tasks_list_keyboard(tasks, lang))
    await callback.answer(t("cancelled", lang))


@router.callback_query(F.data == "tasks:back")
async def back_to_tasks(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    tasks = await queries.get_tasks_today(user_id)
    today = date.today().strftime("%d.%m.%Y")
    text = format_tasks_list(tasks, t("tasks_today_title", lang, date=today), lang)
    await callback.message.edit_text(text, reply_markup=get_tasks_list_keyboard(tasks, lang))
    await callback.answer()


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


@router.message(F.text.in_(["❌ Скасувати", "❌ Cancel"]))
async def cancel_fsm(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    lang = get_user_lang(message.from_user.id)
    if current_state:
        await state.clear()
        await message.answer(t("action_cancelled", lang), reply_markup=get_main_reply_keyboard(lang))