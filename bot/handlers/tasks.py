"""
Обробники задач.
LifeHub Bot v4.0
"""

from datetime import date, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.database import queries
from bot.states.states import TaskCreation
from bot.keyboards import tasks as kb
from bot.keyboards.reply import get_main_menu, get_cancel_keyboard
from bot.locales import uk


router = Router()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                              КОМАНДИ                                         ║
# ╚════════════════════════════════════════════════════════════════════════════╝

@router.message(Command("tasks"))
async def cmd_tasks(message: Message):
    """Показати задачі на сьогодні."""
    user_id = message.from_user.id
    tasks = await queries.get_tasks_today(user_id)
    
    if not tasks:
        text = f"{uk.TASKS['title_today']}\n\n{uk.TASKS['empty']}"
        await message.answer(text, parse_mode="HTML")
        return
    
    text = uk.TASKS['title_today'] + "\n\n"
    
    # Групуємо по пріоритету
    priority_groups = {0: [], 1: [], 2: [], 3: []}
    for task in tasks:
        p = task.get('priority', 2)
        priority_groups[p].append(task)
    
    priority_labels = [
        ("🔴 Терміново:", 0),
        ("🟠 Високий:", 1),
        ("🟡 Середній:", 2),
        ("🟢 Низький:", 3),
    ]
    
    for label, priority in priority_labels:
        group_tasks = priority_groups[priority]
        if group_tasks:
            text += f"\n<b>{label}</b>\n"
            for t in group_tasks:
                status = "✅" if t['is_completed'] else "•"
                deadline_str = ""
                if t.get('scheduled_time'):
                    deadline_str = f" — {t['scheduled_time']}"
                elif t.get('deadline'):
                    d = date.fromisoformat(t['deadline'])
                    if d < date.today():
                        deadline_str = " ⚠️ прострочено"
                
                goal_str = ""
                if t.get('goal_title'):
                    goal_str = f" → 📁 {t['goal_title']}"
                
                text += f"  {status} [{t['id']}] {t['title']}{deadline_str}{goal_str}\n"
    
    done = sum(1 for t in tasks if t['is_completed'])
    total = len(tasks)
    text += f"\n{uk.TASKS['completed_count'].format(done=done, total=total)}"
    
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=kb.get_tasks_list(tasks)
    )


@router.message(Command("inbox"))
async def cmd_inbox(message: Message):
    """Показати inbox (задачі без дедлайну і проєкту)."""
    user_id = message.from_user.id
    tasks = await queries.get_tasks_inbox(user_id)
    
    if not tasks:
        await message.answer(
            f"{uk.TASKS['title_inbox']}\n\n{uk.TASKS['empty_inbox']}",
            parse_mode="HTML"
        )
        return
    
    text = f"{uk.TASKS['title_inbox']} ({len(tasks)})\n\n"
    
    for task in tasks:
        text += f"• [{task['id']}] {task['title']}\n"
    
    text += "\n<i>Ці задачі потребують планування: дедлайн або прив'язка до проєкту.</i>"
    
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=kb.get_tasks_list(tasks)
    )


@router.message(Command("task_add"))
async def cmd_task_add(message: Message, state: FSMContext):
    """Почати створення задачі."""
    await state.clear()
    await state.set_state(TaskCreation.title)
    
    await message.answer(
        uk.TASKS['create_title'],
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                         ДІАЛОГ СТВОРЕННЯ                                     ║
# ╚════════════════════════════════════════════════════════════════════════════╝

@router.message(TaskCreation.title)
async def task_title(message: Message, state: FSMContext):
    """Отримуємо назву задачі."""
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer(uk.CANCELLED, reply_markup=get_main_menu())
        return
    
    await state.update_data(title=message.text)
    await state.set_state(TaskCreation.priority)
    
    await message.answer(
        uk.TASKS['create_priority'],
        reply_markup=kb.get_priority_keyboard()
    )


@router.callback_query(TaskCreation.priority, F.data.startswith("task:priority:"))
async def task_priority(callback: CallbackQuery, state: FSMContext):
    """Отримуємо пріоритет."""
    priority = int(callback.data.split(":")[-1])
    await state.update_data(priority=priority)
    await state.set_state(TaskCreation.deadline)
    
    await callback.message.edit_text(
        uk.TASKS['create_deadline'],
        reply_markup=kb.get_deadline_keyboard()
    )
    await callback.answer()


@router.callback_query(TaskCreation.deadline, F.data.startswith("task:deadline:"))
async def task_deadline(callback: CallbackQuery, state: FSMContext):
    """Отримуємо дедлайн."""
    deadline_type = callback.data.split(":")[-1]
    
    if deadline_type == "custom":
        await state.set_state(TaskCreation.deadline_custom)
        await callback.message.edit_text(uk.TASKS['create_deadline_custom'])
        await callback.answer()
        return
    
    deadline = None
    if deadline_type == "today":
        deadline = date.today().isoformat()
    elif deadline_type == "tomorrow":
        deadline = (date.today() + timedelta(days=1)).isoformat()
    elif deadline_type == "week":
        deadline = (date.today() + timedelta(days=7)).isoformat()
    
    await state.update_data(deadline=deadline)
    await state.set_state(TaskCreation.time)
    
    await callback.message.edit_text(
        uk.TASKS['create_time'],
        reply_markup=kb.get_time_keyboard()
    )
    await callback.answer()


@router.message(TaskCreation.deadline_custom)
async def task_deadline_custom(message: Message, state: FSMContext):
    """Отримуємо кастомну дату."""
    text = message.text.strip()
    
    try:
        if "." in text:
            parts = text.split(".")
            if len(parts) == 2:
                day, month = parts
                year = date.today().year
            else:
                day, month, year = parts
            
            deadline = date(int(year), int(month), int(day)).isoformat()
        else:
            await message.answer(uk.ERRORS['invalid_date'])
            return
    except ValueError:
        await message.answer(uk.ERRORS['invalid_date'])
        return
    
    await state.update_data(deadline=deadline)
    await state.set_state(TaskCreation.time)
    
    await message.answer(
        uk.TASKS['create_time'],
        reply_markup=kb.get_time_keyboard()
    )


@router.callback_query(TaskCreation.time, F.data.startswith("task:time:"))
async def task_time(callback: CallbackQuery, state: FSMContext):
    """Отримуємо час."""
    time_value = callback.data.replace("task:time:", "")
    
    if time_value == "custom":
        await state.set_state(TaskCreation.time_custom)
        await callback.message.edit_text(uk.TASKS['create_time_custom'])
        await callback.answer()
        return
    
    scheduled_time = None if time_value == "none" else time_value
    await state.update_data(scheduled_time=scheduled_time)
    
    user_id = callback.from_user.id
    projects = await queries.get_projects(user_id)
    
    if projects:
        await state.set_state(TaskCreation.goal)
        await callback.message.edit_text(
            uk.TASKS['create_goal'],
            reply_markup=kb.get_goal_keyboard(projects)
        )
    else:
        await state.set_state(TaskCreation.recurring)
        await callback.message.edit_text(
            uk.TASKS['create_recurring'],
            reply_markup=kb.get_recurring_keyboard()
        )
    
    await callback.answer()


@router.message(TaskCreation.time_custom)
async def task_time_custom(message: Message, state: FSMContext):
    """Отримуємо кастомний час."""
    text = message.text.strip()
    
    try:
        if ":" not in text:
            raise ValueError
        hours, minutes = text.split(":")
        if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
            raise ValueError
        scheduled_time = f"{int(hours):02d}:{int(minutes):02d}"
    except ValueError:
        await message.answer(uk.ERRORS['invalid_time'])
        return
    
    await state.update_data(scheduled_time=scheduled_time)
    
    user_id = message.from_user.id
    projects = await queries.get_projects(user_id)
    
    if projects:
        await state.set_state(TaskCreation.goal)
        await message.answer(
            uk.TASKS['create_goal'],
            reply_markup=kb.get_goal_keyboard(projects)
        )
    else:
        await state.set_state(TaskCreation.recurring)
        await message.answer(
            uk.TASKS['create_recurring'],
            reply_markup=kb.get_recurring_keyboard()
        )


@router.callback_query(TaskCreation.goal, F.data.startswith("task:goal:"))
async def task_goal(callback: CallbackQuery, state: FSMContext):
    """Отримуємо прив'язку до проєкту."""
    goal_value = callback.data.replace("task:goal:", "")
    
    goal_id = None if goal_value == "none" else int(goal_value)
    await state.update_data(goal_id=goal_id)
    
    await state.set_state(TaskCreation.recurring)
    await callback.message.edit_text(
        uk.TASKS['create_recurring'],
        reply_markup=kb.get_recurring_keyboard()
    )
    await callback.answer()


@router.callback_query(TaskCreation.recurring, F.data.startswith("task:recurring:"))
async def task_recurring(callback: CallbackQuery, state: FSMContext):
    """Отримуємо тип повторення."""
    recurring_type = callback.data.replace("task:recurring:", "")
    
    if recurring_type == "custom":
        await state.update_data(recurrence_rule="custom", selected_days=[])
        await state.set_state(TaskCreation.recurring_days)
        await callback.message.edit_text(
            uk.TASKS['create_recurring_days'],
            reply_markup=kb.get_weekdays_inline([])
        )
        await callback.answer()
        return
    
    recurrence_rule = None if recurring_type == "none" else recurring_type
    await state.update_data(
        is_recurring=recurrence_rule is not None,
        recurrence_rule=recurrence_rule,
        recurrence_days=None
    )
    
    await _create_task(callback, state)


@router.callback_query(TaskCreation.recurring_days, F.data.startswith("task:day:"))
async def task_select_day(callback: CallbackQuery, state: FSMContext):
    """Вибір дня тижня."""
    day = int(callback.data.replace("task:day:", ""))
    data = await state.get_data()
    selected = data.get('selected_days', [])
    
    if day in selected:
        selected.remove(day)
    else:
        selected.append(day)
    
    await state.update_data(selected_days=selected)
    await callback.message.edit_reply_markup(
        reply_markup=kb.get_weekdays_inline(selected)
    )
    await callback.answer()


@router.callback_query(TaskCreation.recurring_days, F.data == "task:days:done")
async def task_days_done(callback: CallbackQuery, state: FSMContext):
    """Завершення вибору днів."""
    data = await state.get_data()
    selected = data.get('selected_days', [])
    
    if not selected:
        await callback.answer("⚠️ Обери хоча б один день", show_alert=True)
        return
    
    recurrence_days = ",".join(str(d) for d in sorted(selected))
    await state.update_data(
        is_recurring=True,
        recurrence_rule="custom",
        recurrence_days=recurrence_days
    )
    
    await _create_task(callback, state)


async def _create_task(callback: CallbackQuery, state: FSMContext):
    """Фінальне створення задачі."""
    data = await state.get_data()
    user_id = callback.from_user.id
    
    task_id = await queries.create_task(
        user_id=user_id,
        title=data['title'],
        priority=data.get('priority', 2),
        deadline=data.get('deadline'),
        scheduled_time=data.get('scheduled_time'),
        goal_id=data.get('goal_id'),
        is_recurring=data.get('is_recurring', False),
        recurrence_rule=data.get('recurrence_rule'),
        recurrence_days=data.get('recurrence_days'),
    )
    
    await state.clear()
    
    priority_labels = ["🔴 Терміново", "🟠 Високий", "🟡 Середній", "🟢 Низький"]
    deadline_str = data.get('deadline', 'Без дедлайну') or 'Без дедлайну'
    time_str = data.get('scheduled_time', 'Без часу') or 'Без часу'
    
    goal_str = "Без проєкту"
    if data.get('goal_id'):
        goal = await queries.get_goal_by_id(data['goal_id'], user_id)
        if goal:
            goal_str = goal['title']
    
    recurring_str = "Ні"
    if data.get('is_recurring'):
        rule = data.get('recurrence_rule')
        if rule == 'daily':
            recurring_str = "Щодня"
        elif rule == 'weekdays':
            recurring_str = "По буднях"
        elif rule == 'custom':
            days = data.get('recurrence_days', '')
            day_names = {1: 'Пн', 2: 'Вт', 3: 'Ср', 4: 'Чт', 5: 'Пт', 6: 'Сб', 7: 'Нд'}
            recurring_str = ", ".join(day_names.get(int(d), d) for d in days.split(","))
    
    text = uk.TASKS['create_confirm'].format(
        title=data['title'],
        priority=priority_labels[data.get('priority', 2)],
        deadline=deadline_str,
        time=time_str,
        goal=goal_str,
        recurring=recurring_str
    )
    
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer("✅ Задачу створено!")


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                            CALLBACK ACTIONS                                  ║
# ╚════════════════════════════════════════════════════════════════════════════╝

@router.callback_query(F.data == "task:add")
async def callback_task_add(callback: CallbackQuery, state: FSMContext):
    """Додати задачу через inline."""
    await state.clear()
    await state.set_state(TaskCreation.title)
    
    await callback.message.answer(
        uk.TASKS['create_title'],
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("task:done:"))
async def callback_task_done(callback: CallbackQuery):
    """Позначити задачу виконаною."""
    task_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    success = await queries.complete_task(task_id, user_id)
    
    if success:
        task = await queries.get_task_by_id(task_id, user_id)
        await callback.answer(
            uk.TASKS['marked_done'].format(title=task['title'] if task else ''),
            show_alert=True
        )
        await cmd_tasks(callback.message)
    else:
        await callback.answer("❌ Помилка", show_alert=True)


@router.callback_query(F.data.startswith("task:undone:"))
async def callback_task_undone(callback: CallbackQuery):
    """Скасувати виконання задачі."""
    task_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    success = await queries.uncomplete_task(task_id, user_id)
    
    if success:
        await callback.answer("↩️ Задачу повернуто")
        await cmd_tasks(callback.message)
    else:
        await callback.answer("❌ Помилка", show_alert=True)


@router.callback_query(F.data.startswith("task:view:"))
async def callback_task_view(callback: CallbackQuery):
    """Переглянути деталі задачі."""
    task_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    task = await queries.get_task_by_id(task_id, user_id)
    
    if not task:
        await callback.answer(uk.TASKS['not_found'], show_alert=True)
        return
    
    priority_labels = ["🔴 Терміново", "🟠 Високий", "🟡 Середній", "🟢 Низький"]
    status = "✅ Виконано" if task['is_completed'] else "⬜ Активна"
    
    text = f"""
📋 <b>{task['title']}</b>

📊 Статус: {status}
🎯 Пріоритет: {priority_labels[task.get('priority', 2)]}
📅 Дедлайн: {task.get('deadline') or 'Без дедлайну'}
⏰ Час: {task.get('scheduled_time') or 'Без часу'}
"""
    
    if task.get('goal_title'):
        text += f"📁 Проєкт: {task['goal_title']}\n"
    
    if task.get('is_recurring'):
        text += f"🔄 Повторення: {task.get('recurrence_rule')}\n"
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=kb.get_task_actions(task_id, task['is_completed'])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("task:delete:"))
async def callback_task_delete(callback: CallbackQuery):
    """Підтвердження видалення."""
    task_id = int(callback.data.split(":")[-1])
    
    await callback.message.edit_text(
        "🗑 <b>Видалити задачу?</b>\n\nЦю дію неможливо скасувати.",
        parse_mode="HTML",
        reply_markup=kb.get_delete_confirm(task_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("task:delete_confirm:"))
async def callback_task_delete_confirm(callback: CallbackQuery):
    """Фінальне видалення."""
    task_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    success = await queries.delete_task(task_id, user_id)
    
    if success:
        await callback.message.edit_text(uk.TASKS['deleted'])
        await callback.answer("🗑 Видалено")
    else:
        await callback.answer("❌ Помилка", show_alert=True)


@router.callback_query(F.data.startswith("tasks:page:"))
async def callback_tasks_page(callback: CallbackQuery):
    """Пагінація списку задач."""
    page_str = callback.data.split(":")[-1]
    
    if page_str == "current":
        await callback.answer()
        return
    
    page = int(page_str)
    user_id = callback.from_user.id
    tasks = await queries.get_tasks_today(user_id)
    
    await callback.message.edit_reply_markup(
        reply_markup=kb.get_tasks_list(tasks, page=page)
    )
    await callback.answer()
