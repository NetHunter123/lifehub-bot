"""
Обробник /today — Dashboard на сьогодні.
LifeHub Bot v4.0

АРХІТЕКТУРА:
- time_blocks ВИДАЛЕНО!
- Замість них: recurring tasks з is_fixed=1
- Habits ОКРЕМО від recurring tasks (streak vs статистика)

Елементи dashboard:
1. Recurring tasks (is_fixed=1: школа, робота; is_fixed=0: гнучкі)
2. One-time tasks (з дедлайном сьогодні/прострочені)  
3. Habits (зі streak tracking)

Два режими відображення:
- За часом (chronological) — default
- За типом (grouped)
"""

from datetime import date
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from bot.database import queries
from bot.keyboards import today as kb
from bot.locales import uk


router = Router()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                              КОМАНДИ                                         ║
# ╚════════════════════════════════════════════════════════════════════════════╝

@router.message(Command("today"))
async def cmd_today(message: Message, sort_mode: str = 'time'):
    """Показати dashboard на сьогодні."""
    user_id = message.from_user.id
    
    schedule = await queries.get_today_schedule(user_id)
    
    today = date.today()
    weekday = uk.TODAY['weekdays'][today.isoweekday() - 1]
    date_str = today.strftime("%d.%m")
    
    if not schedule['timeline']:
        text = f"📅 <b>СЬОГОДНІ</b> — {weekday}, {date_str}\n\n{uk.TODAY['empty']}"
        await message.answer(text, parse_mode="HTML", reply_markup=kb.get_today_keyboard())
        return
    
    if sort_mode == 'time':
        text = await _format_by_time(schedule, weekday, date_str)
    else:
        text = await _format_by_type(schedule, weekday, date_str)
    
    # Рахуємо прогрес
    done_count = 0
    total_count = len(schedule['timeline'])
    
    for item in schedule['timeline']:
        if item['type'] == 'habit':
            if item.get('today_status') in ('done', 'skipped'):
                done_count += 1
        elif item['type'] == 'task':
            if item.get('is_completed'):
                done_count += 1
        elif item['type'] == 'recurring_task':
            if item['occurrence']['status'] in ('done', 'skipped'):
                done_count += 1
    
    percent = int(done_count / total_count * 100) if total_count > 0 else 0
    text += f"\n{uk.TODAY['progress'].format(done=done_count, total=total_count, percent=percent)}"
    
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=kb.get_today_keyboard(sort_mode)
    )


async def _format_by_time(schedule: dict, weekday: str, date_str: str) -> str:
    """Форматування по часу (chronological)."""
    text = f"📅 <b>СЬОГОДНІ</b> — {weekday}, {date_str}\n\n"
    
    # Елементи з часом
    with_time = [i for i in schedule['timeline'] if i.get('time')]
    without_time = [i for i in schedule['timeline'] if not i.get('time')]
    
    for item in with_time:
        line = _format_timeline_item(item)
        text += f"{line}\n"
    
    if without_time:
        text += "\n── без часу ──\n"
        for item in without_time:
            line = _format_timeline_item(item)
            text += f"{line}\n"
    
    return text


async def _format_by_type(schedule: dict, weekday: str, date_str: str) -> str:
    """Форматування по типу (grouped)."""
    text = f"📅 <b>СЬОГОДНІ</b> — {weekday}, {date_str}\n\n"
    
    # Групуємо
    fixed = [i for i in schedule['timeline'] if i['type'] == 'recurring_task' and i.get('is_fixed')]
    recurring = [i for i in schedule['timeline'] if i['type'] == 'recurring_task' and not i.get('is_fixed')]
    tasks = [i for i in schedule['timeline'] if i['type'] == 'task']
    habits = [i for i in schedule['timeline'] if i['type'] == 'habit']
    
    if fixed:
        text += "🏫 <b>ФІКСОВАНИЙ ЧАС:</b>\n"
        for item in fixed:
            line = _format_timeline_item(item, show_type=False)
            text += f"  {line}\n"
        text += "\n"
    
    if tasks:
        text += "📋 <b>ЗАДАЧІ:</b>\n"
        for item in sorted(tasks, key=lambda x: x.get('priority', 2)):
            line = _format_timeline_item(item, show_type=False)
            text += f"  {line}\n"
        text += "\n"
    
    if recurring:
        text += "🔄 <b>ПОВТОРЮВАНІ:</b>\n"
        for item in recurring:
            line = _format_timeline_item(item, show_type=False)
            text += f"  {line}\n"
        text += "\n"
    
    if habits:
        text += "✅ <b>ЗВИЧКИ:</b>\n"
        for item in habits:
            line = _format_timeline_item(item, show_type=False)
            text += f"  {line}\n"
    
    return text


def _format_timeline_item(item: dict, show_type: bool = True) -> str:
    """Форматування одного елемента timeline."""
    item_type = item['type']
    
    # Визначаємо статус
    if item_type == 'habit':
        if item.get('today_status') == 'done':
            status = "✅"
        elif item.get('today_status') == 'skipped':
            status = "⏭"
        else:
            status = "⬜"
    elif item_type == 'task':
        status = "✅" if item.get('is_completed') else "⬜"
    elif item_type == 'recurring_task':
        occ_status = item['occurrence']['status']
        if occ_status == 'done':
            status = "✅"
        elif occ_status == 'skipped':
            status = "⏭"
        else:
            status = "⬜"
    else:
        status = "•"
    
    # Час
    time_str = ""
    if item.get('time'):
        time_str = f"{item['time']} "
        if item.get('end_time'):
            time_str = f"{item['time']}-{item['end_time']} "
    
    # Пріоритет для tasks
    priority_str = ""
    if item_type == 'task':
        priority_icons = ["🔴", "🟠", "🟡", "🟢"]
        priority_str = f"{priority_icons[item.get('priority', 2)]} "
    
    # Фіксований час
    fixed_str = ""
    if item.get('is_fixed'):
        fixed_str = " 📌"
    
    # Streak для habits
    streak_str = ""
    if item_type == 'habit' and item.get('streak', 0) > 0:
        streak_str = f" 🔥{item['streak']}"
    
    # Occurrence number для recurring
    occ_str = ""
    if item_type == 'recurring_task':
        occ_num = item['occurrence'].get('occurrence_number', 0)
        if occ_num > 0:
            occ_str = f" [#{occ_num}]"
    
    # Прив'язка до проєкту
    goal_str = ""
    if item.get('goal_title'):
        goal_str = f" → {item['goal_title']}"
    elif item.get('parent_id'):
        goal_str = " → 📁"
    
    return f"{status} {time_str}{priority_str}{item['title']}{streak_str}{occ_str}{fixed_str}{goal_str}"


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                            CALLBACK ACTIONS                                  ║
# ╚════════════════════════════════════════════════════════════════════════════╝

@router.callback_query(F.data == "today:refresh")
async def callback_today_refresh(callback: CallbackQuery):
    """Оновити dashboard."""
    await cmd_today(callback.message)
    await callback.answer("🔄 Оновлено")


@router.callback_query(F.data.startswith("today:sort:"))
async def callback_today_sort(callback: CallbackQuery):
    """Змінити режим сортування."""
    sort_mode = callback.data.replace("today:sort:", "")
    await cmd_today(callback.message, sort_mode=sort_mode)
    await callback.answer()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                         RECURRING TASK ACTIONS                               ║
# ╚════════════════════════════════════════════════════════════════════════════╝

@router.callback_query(F.data.startswith("recurring:done:"))
async def callback_recurring_done(callback: CallbackQuery):
    """Позначити recurring task виконаним."""
    task_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    # Переконуємось що occurrence існує
    await queries.get_or_create_occurrence(task_id, user_id)
    success = await queries.complete_occurrence(task_id, user_id)
    
    if success:
        task = await queries.get_task_by_id(task_id, user_id)
        occ = await queries.get_or_create_occurrence(task_id, user_id)
        
        await callback.answer(
            uk.RECURRING['marked_done'].format(
                title=task['title'] if task else '',
                occurrence_number=occ.get('occurrence_number', 0)
            ),
            show_alert=True
        )
        await cmd_today(callback.message)
    else:
        await callback.answer("❌ Помилка", show_alert=True)


@router.callback_query(F.data.startswith("recurring:skip:"))
async def callback_recurring_skip(callback: CallbackQuery):
    """Пропустити recurring task."""
    task_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    await queries.get_or_create_occurrence(task_id, user_id)
    success = await queries.skip_occurrence(task_id, user_id)
    
    if success:
        task = await queries.get_task_by_id(task_id, user_id)
        await callback.answer(
            uk.RECURRING['marked_skip'].format(title=task['title'] if task else ''),
            show_alert=True
        )
        await cmd_today(callback.message)
    else:
        await callback.answer("❌ Помилка", show_alert=True)


@router.callback_query(F.data.startswith("recurring:undone:"))
async def callback_recurring_undone(callback: CallbackQuery):
    """Скасувати виконання recurring task."""
    task_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    db = await queries.get_db()
    try:
        today = date.today().isoformat()
        await db.execute(
            "UPDATE task_occurrences SET status = 'pending', completed_at = NULL WHERE task_id = ? AND date = ?",
            (task_id, today)
        )
        await db.commit()
    finally:
        await db.close()
    
    await callback.answer("↩️ Скасовано")
    await cmd_today(callback.message)


@router.callback_query(F.data.startswith("recurring:unskip:"))
async def callback_recurring_unskip(callback: CallbackQuery):
    """Повернути пропущений recurring task."""
    task_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    success = await queries.unskip_occurrence(task_id, user_id)
    
    if success:
        await callback.answer("↩️ Повернуто")
        await cmd_today(callback.message)
    else:
        await callback.answer("❌ Помилка", show_alert=True)


@router.callback_query(F.data.startswith("recurring:stats:"))
async def callback_recurring_stats(callback: CallbackQuery):
    """Показати статистику recurring task."""
    task_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    task = await queries.get_task_by_id(task_id, user_id)
    stats = await queries.get_task_occurrence_stats(task_id)
    
    if not task:
        await callback.answer("❌ Не знайдено", show_alert=True)
        return
    
    text = f"""
🔄 <b>{task['title']}</b>

📊 <b>Статистика:</b>
• Всього: {stats['total']} разів
• Виконано: {stats['done']}
• Пропущено: {stats['skipped']}
• Успішність: {stats['success_rate']}%
"""
    
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                         MORNING/EVENING REMINDERS                            ║
# ╚════════════════════════════════════════════════════════════════════════════╝

async def send_morning_review(user_id: int, bot) -> None:
    """
    Ранковий огляд (08:00).
    Викликається з APScheduler.
    """
    schedule = await queries.get_today_schedule(user_id)
    
    today = date.today()
    weekday = uk.TODAY['weekdays'][today.isoweekday() - 1]
    
    text = f"🌅 <b>Доброго ранку!</b> Ось твій {weekday}:\n\n"
    
    # Задачі
    tasks = schedule['one_time_tasks']
    if tasks:
        text += f"📋 <b>Задачі ({len(tasks)}):</b>\n"
        for t in tasks[:5]:
            priority_icons = ["🔴", "🟠", "🟡", "🟢"]
            priority = priority_icons[t.get('priority', 2)]
            time_str = f" — {t['scheduled_time']}" if t.get('scheduled_time') else ""
            text += f"  {priority} [{t['id']}] {t['title']}{time_str}\n"
        if len(tasks) > 5:
            text += f"  ... та ще {len(tasks) - 5}\n"
        text += "\n"
    
    # Recurring
    recurring = schedule['recurring_tasks']
    if recurring:
        text += f"🔄 <b>Recurring ({len(recurring)}):</b>\n"
        for r in recurring[:3]:
            time_str = f"{r['scheduled_time']} " if r.get('scheduled_time') else ""
            fixed = "📌" if r.get('is_fixed') else ""
            text += f"  • {time_str}{r['title']} {fixed}\n"
        text += "\n"
    
    # Звички
    habits = schedule['habits']
    if habits:
        text += f"✅ <b>Звички ({len(habits)}):</b>\n"
        for h in habits:
            streak = f"🔥{h.get('current_streak', 0)}" if h.get('current_streak', 0) > 0 else ""
            text += f"  ⬜ {h['title']} {streak}\n"
        text += "\n"
    
    text += "💪 Гарного продуктивного дня!"
    
    await bot.send_message(
        user_id,
        text,
        parse_mode="HTML",
        reply_markup=kb.get_morning_keyboard()
    )


async def send_evening_summary(user_id: int, bot) -> None:
    """
    Вечірній підсумок (21:00).
    Викликається з APScheduler.
    """
    schedule = await queries.get_today_schedule(user_id)
    
    text = "🌙 <b>Підсумок дня:</b>\n\n"
    
    # Задачі
    tasks = schedule['one_time_tasks']
    if tasks:
        done = sum(1 for t in tasks if t['is_completed'])
        text += f"📋 <b>Задачі:</b> {done}/{len(tasks)}\n"
        for t in tasks:
            status = "✅" if t['is_completed'] else "❌"
            text += f"  {status} {t['title']}\n"
        text += "\n"
    
    # Звички
    habits = schedule['habits']
    if habits:
        done = sum(1 for h in habits if h.get('today_status') in ('done', 'skipped'))
        text += f"✅ <b>Звички:</b> {done}/{len(habits)}\n"
        for h in habits:
            if h.get('today_status') == 'done':
                status = "✅"
                streak_info = f" — 🔥{h.get('current_streak', 0)} днів!"
            elif h.get('today_status') == 'skipped':
                status = "⏭"
                streak_info = ""
            else:
                status = "❌"
                streak_info = " — серія втрачена 😢"
            text += f"  {status} {h['title']}{streak_info}\n"
    
    await bot.send_message(
        user_id,
        text,
        parse_mode="HTML",
        reply_markup=kb.get_evening_keyboard()
    )


@router.callback_query(F.data == "today:start_day")
async def callback_start_day(callback: CallbackQuery):
    """Кнопка 'Почати день'."""
    await callback.message.edit_text("💪 Гарного дня! Починай з найважливішого!")
    await callback.answer()


@router.callback_query(F.data.startswith("today:snooze:"))
async def callback_snooze(callback: CallbackQuery):
    """Відкласти нагадування."""
    minutes = int(callback.data.split(":")[-1])
    await callback.message.edit_text(f"⏰ Нагадаю через {minutes} хвилин...")
    await callback.answer()
    # TODO: Реалізувати через APScheduler


@router.callback_query(F.data == "today:note")
async def callback_today_note(callback: CallbackQuery):
    """Додати нотатку до дня."""
    await callback.answer("📝 В розробці...", show_alert=True)


@router.callback_query(F.data == "today:plan_tomorrow")
async def callback_plan_tomorrow(callback: CallbackQuery):
    """Планувати завтра."""
    await callback.answer("📅 В розробці...", show_alert=True)
