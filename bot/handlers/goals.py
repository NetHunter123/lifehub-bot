"""
Обробники команд для цілей v3.
5 структурних типів: task, project, habit, target, metric.
"""

from datetime import datetime, date, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards.goals import (
    get_goal_type_keyboard,
    get_frequency_keyboard,
    get_parent_keyboard,
    get_deadline_keyboard,
    get_goals_list_keyboard,
    get_goal_actions_keyboard,
    get_goal_edit_keyboard,
    get_confirm_keyboard,
    get_habits_today_keyboard,
    get_domain_tags_keyboard,
    GoalCallback, GoalAction, GoalTypeCallback, GoalParentCallback,
    FrequencyCallback, GoalEditCallback, GoalEditField, GoalType, GOAL_TYPE_EMOJI,
)
from bot.keyboards.reply import get_main_reply_keyboard, get_cancel_keyboard, get_skip_cancel_keyboard
from bot.locales import t, get_user_lang
from bot.database import goal_queries as gq

router = Router()


# ============== FSM STATES ==============

class GoalCreation(StatesGroup):
    title = State()
    goal_type = State()
    # Habit-specific
    frequency = State()
    schedule_days = State()
    reminder_time = State()
    duration = State()          # Тривалість звички
    # Target-specific
    target_value = State()
    unit = State()
    # Metric-specific
    target_range = State()
    # Common
    parent = State()
    deadline = State()
    domain_tags = State()


class GoalEdit(StatesGroup):
    waiting_value = State()


class GoalEntry(StatesGroup):
    value = State()


# ============== HELPERS ==============

def format_goal(goal: dict, lang: str) -> str:
    """Форматує ціль для відображення."""
    emoji = GOAL_TYPE_EMOJI.get(GoalType(goal['goal_type']), "🎯")
    type_name = t(f"goal_type_{goal['goal_type']}", lang)
    status_emoji = "✅" if goal.get('status') == 'completed' else "📌"
    
    lines = [
        f"{status_emoji} <b>{goal['title']}</b>",
        f"",
        f"📊 {t('goal_type_label', lang)}: {emoji} {type_name}",
    ]
    
    # Прогрес/streak залежно від типу
    if goal['goal_type'] == 'habit':
        streak = goal.get('current_streak', 0)
        longest = goal.get('longest_streak', 0)
        lines.append(f"🔥 {t('streak', lang)}: {streak} ({t('best', lang)}: {longest})")
        
        # Час і тривалість для звички
        if goal.get('reminder_time'):
            lines.append(f"⏰ {t('time', lang)}: {goal['reminder_time']}")
        if goal.get('duration_minutes'):
            lines.append(f"⏱ {t('duration', lang)}: {goal['duration_minutes']} {t('minutes', lang)}")
            
    elif goal['goal_type'] == 'target':
        current = goal.get('current_value', 0)
        target = goal.get('target_value', 0)
        unit = goal.get('unit', '')
        progress = goal.get('progress', 0)
        bar = get_progress_bar(progress)
        lines.append(f"📈 {current}/{target} {unit} {bar} {progress}%")
    elif goal['goal_type'] == 'metric':
        current = goal.get('current_value', 0)
        unit = goal.get('unit', '')
        target_min = goal.get('target_min')
        target_max = goal.get('target_max')
        if target_min and target_max:
            lines.append(f"📈 {t('current', lang)}: {current} {unit} ({t('range', lang)}: {target_min}-{target_max})")
        else:
            lines.append(f"📈 {t('current', lang)}: {current} {unit}")
    else:
        progress = goal.get('progress', 0)
        bar = get_progress_bar(progress)
        lines.append(f"📈 {t('progress', lang)}: {bar} {progress}%")
    
    if goal.get('description'):
        lines.append(f"")
        lines.append(f"📝 {goal['description']}")
    
    if goal.get('deadline'):
        deadline_str = datetime.fromisoformat(goal['deadline']).strftime("%d.%m.%Y")
        lines.append(f"📅 {t('deadline', lang)}: {deadline_str}")
    
    if goal.get('frequency'):
        freq_key = f"freq_{goal['frequency']}"
        freq_text = t(freq_key, lang) if goal['frequency'] != 'custom' else format_schedule_days(goal.get('schedule_days', ''), lang)
        lines.append(f"🔄 {t('frequency', lang)}: {freq_text}")
    
    if goal.get('domain_tags'):
        tags = " ".join(f"#{tag}" for tag in goal['domain_tags'])
        lines.append(f"🏷 {tags}")
    
    created = datetime.fromisoformat(goal['created_at']).strftime("%d.%m.%Y")
    lines.append(f"")
    lines.append(f"🕐 {t('created', lang)}: {created}")
    
    return "\n".join(lines)


def format_schedule_days(schedule_days: str, lang: str) -> str:
    """Форматує дні тижня для відображення."""
    if not schedule_days:
        return ""
    
    day_names_uk = {1: 'Пн', 2: 'Вт', 3: 'Ср', 4: 'Чт', 5: 'Пт', 6: 'Сб', 7: 'Нд'}
    day_names_en = {1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu', 5: 'Fri', 6: 'Sat', 7: 'Sun'}
    day_names = day_names_uk if lang == 'uk' else day_names_en
    
    days = [int(d) for d in schedule_days.split(',') if d.strip().isdigit()]
    return ', '.join(day_names.get(d, str(d)) for d in days)


def get_progress_bar(progress: int, length: int = 10) -> str:
    filled = int(progress / 100 * length)
    return "█" * filled + "░" * (length - filled)


def format_goals_list(goals: list, title: str, lang: str) -> str:
    """Форматує список цілей з деревом вкладеності."""
    if not goals:
        return f"{title}\n\n{t('goals_empty', lang)}"
    
    lines = [title, ""]
    
    # Будуємо дерево: id -> children
    children_map = {}
    for goal in goals:
        parent_id = goal.get('parent_id')
        if parent_id:
            if parent_id not in children_map:
                children_map[parent_id] = []
            children_map[parent_id].append(goal)
    
    # Топ-рівень: проекти та таргети без parent
    top_level = [g for g in goals if g['goal_type'] in ('project', 'target') and not g.get('parent_id')]
    
    # Звички без parent
    orphan_habits = [g for g in goals if g['goal_type'] == 'habit' and not g.get('parent_id')]
    
    def format_goal_line(goal: dict, indent: int = 0) -> list:
        """Форматує одну ціль та її дітей рекурсивно."""
        result = []
        prefix = "  " * indent
        
        emoji = GOAL_TYPE_EMOJI.get(GoalType(goal['goal_type']), "🎯")
        status = "✅" if goal.get('status') == 'completed' else "⬜"
        
        if goal['goal_type'] == 'habit':
            streak = goal.get('current_streak', 0)
            extra = f" 🔥{streak}" if streak > 0 else ""
        else:
            progress = goal.get('progress', 0)
            extra = f" [{progress}%]" if progress > 0 else ""
        
        result.append(f"{prefix}{status}{emoji} {goal['title']}{extra}")
        
        # Додаємо дітей
        if goal['id'] in children_map:
            for child in children_map[goal['id']]:
                result.extend(format_goal_line(child, indent + 1))
        
        return result
    
    # Проєкти з деревом
    if top_level:
        lines.append(f"📋 <b>{t('goal_type_project', lang)}</b>:")
        for goal in top_level:
            lines.extend(format_goal_line(goal, 1))
        lines.append("")
    
    # Звички без прив'язки
    if orphan_habits:
        lines.append(f"✅ <b>{t('goal_type_habit', lang)}</b>:")
        for habit in orphan_habits:
            streak = habit.get('current_streak', 0)
            extra = f" 🔥{streak}" if streak > 0 else ""
            lines.append(f"  ⬜ {habit['title']}{extra}")
        lines.append("")
    
    stats = {
        'active': sum(1 for g in goals if g.get('status') == 'active'),
        'completed': sum(1 for g in goals if g.get('status') == 'completed')
    }
    lines.append(f"📊 {t('goals_stats', lang, active=stats['active'], completed=stats['completed'])}")
    
    return "\n".join(lines)


def calculate_deadline(option: str) -> str | None:
    """Обчислює дату дедлайну."""
    today = date.today()
    
    if option == "end_week":
        days_until_sunday = 6 - today.weekday()
        return (today + timedelta(days=days_until_sunday)).isoformat()
    elif option == "end_month":
        if today.month == 12:
            return date(today.year + 1, 1, 1).isoformat()
        return (date(today.year, today.month + 1, 1) - timedelta(days=1)).isoformat()
    elif option == "end_quarter":
        quarter = (today.month - 1) // 3 + 1
        if quarter == 4:
            return date(today.year, 12, 31).isoformat()
        return (date(today.year, quarter * 3 + 1, 1) - timedelta(days=1)).isoformat()
    elif option == "end_year":
        return date(today.year, 12, 31).isoformat()
    return None


def detect_goal_type(text: str) -> GoalType | None:
    """Визначає тип цілі за ключовими словами."""
    text_lower = text.lower()
    
    habit_keywords = ['щодня', 'щотижня', 'регулярно', 'кожен день', 'разів на тиждень', 'daily', 'weekly']
    target_keywords = ['прочитати', 'накопичити', 'досягти', 'книг', 'км', 'кг', 'за рік', 'до кінця']
    metric_keywords = ['тримати', 'контролювати', 'відстежувати', 'вага', 'моніторити']
    project_keywords = ['вивчити', 'запустити', 'створити', 'зробити', 'побудувати', 'проєкт']
    task_keywords = ['купити', 'записатись', 'подзвонити', 'надіслати', 'зробити']
    
    if any(kw in text_lower for kw in habit_keywords):
        return GoalType.habit
    if any(kw in text_lower for kw in target_keywords):
        return GoalType.target
    if any(kw in text_lower for kw in metric_keywords):
        return GoalType.metric
    if any(kw in text_lower for kw in project_keywords):
        return GoalType.project
    if any(kw in text_lower for kw in task_keywords):
        return GoalType.task
    
    return None


# ============== COMMANDS ==============

@router.message(Command("goals"))
async def cmd_goals(message: Message) -> None:
    """Показати список цілей."""
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    goals = await gq.get_all_goals(user_id, status='active')
    
    text = format_goals_list(goals, t("goals_active_title", lang), lang)
    await message.answer(text, reply_markup=get_goals_list_keyboard(goals, lang, "active"))


@router.message(F.text.in_(["🎯 Цілі", "🎯 Goals"]))
async def btn_goals(message: Message) -> None:
    await cmd_goals(message)


@router.message(Command("habits"))
async def cmd_habits(message: Message) -> None:
    """Звички на сьогодні."""
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    habits = await gq.get_habits_today(user_id)
    
    today_str = date.today().strftime("%d.%m.%Y")
    
    if not habits:
        text = f"✅ <b>{t('habits_title', lang)}</b> ({today_str})\n\n{t('habits_empty', lang)}"
    else:
        done = sum(1 for h in habits if h.get('today_status') == 'done')
        text = f"✅ <b>{t('habits_title', lang)}</b> ({today_str})\n\n"
        text += f"{t('habits_progress', lang, done=done, total=len(habits), percent=int(done/len(habits)*100) if habits else 0)}"
    
    await message.answer(text, reply_markup=get_habits_today_keyboard(habits, lang))


@router.message(F.text.in_(["✅ Звички", "✅ Habits"]))
async def btn_habits(message: Message) -> None:
    await cmd_habits(message)


# ============== FILTERS ==============

@router.callback_query(F.data.startswith("goals_f:"))
async def filter_goals(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    filter_type = callback.data.split(":")[1]
    
    if filter_type == "active":
        goals = await gq.get_all_goals(user_id, status='active')
        title = t("goals_active_title", lang)
    elif filter_type == "completed":
        goals = await gq.get_all_goals(user_id, status='completed')
        title = t("goals_completed_title", lang)
    else:
        goals = await gq.get_all_goals(user_id)
        title = t("goals_all_title", lang)
    
    text = format_goals_list(goals, title, lang)
    await callback.message.edit_text(text, reply_markup=get_goals_list_keyboard(goals, lang, filter_type))
    await callback.answer()


# ============== GOAL CREATION ==============

@router.message(Command("goal_add"))
async def start_goal_creation(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    await state.set_state(GoalCreation.title)
    await state.update_data(lang=lang)
    await message.answer(t("goal_add_title", lang), reply_markup=get_cancel_keyboard(lang))


@router.callback_query(F.data == "goal:add")
async def start_goal_creation_cb(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    await state.set_state(GoalCreation.title)
    await state.update_data(lang=lang)
    await callback.message.answer(t("goal_add_title", lang), reply_markup=get_cancel_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data == "habit:add")
async def start_habit_creation(callback: CallbackQuery, state: FSMContext) -> None:
    """Швидке створення звички."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    await state.set_state(GoalCreation.title)
    await state.update_data(lang=lang, preset_type='habit')
    await callback.message.answer(t("habit_add_title", lang), reply_markup=get_cancel_keyboard(lang))
    await callback.answer()


# --- Step 1: Title ---
@router.message(GoalCreation.title)
async def process_title(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    
    if message.text in ["❌ Скасувати", "❌ Cancel"]:
        await state.clear()
        await message.answer(t("cancelled", lang), reply_markup=get_main_reply_keyboard(lang))
        return
    
    title = message.text
    await state.update_data(title=title)
    
    # Якщо вже є preset_type (наприклад, для звички)
    if data.get('preset_type'):
        await state.update_data(goal_type=data['preset_type'])
        if data['preset_type'] == 'habit':
            await state.set_state(GoalCreation.frequency)
            await message.answer(t("goal_add_frequency", lang), reply_markup=get_frequency_keyboard(lang))
            return
    
    # Намагаємось автовизначити тип
    detected = detect_goal_type(title)
    
    if detected:
        await state.update_data(suggested_type=detected.value)
        await message.answer(
            t("goal_type_detected", lang, type_name=t(f"goal_type_{detected.value}", lang)),
        )
    
    await state.set_state(GoalCreation.goal_type)
    await message.answer(t("goal_add_type", lang), reply_markup=get_goal_type_keyboard(lang))


# --- Step 2: Type ---
@router.callback_query(GoalCreation.goal_type, GoalTypeCallback.filter())
async def process_type(callback: CallbackQuery, callback_data: GoalTypeCallback, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    goal_type = callback_data.goal_type.value
    
    await state.update_data(goal_type=goal_type)
    
    if goal_type == 'habit':
        await state.set_state(GoalCreation.frequency)
        await callback.message.edit_text(t("goal_add_frequency", lang), reply_markup=get_frequency_keyboard(lang))
    elif goal_type == 'target':
        await state.set_state(GoalCreation.target_value)
        await callback.message.edit_text(t("goal_add_target_value", lang))
    elif goal_type == 'metric':
        await state.set_state(GoalCreation.target_range)
        await callback.message.edit_text(t("goal_add_metric_range", lang))
    else:
        # project, task — переходимо до батьківської цілі
        await _ask_parent(callback.message, state, lang)
    
    await callback.answer()


# --- Step 3a: Frequency (Habit) ---
@router.callback_query(GoalCreation.frequency, FrequencyCallback.filter())
async def process_frequency(callback: CallbackQuery, callback_data: FrequencyCallback, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    freq = callback_data.frequency
    
    schedule_days = None
    if freq == "daily":
        schedule_days = "1,2,3,4,5,6,7"
    elif freq == "weekdays":
        schedule_days = "1,2,3,4,5"
        freq = "daily"
    elif freq == "3_per_week":
        schedule_days = "1,3,5"
    
    await state.update_data(frequency=freq, schedule_days=schedule_days)
    
    if freq == "custom":
        await callback.message.edit_text(t("goal_add_schedule_days", lang))
        await state.set_state(GoalCreation.schedule_days)
    else:
        # Для звичок питаємо час і тривалість
        await state.set_state(GoalCreation.reminder_time)
        await callback.message.edit_text(t("goal_add_reminder_time", lang))
    
    await callback.answer()


# --- Step 3a.1: Custom days ---
@router.message(GoalCreation.schedule_days)
async def process_schedule_days(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    
    days = parse_schedule_days(message.text)
    if not days:
        await message.answer(t("error_invalid_days", lang))
        return
    
    await state.update_data(schedule_days=days)
    await state.set_state(GoalCreation.reminder_time)
    await message.answer(t("goal_add_reminder_time", lang))


def parse_schedule_days(text: str) -> str | None:
    """Парсить дні тижня: 1,3,5 або Пн,Ср,Пт або Mon,Wed,Fri."""
    text = text.strip().lower()
    
    # Числовий формат: 1,3,5
    if all(c.isdigit() or c in ',. ' for c in text):
        nums = [int(n) for n in text.replace('.', ',').replace(' ', ',').split(',') if n.isdigit()]
        if all(1 <= n <= 7 for n in nums):
            return ','.join(str(n) for n in sorted(set(nums)))
    
    # Українські назви
    ua_days = {'пн': 1, 'вт': 2, 'ср': 3, 'чт': 4, 'пт': 5, 'сб': 6, 'нд': 7,
               'понеділок': 1, 'вівторок': 2, 'середа': 3, 'четвер': 4, 
               'п\'ятниця': 5, 'субота': 6, 'неділя': 7}
    
    # Англійські назви
    en_days = {'mon': 1, 'tue': 2, 'wed': 3, 'thu': 4, 'fri': 5, 'sat': 6, 'sun': 7,
               'monday': 1, 'tuesday': 2, 'wednesday': 3, 'thursday': 4,
               'friday': 5, 'saturday': 6, 'sunday': 7}
    
    all_days = {**ua_days, **en_days}
    
    # Розбиваємо по комах, пробілах
    import re
    parts = re.split(r'[,\s]+', text)
    nums = []
    for part in parts:
        if part in all_days:
            nums.append(all_days[part])
    
    if nums:
        return ','.join(str(n) for n in sorted(set(nums)))
    
    return None


# --- Step 3a.2: Reminder time ---
@router.message(GoalCreation.reminder_time)
async def process_reminder_time(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    
    text = message.text.strip().lower()
    
    # Пропустити
    if text in ['skip', 'пропустити', '-', '']:
        await state.update_data(reminder_time=None)
    else:
        from bot.handlers.tasks import parse_time
        parsed = parse_time(message.text)
        if not parsed:
            await message.answer(t("error_invalid_time", lang))
            return
        hour, minute = parsed
        await state.update_data(reminder_time=f"{hour:02d}:{minute:02d}")
    
    # Питаємо тривалість
    await state.set_state(GoalCreation.duration)
    await message.answer(t("goal_add_duration", lang), reply_markup=get_skip_cancel_keyboard(lang))


# --- Step 3a.3: Duration ---
@router.message(GoalCreation.duration)
async def process_duration(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    
    text = message.text.strip().lower()
    
    # Пропуск
    if text in ['skip', 'пропустити', '-', '⏭ пропустити', '⏭ skip']:
        await state.update_data(duration_minutes=None)
        await _ask_parent(message, state, lang, is_callback=False)
        return
    
    # Скасування
    if text in ['❌ скасувати', '❌ cancel']:
        await state.clear()
        await message.answer(t("cancelled", lang), reply_markup=get_main_reply_keyboard(lang))
        return
    
    # Парсимо тривалість: "30", "30 хв", "1 година", "1h"
    import re
    
    # Варіант 1: просто число (хвилини)
    if text.isdigit():
        await state.update_data(duration_minutes=int(text))
        await _ask_parent(message, state, lang, is_callback=False)
        return
    
    # Варіант 2: число + одиниця
    match = re.match(r'^(\d+)\s*(хв|хвилин|min|м|h|год|година)?', text)
    if match:
        value = int(match.group(1))
        unit = match.group(2) or ''
        
        if unit in ['h', 'год', 'година']:
            value *= 60
        
        await state.update_data(duration_minutes=value)
        await _ask_parent(message, state, lang, is_callback=False)
        return
    
    await message.answer(t("error_invalid_duration", lang))


# --- Step 3b: Target Value ---
@router.message(GoalCreation.target_value)
async def process_target_value(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    
    # Парсимо: "24 книги" або "100"
    text = message.text.strip()
    parts = text.split(maxsplit=1)
    
    try:
        value = float(parts[0].replace(",", "."))
        unit = parts[1] if len(parts) > 1 else ""
    except ValueError:
        await message.answer(t("error_invalid_number", lang))
        return
    
    await state.update_data(target_value=value, unit=unit)
    await _ask_parent(message, state, lang, is_callback=False)


# --- Step 3c: Metric Range ---
@router.message(GoalCreation.target_range)
async def process_metric_range(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    
    # Парсимо: "75-78 кг" або "75 78"
    text = message.text.strip()
    
    import re
    match = re.match(r'(\d+(?:[.,]\d+)?)\s*[-–]\s*(\d+(?:[.,]\d+)?)\s*(.*)', text)
    
    if match:
        target_min = float(match.group(1).replace(",", "."))
        target_max = float(match.group(2).replace(",", "."))
        unit = match.group(3).strip()
    else:
        parts = text.split()
        if len(parts) >= 2:
            try:
                target_min = float(parts[0].replace(",", "."))
                target_max = float(parts[1].replace(",", "."))
                unit = " ".join(parts[2:]) if len(parts) > 2 else ""
            except ValueError:
                await message.answer(t("error_invalid_range", lang))
                return
        else:
            await message.answer(t("error_invalid_range", lang))
            return
    
    await state.update_data(target_min=target_min, target_max=target_max, unit=unit)
    await _ask_parent(message, state, lang, is_callback=False)


async def _ask_parent(message, state: FSMContext, lang: str, is_callback: bool = True) -> None:
    """Питає про батьківську ціль."""
    user_id = message.chat.id
    projects = await gq.get_projects(user_id)
    
    if projects:
        await state.set_state(GoalCreation.parent)
        text = t("goal_add_parent", lang)
        kb = get_parent_keyboard(projects, lang)
        if is_callback:
            await message.edit_text(text, reply_markup=kb)
        else:
            await message.answer(text, reply_markup=kb)
    else:
        await state.update_data(parent_id=None)
        await _ask_deadline(message, state, lang, is_callback)


# --- Step 4: Parent ---
@router.callback_query(GoalCreation.parent, GoalParentCallback.filter())
async def process_parent(callback: CallbackQuery, callback_data: GoalParentCallback, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    
    parent_id = callback_data.parent_id if callback_data.parent_id > 0 else None
    await state.update_data(parent_id=parent_id)
    
    await _ask_deadline(callback.message, state, lang)
    await callback.answer()


async def _ask_deadline(message, state: FSMContext, lang: str, is_callback: bool = True) -> None:
    """Питає про дедлайн."""
    data = await state.get_data()
    
    # Для звичок і метрик дедлайн не потрібен
    if data.get('goal_type') in ('habit', 'metric'):
        await _finish_creation(message, state, lang, deadline=None, is_callback=is_callback)
        return
    
    await state.set_state(GoalCreation.deadline)
    text = t("goal_add_deadline", lang)
    kb = get_deadline_keyboard(lang)
    
    if is_callback:
        await message.edit_text(text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


# --- Step 5: Deadline ---
@router.callback_query(GoalCreation.deadline, F.data.startswith("goal_ddl:"))
async def process_deadline(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    option = callback.data.split(":")[1]
    
    if option == "custom":
        await callback.message.edit_text(t("goal_add_deadline_custom", lang))
        return
    
    deadline = calculate_deadline(option)
    await _finish_creation(callback.message, state, lang, deadline)
    await callback.answer()


@router.message(GoalCreation.deadline)
async def process_deadline_custom(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    
    from bot.handlers.tasks import parse_date
    parsed = parse_date(message.text)
    
    if not parsed:
        await message.answer(t("error_invalid_date", lang))
        return
    
    await _finish_creation(message, state, lang, parsed.isoformat(), is_callback=False)


async def _finish_creation(message, state: FSMContext, lang: str, deadline: str = None, is_callback: bool = True) -> None:
    """Завершує створення цілі."""
    data = await state.get_data()
    user_id = message.chat.id
    
    goal_id = await gq.create_goal(
        user_id=user_id,
        title=data['title'],
        goal_type=data['goal_type'],
        parent_id=data.get('parent_id'),
        deadline=deadline,
        frequency=data.get('frequency'),
        schedule_days=data.get('schedule_days'),
        reminder_time=data.get('reminder_time'),
        duration_minutes=data.get('duration_minutes'),
        target_value=data.get('target_value'),
        unit=data.get('unit'),
        target_min=data.get('target_min'),
        target_max=data.get('target_max'),
    )
    
    await state.clear()
    
    goal = await gq.get_goal_by_id(goal_id, user_id)
    text = t("goal_created", lang, goal_id=goal_id) + "\n\n" + format_goal(goal, lang)
    
    if is_callback:
        await message.edit_text(text, reply_markup=get_goal_actions_keyboard(goal, lang))
    else:
        await message.answer(text, reply_markup=get_goal_actions_keyboard(goal, lang))
    
    # Повертаємо reply клавіатуру
    await message.answer("👇", reply_markup=get_main_reply_keyboard(lang))


# ============== GOAL ACTIONS ==============

@router.callback_query(GoalCallback.filter(F.action == GoalAction.view))
async def view_goal(callback: CallbackQuery, callback_data: GoalCallback) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    goal = await gq.get_goal_by_id(callback_data.goal_id, user_id)
    
    if not goal:
        await callback.answer(t("goal_not_found", lang), show_alert=True)
        return
    
    await callback.message.edit_text(
        format_goal(goal, lang),
        reply_markup=get_goal_actions_keyboard(goal, lang)
    )
    await callback.answer()


@router.callback_query(GoalCallback.filter(F.action == GoalAction.complete))
async def complete_goal(callback: CallbackQuery, callback_data: GoalCallback) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    
    success = await gq.complete_goal(callback_data.goal_id, user_id)
    
    if success:
        await callback.answer(t("goal_completed", lang), show_alert=True)
        goal = await gq.get_goal_by_id(callback_data.goal_id, user_id)
        await callback.message.edit_text(
            format_goal(goal, lang),
            reply_markup=get_goal_actions_keyboard(goal, lang)
        )
    else:
        await callback.answer(t("error_general", lang), show_alert=True)


@router.callback_query(GoalCallback.filter(F.action == GoalAction.restore))
async def restore_goal(callback: CallbackQuery, callback_data: GoalCallback) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    
    success = await gq.restore_goal(callback_data.goal_id, user_id)
    
    if success:
        await callback.answer(t("goal_restored", lang), show_alert=True)
        goal = await gq.get_goal_by_id(callback_data.goal_id, user_id)
        await callback.message.edit_text(
            format_goal(goal, lang),
            reply_markup=get_goal_actions_keyboard(goal, lang)
        )
    else:
        await callback.answer(t("error_general", lang), show_alert=True)


@router.callback_query(GoalCallback.filter(F.action == GoalAction.progress))
async def view_progress(callback: CallbackQuery, callback_data: GoalCallback) -> None:
    """Показати прогрес проєкту з деревом підцілей."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    goal_id = callback_data.goal_id
    
    goal = await gq.get_goal_by_id(goal_id, user_id)
    if not goal:
        await callback.answer(t("goal_not_found", lang), show_alert=True)
        return
    
    # Отримуємо підцілі
    children = await gq.get_child_goals(goal_id, user_id)
    
    # Перераховуємо прогрес
    if goal['goal_type'] == 'project':
        progress = await gq.recalculate_project_progress(goal_id, user_id)
        goal['progress'] = progress
    
    # Формуємо дерево
    lines = [f"📊 <b>{t('progress', lang)}: {goal['title']}</b>", ""]
    
    emoji = GOAL_TYPE_EMOJI.get(GoalType(goal['goal_type']), "🎯")
    bar = get_progress_bar(goal.get('progress', 0))
    lines.append(f"{emoji} {goal['title']} — {bar} {goal.get('progress', 0)}%")
    
    if children:
        lines.append("")
        lines.append(f"📋 <b>{t('subgoals', lang)}:</b>")
        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            prefix = "└── " if is_last else "├── "
            
            child_emoji = GOAL_TYPE_EMOJI.get(GoalType(child['goal_type']), "🎯")
            
            if child['goal_type'] == 'habit':
                streak = child.get('current_streak', 0)
                info = f"🔥{streak}"
            elif child.get('status') == 'completed':
                info = "✅"
            else:
                info = f"{child.get('progress', 0)}%"
            
            lines.append(f"  {prefix}{child_emoji} {child['title']} — {info}")
    else:
        lines.append("")
        lines.append(f"📭 {t('no_subgoals', lang)}")
        lines.append(f"💡 {t('hint_add_subgoal', lang)}")
    
    # Кнопка "Додати підціль"
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"➕ {t('add_subgoal', lang)}", callback_data=f"subgoal:add:{goal_id}")],
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data=GoalCallback(action=GoalAction.view, goal_id=goal_id).pack())]
    ])
    
    await callback.message.edit_text("\n".join(lines), reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("subgoal:add:"))
async def start_subgoal_creation(callback: CallbackQuery, state: FSMContext) -> None:
    """Почати створення підцілі."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    parent_id = int(callback.data.split(":")[2])
    
    await state.set_state(GoalCreation.title)
    await state.update_data(lang=lang, parent_id=parent_id)
    await callback.message.answer(t("goal_add_subgoal_title", lang), reply_markup=get_cancel_keyboard(lang))
    await callback.answer()


@router.callback_query(GoalCallback.filter(F.action == GoalAction.delete))
async def delete_goal_confirm(callback: CallbackQuery, callback_data: GoalCallback) -> None:
    lang = get_user_lang(callback.from_user.id)
    await callback.message.edit_text(
        t("goal_delete_confirm", lang),
        reply_markup=get_confirm_keyboard(callback_data.goal_id, "delete", lang)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("goal_confirm:delete:"))
async def delete_goal_execute(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    goal_id = int(callback.data.split(":")[2])
    
    success = await gq.delete_goal(goal_id, user_id)
    
    if success:
        await callback.answer(t("goal_deleted", lang), show_alert=True)
        goals = await gq.get_all_goals(user_id, status='active')
        text = format_goals_list(goals, t("goals_active_title", lang), lang)
        await callback.message.edit_text(text, reply_markup=get_goals_list_keyboard(goals, lang))
    else:
        await callback.answer(t("error_general", lang), show_alert=True)


# ============== HABIT LOG ==============

@router.callback_query(GoalCallback.filter(F.action == GoalAction.log))
async def log_habit_done(callback: CallbackQuery, callback_data: GoalCallback) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    
    await gq.log_habit(callback_data.goal_id, user_id, 'done')
    
    goal = await gq.get_goal_by_id(callback_data.goal_id, user_id)
    streak = goal.get('current_streak', 0)
    
    await callback.answer(t("habit_done", lang, streak=streak), show_alert=True)
    await callback.message.edit_text(
        format_goal(goal, lang),
        reply_markup=get_goal_actions_keyboard(goal, lang)
    )


@router.callback_query(F.data.startswith("habit_skip:"))
async def log_habit_skip(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    goal_id = int(callback.data.split(":")[1])
    
    await gq.log_habit(goal_id, user_id, 'skipped')
    
    goal = await gq.get_goal_by_id(goal_id, user_id)
    await callback.answer(t("habit_skipped", lang), show_alert=True)
    await callback.message.edit_text(
        format_goal(goal, lang),
        reply_markup=get_goal_actions_keyboard(goal, lang)
    )


# ============== TARGET/METRIC ENTRY ==============

@router.callback_query(GoalCallback.filter(F.action == GoalAction.entry))
async def start_entry(callback: CallbackQuery, callback_data: GoalCallback, state: FSMContext) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    
    goal = await gq.get_goal_by_id(callback_data.goal_id, user_id)
    unit = goal.get('unit', '')
    
    await state.set_state(GoalEntry.value)
    await state.update_data(entry_goal_id=callback_data.goal_id, lang=lang, unit=unit)
    
    await callback.message.edit_text(t("goal_add_entry", lang, unit=unit))
    await callback.answer()


@router.message(GoalEntry.value)
async def process_entry(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    goal_id = data.get("entry_goal_id")
    user_id = message.from_user.id
    
    try:
        value = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer(t("error_invalid_number", lang))
        return
    
    await gq.add_goal_entry(goal_id, user_id, value)
    await state.clear()
    
    goal = await gq.get_goal_by_id(goal_id, user_id)
    await message.answer(
        t("entry_added", lang) + "\n\n" + format_goal(goal, lang),
        reply_markup=get_goal_actions_keyboard(goal, lang)
    )
    await message.answer("👇", reply_markup=get_main_reply_keyboard(lang))


# ============== EDIT ==============

@router.callback_query(GoalCallback.filter(F.action == GoalAction.edit))
async def edit_goal_menu(callback: CallbackQuery, callback_data: GoalCallback) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    goal = await gq.get_goal_by_id(callback_data.goal_id, user_id)
    
    if not goal:
        await callback.answer(t("goal_not_found", lang), show_alert=True)
        return
    
    await callback.message.edit_text(
        t("goal_edit_choose_field", lang, title=goal['title']),
        reply_markup=get_goal_edit_keyboard(goal['id'], goal['goal_type'], lang)
    )
    await callback.answer()


@router.callback_query(GoalEditCallback.filter())
async def edit_field_selected(callback: CallbackQuery, callback_data: GoalEditCallback, state: FSMContext) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    
    await state.update_data(edit_goal_id=callback_data.goal_id, edit_field=callback_data.field.value, lang=lang)
    await state.set_state(GoalEdit.waiting_value)
    
    prompt = t(f"goal_edit_{callback_data.field.value}", lang)
    await callback.message.edit_text(prompt)
    await callback.answer()


@router.message(GoalEdit.waiting_value)
async def process_edit_value(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    goal_id = data.get("edit_goal_id")
    field = data.get("edit_field")
    user_id = message.from_user.id
    
    update_data = {}
    
    if field == "title":
        update_data["title"] = message.text
    elif field == "description":
        update_data["description"] = message.text
    elif field == "deadline":
        from bot.handlers.tasks import parse_date
        parsed = parse_date(message.text)
        if not parsed:
            await message.answer(t("error_invalid_date", lang))
            return
        update_data["deadline"] = parsed.isoformat()
    elif field == "target_value":
        try:
            update_data["target_value"] = float(message.text.replace(",", "."))
        except ValueError:
            await message.answer(t("error_invalid_number", lang))
            return
    
    success = await gq.update_goal(goal_id, user_id, **update_data)
    await state.clear()
    
    if success:
        await message.answer(t("goal_updated", lang), reply_markup=get_main_reply_keyboard(lang))
        goal = await gq.get_goal_by_id(goal_id, user_id)
        await message.answer(format_goal(goal, lang), reply_markup=get_goal_actions_keyboard(goal, lang))
    else:
        await message.answer(t("error_general", lang), reply_markup=get_main_reply_keyboard(lang))


# ============== NAVIGATION ==============

@router.callback_query(F.data == "goals:back")
async def back_to_goals(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    goals = await gq.get_all_goals(user_id, status='active')
    
    text = format_goals_list(goals, t("goals_active_title", lang), lang)
    await callback.message.edit_text(text, reply_markup=get_goals_list_keyboard(goals, lang))
    await callback.answer()


# ============== CANCEL ==============

@router.message(F.text.in_(["❌ Скасувати", "❌ Cancel"]))
async def cancel_goal_fsm(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    lang = get_user_lang(message.from_user.id)
    
    if current and current.startswith("GoalCreation") or current and current.startswith("GoalEdit") or current and current.startswith("GoalEntry"):
        await state.clear()
        await message.answer(t("cancelled", lang), reply_markup=get_main_reply_keyboard(lang))
