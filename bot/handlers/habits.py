"""
Обробники звичок.
LifeHub Bot v4.0

ВАЖЛИВО: Habits ≠ Recurring Tasks!
- Habit: streak tracking, мотивація безперервністю
- Recurring Task: статистика виконання, БЕЗ streak

Streak правила:
- 'done' або 'skipped' — streak зберігається
- Пропуск без логу — streak = 0
"""

from datetime import date
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.database import queries
from bot.states.states import HabitCreation
from bot.keyboards import habits as kb
from bot.keyboards.reply import get_main_menu, get_cancel_keyboard
from bot.locales import uk


router = Router()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                              КОМАНДИ                                         ║
# ╚════════════════════════════════════════════════════════════════════════════╝

@router.message(Command("habits"))
async def cmd_habits(message: Message):
    """Показати звички на сьогодні."""
    user_id = message.from_user.id
    habits = await queries.get_habits_today(user_id)
    
    if not habits:
        await message.answer(
            f"{uk.HABITS['title_today']}\n\n{uk.HABITS['empty']}",
            parse_mode="HTML"
        )
        return
    
    today = date.today()
    weekday = uk.TODAY['weekdays'][today.isoweekday() - 1]
    
    text = f"{uk.HABITS['title_today']} ({weekday})\n\n"
    
    done_count = 0
    
    for habit in habits:
        # Визначаємо статус
        today_status = habit.get('today_status')
        if today_status == 'done':
            status = "✅"
            done_count += 1
        elif today_status == 'skipped':
            status = "⏭"
            done_count += 1  # skipped теж рахується як "зроблено"
        else:
            status = "⬜"
        
        streak = habit.get('current_streak', 0)
        streak_text = f" 🔥{streak}" if streak > 0 else ""
        
        time_text = ""
        if habit.get('reminder_time'):
            time_text = f" {habit['reminder_time']}"
        
        text += f"{status}{time_text} {habit['title']}{streak_text}\n"
    
    text += f"\n📊 Прогрес: {done_count}/{len(habits)}"
    
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=kb.get_habits_today(habits)
    )


@router.message(Command("habit_add"))
async def cmd_habit_add(message: Message, state: FSMContext):
    """Почати створення звички."""
    await state.clear()
    await state.set_state(HabitCreation.title)
    
    await message.answer(
        uk.HABITS['create_title'],
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                         ДІАЛОГ СТВОРЕННЯ                                     ║
# ╚════════════════════════════════════════════════════════════════════════════╝

@router.message(HabitCreation.title)
async def habit_title(message: Message, state: FSMContext):
    """Отримуємо назву звички."""
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer(uk.CANCELLED, reply_markup=get_main_menu())
        return
    
    await state.update_data(title=message.text)
    await state.set_state(HabitCreation.frequency)
    
    await message.answer(
        uk.HABITS['create_frequency'],
        reply_markup=kb.get_frequency_keyboard()
    )


@router.callback_query(HabitCreation.frequency, F.data.startswith("habit:freq:"))
async def habit_frequency(callback: CallbackQuery, state: FSMContext):
    """Отримуємо частоту."""
    frequency = callback.data.replace("habit:freq:", "")
    
    if frequency == "custom":
        await state.update_data(frequency="custom", selected_days=[])
        await state.set_state(HabitCreation.schedule_days)
        await callback.message.edit_text(
            uk.HABITS['create_days'],
            reply_markup=kb.get_weekdays_keyboard([])
        )
    else:
        await state.update_data(frequency=frequency)
        await state.set_state(HabitCreation.reminder_time)
        await callback.message.edit_text(
            uk.HABITS['create_time'],
            reply_markup=kb.get_time_keyboard()
        )
    
    await callback.answer()


@router.callback_query(HabitCreation.schedule_days, F.data.startswith("habit:day:"))
async def habit_day_toggle(callback: CallbackQuery, state: FSMContext):
    """Перемикання дня тижня."""
    day = int(callback.data.replace("habit:day:", ""))
    data = await state.get_data()
    selected = data.get('selected_days', [])
    
    if day in selected:
        selected.remove(day)
    else:
        selected.append(day)
    
    await state.update_data(selected_days=selected)
    await callback.message.edit_reply_markup(
        reply_markup=kb.get_weekdays_keyboard(selected)
    )
    await callback.answer()


@router.callback_query(HabitCreation.schedule_days, F.data == "habit:days:done")
async def habit_days_done(callback: CallbackQuery, state: FSMContext):
    """Завершення вибору днів."""
    data = await state.get_data()
    selected = data.get('selected_days', [])
    
    if not selected:
        await callback.answer("⚠️ Обери хоча б один день", show_alert=True)
        return
    
    schedule_days = ",".join(str(d) for d in sorted(selected))
    await state.update_data(schedule_days=schedule_days)
    
    await state.set_state(HabitCreation.reminder_time)
    await callback.message.edit_text(
        uk.HABITS['create_time'],
        reply_markup=kb.get_time_keyboard()
    )
    await callback.answer()


@router.callback_query(HabitCreation.reminder_time, F.data.startswith("habit:time:"))
async def habit_time(callback: CallbackQuery, state: FSMContext):
    """Отримуємо час нагадування."""
    time_value = callback.data.replace("habit:time:", "")
    
    if time_value == "custom":
        await state.set_state(HabitCreation.time_custom)
        await callback.message.edit_text("⏰ Введи час (ГГ:ХХ):")
        await callback.answer()
        return
    
    reminder_time = None if time_value == "none" else time_value
    await state.update_data(reminder_time=reminder_time)
    
    await state.set_state(HabitCreation.duration)
    await callback.message.edit_text(
        uk.HABITS['create_duration'],
        reply_markup=kb.get_duration_keyboard()
    )
    await callback.answer()


@router.message(HabitCreation.time_custom)
async def habit_time_custom(message: Message, state: FSMContext):
    """Отримуємо кастомний час."""
    text = message.text.strip()
    
    try:
        if ":" not in text:
            raise ValueError
        hours, minutes = text.split(":")
        if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
            raise ValueError
        reminder_time = f"{int(hours):02d}:{int(minutes):02d}"
    except ValueError:
        await message.answer(uk.ERRORS['invalid_time'])
        return
    
    await state.update_data(reminder_time=reminder_time)
    await state.set_state(HabitCreation.duration)
    
    await message.answer(
        uk.HABITS['create_duration'],
        reply_markup=kb.get_duration_keyboard()
    )


@router.callback_query(HabitCreation.duration, F.data.startswith("habit:duration:"))
async def habit_duration(callback: CallbackQuery, state: FSMContext):
    """Отримуємо тривалість."""
    duration_value = callback.data.replace("habit:duration:", "")
    
    duration = None if duration_value == "none" else int(duration_value)
    await state.update_data(duration_minutes=duration)
    
    # Перевіряємо чи є проєкти
    user_id = callback.from_user.id
    projects = await queries.get_projects(user_id)
    
    if projects:
        await state.set_state(HabitCreation.parent)
        from bot.keyboards.goals import get_parent_keyboard
        await callback.message.edit_text(
            uk.HABITS['create_parent'],
            reply_markup=get_parent_keyboard(projects)
        )
    else:
        await _create_habit(callback, state)
    
    await callback.answer()


@router.callback_query(HabitCreation.parent, F.data.startswith("goal:parent:"))
async def habit_parent(callback: CallbackQuery, state: FSMContext):
    """Отримуємо батьківський проєкт."""
    parent_value = callback.data.replace("goal:parent:", "")
    
    parent_id = None if parent_value == "none" else int(parent_value)
    await state.update_data(parent_id=parent_id)
    
    await _create_habit(callback, state)


async def _create_habit(callback: CallbackQuery, state: FSMContext):
    """Фінальне створення звички."""
    data = await state.get_data()
    user_id = callback.from_user.id
    
    habit_id = await queries.create_goal(
        user_id=user_id,
        title=data['title'],
        goal_type='habit',
        frequency=data.get('frequency', 'daily'),
        schedule_days=data.get('schedule_days'),
        reminder_time=data.get('reminder_time'),
        duration_minutes=data.get('duration_minutes'),
        parent_id=data.get('parent_id'),
    )
    
    await state.clear()
    
    freq_labels = {
        'daily': 'Щодня',
        'weekdays': 'По буднях',
        'custom': 'Обрані дні'
    }
    
    parent_str = "Без проєкту"
    if data.get('parent_id'):
        parent = await queries.get_goal_by_id(data['parent_id'], user_id)
        if parent:
            parent_str = parent['title']
    
    text = uk.HABITS['create_confirm'].format(
        title=data['title'],
        frequency=freq_labels.get(data.get('frequency', 'daily'), data.get('frequency')),
        time=data.get('reminder_time') or 'Без часу',
        duration=data.get('duration_minutes') or '—',
        parent=parent_str
    )
    
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer("✅ Звичку створено!")


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                            CALLBACK ACTIONS                                  ║
# ╚════════════════════════════════════════════════════════════════════════════╝

@router.callback_query(F.data == "habit:add")
async def callback_habit_add(callback: CallbackQuery, state: FSMContext):
    """Додати звичку через inline."""
    await state.clear()
    await state.set_state(HabitCreation.title)
    
    await callback.message.answer(
        uk.HABITS['create_title'],
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "habits:today")
async def callback_habits_today(callback: CallbackQuery):
    """Повернутись до списку звичок."""
    await cmd_habits(callback.message)
    await callback.answer()


@router.callback_query(F.data.startswith("habit:view:"))
async def callback_habit_view(callback: CallbackQuery):
    """Переглянути деталі звички."""
    habit_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    habit = await queries.get_goal_by_id(habit_id, user_id)
    
    if not habit or habit['goal_type'] != 'habit':
        await callback.answer("❌ Звичку не знайдено", show_alert=True)
        return
    
    freq_labels = {
        'daily': 'Щодня',
        'weekdays': 'По буднях (Пн-Пт)',
        'custom': 'Обрані дні'
    }
    
    text = f"""
✅ <b>{habit['title']}</b>

🔥 Поточна серія: <b>{habit.get('current_streak', 0)}</b> днів
🏆 Найдовша: <b>{habit.get('longest_streak', 0)}</b> днів

📅 Частота: {freq_labels.get(habit.get('frequency'), habit.get('frequency'))}
⏰ Час: {habit.get('reminder_time') or 'Не вказано'}
⏱ Тривалість: {habit.get('duration_minutes') or '—'} хв
"""
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=kb.get_habit_actions(habit_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("habit:done:"))
async def callback_habit_done(callback: CallbackQuery):
    """Позначити звичку виконаною."""
    habit_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    await queries.log_habit(habit_id, user_id, 'done')
    
    habit = await queries.get_goal_by_id(habit_id, user_id)
    streak = habit.get('current_streak', 0) if habit else 0
    title = habit['title'] if habit else ''
    
    await callback.answer(
        uk.HABITS['marked_done'].format(title=title, streak=streak),
        show_alert=True
    )
    
    await cmd_habits(callback.message)


@router.callback_query(F.data.startswith("habit:skip:"))
async def callback_habit_skip(callback: CallbackQuery):
    """Пропустити звичку (streak зберігається)."""
    habit_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    await queries.log_habit(habit_id, user_id, 'skipped')
    
    habit = await queries.get_goal_by_id(habit_id, user_id)
    title = habit['title'] if habit else ''
    
    await callback.answer(
        uk.HABITS['marked_skip'].format(title=title),
        show_alert=True
    )
    
    await cmd_habits(callback.message)


@router.callback_query(F.data.startswith("habit:undone:"))
async def callback_habit_undone(callback: CallbackQuery):
    """Скасувати виконання звички."""
    habit_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    # Видаляємо лог за сьогодні
    db = await queries.get_db()
    try:
        today = date.today().isoformat()
        await db.execute(
            "DELETE FROM habit_logs WHERE goal_id = ? AND user_id = ? AND date = ?",
            (habit_id, user_id, today)
        )
        await db.commit()
    finally:
        await db.close()
    
    await callback.answer("↩️ Скасовано")
    await cmd_habits(callback.message)


@router.callback_query(F.data == "habit:all_done")
async def callback_habit_all_done(callback: CallbackQuery):
    """Позначити всі звички виконаними."""
    user_id = callback.from_user.id
    habits = await queries.get_habits_today(user_id)
    
    count = 0
    for habit in habits:
        if habit.get('today_status') not in ('done', 'skipped'):
            await queries.log_habit(habit['id'], user_id, 'done')
            count += 1
    
    await callback.answer(f"✅ Позначено {count} звичок")
    await cmd_habits(callback.message)


@router.callback_query(F.data.startswith("habit:stats:"))
async def callback_habit_stats(callback: CallbackQuery):
    """Показати статистику звички."""
    habit_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    habit = await queries.get_goal_by_id(habit_id, user_id)
    stats = await queries.get_habit_stats(habit_id, user_id)
    
    if not habit:
        await callback.answer("❌ Звичку не знайдено", show_alert=True)
        return
    
    text = uk.HABITS['stats_template'].format(
        title=habit['title'],
        current_streak=habit.get('current_streak', 0),
        longest_streak=habit.get('longest_streak', 0),
        month_done=stats.get('month_done', 0),
        month_total=stats.get('month_total', 0),
        month_rate=stats.get('month_rate', 0),
        total_done=stats.get('total_done', 0)
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=kb.get_stats_keyboard(habit_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("habit:delete:"))
async def callback_habit_delete(callback: CallbackQuery):
    """Підтвердження видалення."""
    habit_id = int(callback.data.split(":")[-1])
    
    await callback.message.edit_text(
        "🗑 <b>Видалити звичку?</b>\n\nСерія буде втрачена назавжди!",
        parse_mode="HTML",
        reply_markup=kb.get_delete_confirm(habit_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("habit:delete_confirm:"))
async def callback_habit_delete_confirm(callback: CallbackQuery):
    """Фінальне видалення."""
    habit_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    success = await queries.delete_goal(habit_id, user_id)
    
    if success:
        await callback.message.edit_text(uk.HABITS['deleted'])
        await callback.answer("🗑 Видалено")
    else:
        await callback.answer("❌ Помилка", show_alert=True)


@router.callback_query(F.data == "habit:cancel")
async def callback_habit_cancel(callback: CallbackQuery, state: FSMContext):
    """Скасування створення."""
    await state.clear()
    await callback.message.edit_text(uk.CANCELLED)
    await callback.answer()
