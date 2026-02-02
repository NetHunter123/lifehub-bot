"""
Dashboard /today — розклад на сьогодні.
LifeHub Bot v4.0

Два режими:
- За часом (хронологічний)
- За типом (групування)
"""

from datetime import date
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from bot.database import queries
from bot.keyboards.today import get_today_keyboard, get_recurring_task_actions
from bot.locales import uk


router = Router()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                              КОМАНДИ                                         ║
# ╚════════════════════════════════════════════════════════════════════════════╝

@router.message(Command("today"))
async def cmd_today(message: Message, sort_mode: str = 'time'):
    """Dashboard на сьогодні."""
    user_id = message.from_user.id
    schedule = await queries.get_today_schedule(user_id)
    
    text = await _format_today(schedule, sort_mode)
    
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_today_keyboard(sort_mode)
    )


async def _format_today(schedule: dict, sort_mode: str) -> str:
    """Форматування розкладу."""
    today = date.today()
    weekday_name = uk.TODAY['weekdays'][today.weekday()]
    date_str = today.strftime("%d.%m")
    
    header = f"📅 <b>СЬОГОДНІ</b> — {weekday_name}, {date_str}\n\n"
    
    if not schedule['timeline']:
        return header + uk.TODAY['empty']
    
    if sort_mode == 'time':
        body = _format_by_time(schedule)
    else:
        body = _format_by_type(schedule)
    
    # Прогрес
    done, total = _calculate_progress(schedule)
    percent = int(done / total * 100) if total > 0 else 0
    
    footer = f"\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
    footer += f"📊 Прогрес: {done}/{total} ({percent}%)"
    
    return header + body + footer


def _format_by_time(schedule: dict) -> str:
    """Форматування хронологічно."""
    lines = []
    
    # Елементи з часом
    with_time = [i for i in schedule['timeline'] if i.get('time')]
    without_time = [i for i in schedule['timeline'] if not i.get('time')]
    
    for item in with_time:
        lines.append(_format_item(item))
    
    # Елементи без часу
    if without_time:
        lines.append("── без часу ──")
        for item in without_time:
            lines.append(_format_item(item, show_time=False))
    
    return "\n".join(lines)


def _format_by_type(schedule: dict) -> str:
    """Форматування за типом."""
    lines = []
    
    # 1. Фіксований час
    fixed = [i for i in schedule['timeline'] 
             if i['type'] == 'recurring_task' and i.get('is_fixed')]
    if fixed:
        lines.append("🏫 <b>ФІКСОВАНИЙ ЧАС:</b>")
        for item in fixed:
            lines.append("  " + _format_item(item))
        lines.append("")
    
    # 2. Звички без проєкту
    habits = [i for i in schedule['timeline'] 
              if i['type'] == 'habit' and not _get_parent_project(i)]
    if habits:
        lines.append("✅ <b>ЗВИЧКИ:</b>")
        for item in sorted(habits, key=lambda x: x.get('time') or '99:99'):
            lines.append("  " + _format_item(item))
        lines.append("")
    
    # 3. Задачі без проєкту
    tasks = [i for i in schedule['timeline'] 
             if i['type'] in ('task', 'recurring_task') 
             and not i.get('is_fixed')
             and not _get_goal_id(i)]
    if tasks:
        lines.append("📋 <b>ЗАДАЧІ:</b>")
        for item in sorted(tasks, key=lambda x: (x.get('priority', 2), x.get('time') or '99:99')):
            lines.append("  " + _format_item(item))
        lines.append("")
    
    # 4. Проєкти з їх items
    project_items = {}
    for item in schedule['timeline']:
        project_id = _get_goal_id(item) or _get_parent_project(item)
        if project_id:
            if project_id not in project_items:
                project_items[project_id] = {
                    'title': item.get('goal_title') or '...',
                    'items': []
                }
            project_items[project_id]['items'].append(item)
    
    for project_id, data in project_items.items():
        lines.append(f"📁 <b>ПРОЄКТ «{data['title']}»:</b>")
        for item in sorted(data['items'], key=lambda x: x.get('time') or '99:99'):
            lines.append("  " + _format_item(item))
        lines.append("")
    
    return "\n".join(lines).strip()


def _format_item(item: dict, show_time: bool = True) -> str:
    """Форматування одного елемента."""
    parts = []
    
    # Статус
    if item['type'] == 'habit':
        status = item.get('today_status')
        if status == 'done':
            parts.append("✅")
        elif status == 'skipped':
            parts.append("⏭")
        else:
            parts.append("⬜")
    elif item['type'] == 'recurring_task':
        occ_status = item.get('occurrence', {}).get('status', 'pending')
        if occ_status == 'done':
            parts.append("✅")
        elif occ_status == 'skipped':
            parts.append("⏭")
        else:
            parts.append("⬜")
    elif item['type'] == 'task':
        # Пріоритет
        priority_icons = ["🔴", "🟠", "🟡", "🟢"]
        priority = item.get('priority', 2)
        parts.append(priority_icons[priority])
    
    # Час
    if show_time and item.get('time'):
        time_str = item['time']
        if item.get('end_time'):
            time_str += f"-{item['end_time']}"
        parts.append(time_str)
    
    # Назва
    parts.append(item.get('title', '???'))
    
    # Duration для habit
    if item['type'] == 'habit' and item.get('duration'):
        parts.append(f"({item['duration']} хв)")
    
    # Streak
    if item.get('streak'):
        parts.append(f"🔥{item['streak']}")
    
    # Occurrence number
    if item.get('occurrence', {}).get('occurrence_number'):
        parts.append(f"[#{item['occurrence']['occurrence_number']}]")
    
    # Fixed marker
    if item.get('is_fixed'):
        parts.append("📌")
    
    # Project link
    if item.get('goal_title') and item['type'] not in ('habit',):
        parts.append(f"→ [{item['goal_title']}]")
    
    return " ".join(str(p) for p in parts)


def _get_goal_id(item: dict) -> int | None:
    """Отримати goal_id для task."""
    if item['type'] == 'task':
        return item.get('goal_id')
    return None


def _get_parent_project(item: dict) -> int | None:
    """Отримати parent_id для habit."""
    if item['type'] == 'habit':
        return item.get('parent_id')
    return None


def _calculate_progress(schedule: dict) -> tuple[int, int]:
    """Підрахунок прогресу (done, total)."""
    done = 0
    total = 0
    
    for item in schedule['timeline']:
        total += 1
        
        if item['type'] == 'habit':
            if item.get('today_status') == 'done':
                done += 1
        elif item['type'] == 'recurring_task':
            if item.get('occurrence', {}).get('status') == 'done':
                done += 1
        elif item['type'] == 'task':
            # Task зі schedule — перевіряємо is_completed
            pass  # Якщо task тут — він ще не виконаний
    
    return (done, total)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                            CALLBACKS                                         ║
# ╚════════════════════════════════════════════════════════════════════════════╝

@router.callback_query(F.data.startswith("today:sort:"))
async def callback_sort_mode(callback: CallbackQuery):
    """Змінити режим сортування."""
    mode = callback.data.replace("today:sort:", "")
    
    user_id = callback.from_user.id
    schedule = await queries.get_today_schedule(user_id)
    text = await _format_today(schedule, mode)
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_today_keyboard(mode)
    )
    await callback.answer()


@router.callback_query(F.data == "today:refresh")
async def callback_refresh(callback: CallbackQuery):
    """Оновити dashboard."""
    user_id = callback.from_user.id
    schedule = await queries.get_today_schedule(user_id)
    text = await _format_today(schedule, 'time')
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_today_keyboard('time')
    )
    await callback.answer("🔄 Оновлено")


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                         RECURRING TASKS                                      ║
# ╚════════════════════════════════════════════════════════════════════════════╝

@router.callback_query(F.data.startswith("recurring:done:"))
async def callback_recurring_done(callback: CallbackQuery):
    """Позначити recurring task виконаною."""
    task_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    success = await queries.complete_occurrence(task_id, user_id)
    
    if success:
        await callback.answer("✅ Виконано!", show_alert=True)
        # Оновлюємо dashboard
        await callback_refresh(callback)
    else:
        await callback.answer("❌ Помилка", show_alert=True)


@router.callback_query(F.data.startswith("recurring:skip:"))
async def callback_recurring_skip(callback: CallbackQuery):
    """Пропустити recurring task."""
    task_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    # Отримуємо task для назви
    task = await queries.get_task_by_id(task_id, user_id)
    
    success = await queries.skip_occurrence(task_id, user_id)
    
    if success:
        time_str = ""
        if task and task.get('scheduled_time'):
            time_str = f"\nЧас {task['scheduled_time']}"
            if task.get('scheduled_end'):
                time_str += f"-{task['scheduled_end']}"
            time_str += " тепер вільний."
        
        await callback.message.edit_text(
            f"⏭ <b>{task['title'] if task else 'Задачу'}</b> пропущено.{time_str}",
            parse_mode="HTML",
            reply_markup=get_recurring_task_actions(task_id, 'skipped')
        )
        await callback.answer()
    else:
        await callback.answer("❌ Помилка", show_alert=True)


@router.callback_query(F.data.startswith("recurring:unskip:"))
async def callback_recurring_unskip(callback: CallbackQuery):
    """Повернути пропущену recurring task."""
    task_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    success = await queries.unskip_occurrence(task_id, user_id)
    
    if success:
        await callback.answer("↩️ Повернуто в розклад")
        await callback_refresh(callback)
    else:
        await callback.answer("❌ Помилка", show_alert=True)


@router.callback_query(F.data.startswith("recurring:undone:"))
async def callback_recurring_undone(callback: CallbackQuery):
    """Скасувати виконання recurring task."""
    task_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    # Оновлюємо статус на pending
    db = await queries.get_db()
    try:
        today = date.today().isoformat()
        await db.execute(
            """
            UPDATE task_occurrences 
            SET status = 'pending', completed_at = NULL
            WHERE task_id = ? AND date = ?
            """,
            (task_id, today)
        )
        await db.commit()
    finally:
        await db.close()
    
    await callback.answer("↩️ Скасовано")
    await callback_refresh(callback)


@router.callback_query(F.data.startswith("recurring:stats:"))
async def callback_recurring_stats(callback: CallbackQuery):
    """Статистика recurring task."""
    task_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    task = await queries.get_task_by_id(task_id, user_id)
    stats = await queries.get_task_occurrence_stats(task_id)
    
    if not task:
        await callback.answer("❌ Не знайдено", show_alert=True)
        return
    
    text = f"""
📊 <b>Статистика: {task['title']}</b>

📅 Всього: {stats['total']} разів
✅ Виконано: {stats['done']} ({stats['success_rate']}%)
⏭ Пропущено: {stats['skipped']}
"""
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="today:refresh")
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                         MORNING / EVENING                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝

@router.message(Command("morning"))
async def cmd_morning(message: Message):
    """Ранковий огляд."""
    user_id = message.from_user.id
    schedule = await queries.get_today_schedule(user_id)
    
    today = date.today()
    weekday_name = uk.TODAY['weekdays'][today.weekday()]
    
    text = f"🌅 <b>Доброго ранку!</b>\n\n"
    text += f"Сьогодні {weekday_name}, {today.strftime('%d.%m.%Y')}\n\n"
    
    # Підсумок
    total = len(schedule['timeline'])
    habits_count = sum(1 for i in schedule['timeline'] if i['type'] == 'habit')
    tasks_count = sum(1 for i in schedule['timeline'] if i['type'] in ('task', 'recurring_task'))
    
    text += f"📋 Задач: {tasks_count}\n"
    text += f"✅ Звичок: {habits_count}\n\n"
    
    # Перші 5 елементів з часом
    with_time = [i for i in schedule['timeline'] if i.get('time')][:5]
    if with_time:
        text += "<b>Найближче:</b>\n"
        for item in with_time:
            text += f"  {item.get('time', '')} {item.get('title', '')}\n"
    
    text += "\n💪 Гарного продуктивного дня!"
    
    from bot.keyboards.today import get_morning_keyboard
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_morning_keyboard()
    )


@router.message(Command("evening"))
async def cmd_evening(message: Message):
    """Вечірній підсумок."""
    user_id = message.from_user.id
    schedule = await queries.get_today_schedule(user_id)
    
    done, total = _calculate_progress(schedule)
    percent = int(done / total * 100) if total > 0 else 0
    
    text = f"🌙 <b>Підсумок дня</b>\n\n"
    text += f"📊 Виконано: {done}/{total} ({percent}%)\n\n"
    
    # Виконані
    completed = []
    pending = []
    
    for item in schedule['timeline']:
        is_done = False
        if item['type'] == 'habit' and item.get('today_status') == 'done':
            is_done = True
        elif item['type'] == 'recurring_task' and item.get('occurrence', {}).get('status') == 'done':
            is_done = True
        
        if is_done:
            completed.append(item)
        else:
            pending.append(item)
    
    if completed:
        text += "<b>✅ Виконано:</b>\n"
        for item in completed[:5]:
            streak = f" 🔥{item['streak']}" if item.get('streak') else ""
            text += f"  • {item.get('title', '')}{streak}\n"
        if len(completed) > 5:
            text += f"  <i>...і ще {len(completed) - 5}</i>\n"
        text += "\n"
    
    if pending:
        text += "<b>❌ Не виконано:</b>\n"
        for item in pending[:3]:
            text += f"  • {item.get('title', '')}\n"
    
    if percent >= 80:
        text += "\n🎉 Відмінний день!"
    elif percent >= 50:
        text += "\n👍 Непогано!"
    else:
        text += "\n💪 Завтра буде краще!"
    
    from bot.keyboards.today import get_evening_keyboard
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_evening_keyboard()
    )


@router.callback_query(F.data == "today:start_day")
async def callback_start_day(callback: CallbackQuery):
    """Кнопка 'Почати день'."""
    await cmd_today(callback.message)
    await callback.answer()
