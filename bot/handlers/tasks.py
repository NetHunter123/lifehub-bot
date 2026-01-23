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
    get_task_actions_keyboard,
    get_tasks_list_keyboard,
    get_confirm_keyboard,
    TaskCallback,
    TaskAction,
    PriorityCallback,
    DeadlineCallback,
)
from bot.keyboards.reply import get_main_reply_keyboard, get_cancel_keyboard, get_skip_cancel_keyboard
from bot.database import queries

router = Router()


# ============== ДОПОМІЖНІ ФУНКЦІЇ ==============

def format_task(task: dict) -> str:
    """Форматування задачі для відображення."""
    priority_emoji = ["🔴", "🟠", "🟡", "🟢"][task["priority"]]
    status_emoji = "✅" if task["is_completed"] else "⬜"
    
    text = f"{status_emoji} {priority_emoji} <b>{task['title']}</b>"
    
    if task.get("description"):
        text += f"\n📝 {task['description']}"
    
    if task.get("deadline"):
        deadline = datetime.fromisoformat(task["deadline"])
        text += f"\n📅 Дедлайн: {deadline.strftime('%d.%m.%Y %H:%M')}"
        
        # Перевірка на прострочення
        if not task["is_completed"] and deadline < datetime.now():
            text += " ⚠️ <i>прострочено!</i>"
    
    return text


def format_tasks_list(tasks: list, title: str) -> str:
    """Форматування списку задач."""
    if not tasks:
        return f"{title}\n\n📭 Задач немає"
    
    # Групуємо за пріоритетом
    priority_names = ["🔴 Терміново", "🟠 Високий", "🟡 Середній", "🟢 Низький"]
    grouped = {i: [] for i in range(4)}
    
    for task in tasks:
        grouped[task["priority"]].append(task)
    
    text = f"{title}\n"
    
    for priority, priority_tasks in grouped.items():
        if priority_tasks:
            text += f"\n<b>{priority_names[priority]}:</b>\n"
            for task in priority_tasks:
                status = "✅" if task["is_completed"] else "•"
                text += f"  {status} [{task['id']}] {task['title']}\n"
    
    # Статистика
    completed = sum(1 for t in tasks if t["is_completed"])
    text += f"\n✅ Виконано: {completed}/{len(tasks)}"
    
    return text


# ============== КОМАНДИ ==============

@router.message(Command("tasks"))
@router.message(F.text == "📋 Задачі")
async def cmd_tasks(message: Message) -> None:
    """Показати задачі на сьогодні."""
    user_id = message.from_user.id
    tasks = await queries.get_tasks_today(user_id)
    
    today = date.today().strftime("%d.%m.%Y")
    text = format_tasks_list(tasks, f"📋 <b>Задачі на сьогодні</b> ({today})")
    
    await message.answer(
        text,
        reply_markup=get_tasks_list_keyboard(tasks) if tasks else None
    )


@router.message(Command("tasks_all"))
async def cmd_tasks_all(message: Message) -> None:
    """Показати всі задачі."""
    user_id = message.from_user.id
    tasks = await queries.get_all_tasks(user_id)
    
    text = format_tasks_list(tasks, "📋 <b>Всі задачі</b>")
    
    await message.answer(
        text,
        reply_markup=get_tasks_list_keyboard(tasks) if tasks else None
    )


@router.message(Command("inbox"))
async def cmd_inbox(message: Message) -> None:
    """Показати inbox (необроблені задачі)."""
    user_id = message.from_user.id
    tasks = await queries.get_tasks_inbox(user_id)
    
    text = format_tasks_list(tasks, "📥 <b>Inbox</b> (необроблені)")
    
    await message.answer(
        text,
        reply_markup=get_tasks_list_keyboard(tasks) if tasks else None
    )


# ============== СТВОРЕННЯ ЗАДАЧІ (FSM) ==============

@router.message(Command("task_add"))
@router.callback_query(F.data == "task:add")
async def start_task_creation(message: Message | CallbackQuery, state: FSMContext) -> None:
    """Початок створення задачі."""
    await state.set_state(TaskCreation.title)
    
    text = "📝 <b>Нова задача</b>\n\nВведи назву задачі:"
    
    if isinstance(message, CallbackQuery):
        await message.message.answer(text, reply_markup=get_cancel_keyboard())
        await message.answer()
    else:
        await message.answer(text, reply_markup=get_cancel_keyboard())


@router.message(TaskCreation.title)
async def process_title(message: Message, state: FSMContext) -> None:
    """Обробка назви задачі."""
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer(
            "❌ Створення скасовано.",
            reply_markup=get_main_reply_keyboard()
        )
        return
    
    await state.update_data(title=message.text)
    await state.set_state(TaskCreation.description)
    
    await message.answer(
        "📝 Додай опис (або пропусти):",
        reply_markup=get_skip_cancel_keyboard()
    )


@router.message(TaskCreation.description)
async def process_description(message: Message, state: FSMContext) -> None:
    """Обробка опису задачі."""
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer(
            "❌ Створення скасовано.",
            reply_markup=get_main_reply_keyboard()
        )
        return
    
    description = None if message.text == "⏭ Пропустити" else message.text
    await state.update_data(description=description)
    await state.set_state(TaskCreation.priority)
    
    await message.answer(
        "🎯 Обери пріоритет:",
        reply_markup=get_priority_keyboard()
    )


@router.callback_query(TaskCreation.priority, PriorityCallback.filter())
async def process_priority(callback: CallbackQuery, callback_data: PriorityCallback, state: FSMContext) -> None:
    """Обробка вибору пріоритету."""
    await state.update_data(priority=callback_data.priority)
    await state.set_state(TaskCreation.deadline)
    
    await callback.message.edit_text(
        "📅 Обери дедлайн:",
        reply_markup=get_deadline_keyboard()
    )
    await callback.answer()


@router.callback_query(TaskCreation.deadline, DeadlineCallback.filter())
async def process_deadline(callback: CallbackQuery, callback_data: DeadlineCallback, state: FSMContext) -> None:
    """Обробка вибору дедлайну."""
    deadline = None
    
    if callback_data.option == "today":
        deadline = datetime.combine(date.today(), datetime.max.time())
    elif callback_data.option == "tomorrow":
        deadline = datetime.combine(date.today() + timedelta(days=1), datetime.max.time())
    elif callback_data.option == "week":
        deadline = datetime.combine(date.today() + timedelta(days=7), datetime.max.time())
    elif callback_data.option == "pick":
        # TODO: Календар для вибору дати
        deadline = datetime.combine(date.today() + timedelta(days=3), datetime.max.time())
    # none = без дедлайну
    
    await state.update_data(deadline=deadline)
    
    # Створюємо задачу
    data = await state.get_data()
    user_id = callback.from_user.id
    
    task_id = await queries.create_task(
        user_id=user_id,
        title=data["title"],
        description=data.get("description"),
        priority=data["priority"],
        deadline=deadline.isoformat() if deadline else None
    )
    
    await state.clear()
    
    # Форматуємо підтвердження
    priority_names = ["🔴 Терміново", "🟠 Високий", "🟡 Середній", "🟢 Низький"]
    
    text = f"✅ <b>Задачу створено!</b>\n\n"
    text += f"📝 {data['title']}\n"
    text += f"🎯 Пріоритет: {priority_names[data['priority']]}\n"
    if deadline:
        text += f"📅 Дедлайн: {deadline.strftime('%d.%m.%Y')}\n"
    text += f"\n🆔 ID: {task_id}"
    
    await callback.message.edit_text(text)
    await callback.message.answer(
        "Що далі?",
        reply_markup=get_main_reply_keyboard()
    )
    await callback.answer("Задачу створено! ✅")


# ============== ДІЇ З ЗАДАЧАМИ ==============

@router.callback_query(TaskCallback.filter(F.action == TaskAction.view))
async def view_task(callback: CallbackQuery, callback_data: TaskCallback) -> None:
    """Перегляд задачі."""
    user_id = callback.from_user.id
    task = await queries.get_task_by_id(callback_data.task_id, user_id)
    
    if not task:
        await callback.answer("❌ Задачу не знайдено", show_alert=True)
        return
    
    text = format_task(task)
    
    await callback.message.edit_text(
        text,
        reply_markup=get_task_actions_keyboard(task["id"])
    )
    await callback.answer()


@router.callback_query(TaskCallback.filter(F.action == TaskAction.complete))
async def complete_task(callback: CallbackQuery, callback_data: TaskCallback) -> None:
    """Виконання задачі."""
    user_id = callback.from_user.id
    success = await queries.complete_task(callback_data.task_id, user_id)
    
    if success:
        # Отримуємо статистику
        stats = await queries.get_tasks_stats(user_id)
        await callback.answer(
            f"✅ Задачу виконано!\nСьогодні: {stats['completed_today']} задач",
            show_alert=True
        )
        # Оновлюємо список
        tasks = await queries.get_tasks_today(user_id)
        today = date.today().strftime("%d.%m.%Y")
        text = format_tasks_list(tasks, f"📋 <b>Задачі на сьогодні</b> ({today})")
        await callback.message.edit_text(
            text,
            reply_markup=get_tasks_list_keyboard(tasks) if tasks else None
        )
    else:
        await callback.answer("❌ Помилка", show_alert=True)


@router.callback_query(TaskCallback.filter(F.action == TaskAction.delete))
async def delete_task_confirm(callback: CallbackQuery, callback_data: TaskCallback) -> None:
    """Підтвердження видалення."""
    await callback.message.edit_text(
        "🗑 <b>Видалити задачу?</b>\n\nЦю дію неможливо скасувати.",
        reply_markup=get_confirm_keyboard(callback_data.task_id, "delete")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm:delete:"))
async def delete_task_execute(callback: CallbackQuery) -> None:
    """Виконання видалення."""
    task_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id
    
    success = await queries.delete_task(task_id, user_id)
    
    if success:
        await callback.answer("🗑 Задачу видалено", show_alert=True)
        # Повертаємось до списку
        tasks = await queries.get_tasks_today(user_id)
        today = date.today().strftime("%d.%m.%Y")
        text = format_tasks_list(tasks, f"📋 <b>Задачі на сьогодні</b> ({today})")
        await callback.message.edit_text(
            text,
            reply_markup=get_tasks_list_keyboard(tasks) if tasks else None
        )
    else:
        await callback.answer("❌ Помилка видалення", show_alert=True)


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery) -> None:
    """Скасування дії."""
    user_id = callback.from_user.id
    tasks = await queries.get_tasks_today(user_id)
    today = date.today().strftime("%d.%m.%Y")
    text = format_tasks_list(tasks, f"📋 <b>Задачі на сьогодні</b> ({today})")
    
    await callback.message.edit_text(
        text,
        reply_markup=get_tasks_list_keyboard(tasks) if tasks else None
    )
    await callback.answer("Скасовано")


# ============== ШВИДКЕ ДОДАВАННЯ ==============

@router.message(Command("task_done"))
async def cmd_task_done(message: Message) -> None:
    """Швидке виконання задачі: /task_done 5"""
    args = message.text.split()
    
    if len(args) < 2:
        await message.answer("❓ Вкажи ID задачі: /task_done 5")
        return
    
    try:
        task_id = int(args[1])
    except ValueError:
        await message.answer("❌ ID має бути числом")
        return
    
    user_id = message.from_user.id
    success = await queries.complete_task(task_id, user_id)
    
    if success:
        stats = await queries.get_tasks_stats(user_id)
        await message.answer(
            f"✅ Задачу #{task_id} виконано!\n"
            f"📊 Сьогодні виконано: {stats['completed_today']}"
        )
    else:
        await message.answer("❌ Задачу не знайдено")


@router.message(Command("task_delete"))
async def cmd_task_delete(message: Message) -> None:
    """Швидке видалення задачі: /task_delete 5"""
    args = message.text.split()
    
    if len(args) < 2:
        await message.answer("❓ Вкажи ID задачі: /task_delete 5")
        return
    
    try:
        task_id = int(args[1])
    except ValueError:
        await message.answer("❌ ID має бути числом")
        return
    
    user_id = message.from_user.id
    success = await queries.delete_task(task_id, user_id)
    
    if success:
        await message.answer(f"🗑 Задачу #{task_id} видалено")
    else:
        await message.answer("❌ Задачу не знайдено")


# ============== СКАСУВАННЯ FSM ==============

@router.message(F.text == "❌ Скасувати")
async def cancel_fsm(message: Message, state: FSMContext) -> None:
    """Глобальний обробник скасування."""
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer(
            "❌ Дію скасовано.",
            reply_markup=get_main_reply_keyboard()
        )
