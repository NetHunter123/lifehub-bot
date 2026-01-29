"""
Обробники для /today dashboard та time blocks.
"""

from datetime import datetime, date, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.reply import get_main_reply_keyboard, get_cancel_keyboard
from bot.locales import t, get_user_lang
from bot.database import today_queries as tq
from bot.database import goal_queries as gq

router = Router()


# ============== FSM ==============

class TimeBlockCreation(StatesGroup):
    title = State()
    start_time = State()
    end_time = State()
    days = State()


# ============== HELPERS ==============

def format_today_schedule(schedule: dict, lang: str) -> str:
    """Форматує розклад на сьогодні."""
    today = date.today()
    weekday_names = {
        1: 'Понеділок', 2: 'Вівторок', 3: 'Середа', 4: 'Четвер',
        5: "П'ятниця", 6: 'Субота', 7: 'Неділя'
    }
    weekday = weekday_names.get(today.isoweekday(), '')
    
    lines = [
        f"📅 <b>{t('today_title', lang)}</b>",
        f"{today.strftime('%d.%m.%Y')} • {weekday}",
        ""
    ]
    
    # Статистика
    total_habits = len(schedule['habits'])
    done_habits = sum(1 for h in schedule['habits'] if h.get('today_status') == 'done')
    total_tasks = len(schedule['tasks'])
    
    # Time blocks (пропущені показуємо окремо)
    active_blocks = [tb for tb in schedule['time_blocks'] if not tb['is_skipped']]
    skipped_blocks = [tb for tb in schedule['time_blocks'] if tb['is_skipped']]
    
    if active_blocks:
        lines.append(f"🏢 <b>{t('time_blocks', lang)}:</b>")
        for tb in active_blocks:
            lines.append(f"  {tb['start_time']}-{tb['end_time']} — {tb['title']}")
        lines.append("")
    
    if skipped_blocks:
        lines.append(f"⏭ <b>{t('skipped_today', lang)}:</b>")
        for tb in skipped_blocks:
            lines.append(f"  <s>{tb['title']}</s>")
        lines.append("")
    
    # Timeline (задачі та звички з часом)
    timed_items = [item for item in schedule['timeline'] if item['type'] in ('task', 'habit')]
    if timed_items:
        lines.append(f"⏰ <b>{t('scheduled', lang)}:</b>")
        for item in timed_items:
            if item['type'] == 'task':
                fixed = "📌" if item.get('is_fixed') else ""
                priority_emoji = {0: '🔴', 1: '🟠', 2: '🟡', 3: '🟢'}.get(item.get('priority', 2), '🟡')
                goal_suffix = f" [{item['goal_title']}]" if item.get('goal_title') else ""
                lines.append(f"  {item['start_time']} {fixed}{priority_emoji} {item['title']}{goal_suffix}")
            elif item['type'] == 'habit':
                status = "✅" if item.get('today_status') == 'done' else "⬜"
                streak = f" 🔥{item['streak']}" if item.get('streak', 0) > 0 else ""
                duration = f" ({item['duration']}хв)" if item.get('duration') else ""
                lines.append(f"  {item['start_time']} {status} {item['title']}{streak}{duration}")
        lines.append("")
    
    # Задачі без часу
    untimed_tasks = [t for t in schedule['tasks'] if not t.get('scheduled_start')]
    if untimed_tasks:
        lines.append(f"📋 <b>{t('tasks', lang)}:</b>")
        for task in untimed_tasks[:10]:  # Max 10
            priority_emoji = {0: '🔴', 1: '🟠', 2: '🟡', 3: '🟢'}.get(task.get('priority', 2), '🟡')
            goal_suffix = f" [{task['goal_title']}]" if task.get('goal_title') else ""
            lines.append(f"  {priority_emoji} {task['title']}{goal_suffix}")
        lines.append("")
    
    # Звички без часу
    untimed_habits = [h for h in schedule['habits'] if not h.get('reminder_time')]
    if untimed_habits:
        lines.append(f"✅ <b>{t('habits', lang)}:</b>")
        for habit in untimed_habits:
            status = "✅" if habit.get('today_status') == 'done' else "⬜"
            streak = f" 🔥{habit.get('current_streak', 0)}" if habit.get('current_streak', 0) > 0 else ""
            lines.append(f"  {status} {habit['title']}{streak}")
        lines.append("")
    
    # Підсумок
    lines.append("━" * 25)
    lines.append(f"✅ {t('habits', lang)}: {done_habits}/{total_habits} | 📋 {t('tasks', lang)}: {total_tasks}")
    
    return "\n".join(lines)


def get_today_keyboard(schedule: dict, lang: str) -> InlineKeyboardMarkup:
    """Клавіатура для /today."""
    builder = InlineKeyboardBuilder()
    
    # Кнопки для time blocks (skip/unskip)
    for tb in schedule['time_blocks']:
        if tb['is_skippable']:
            if tb['is_skipped']:
                builder.row(InlineKeyboardButton(
                    text=f"↩️ {tb['title']}",
                    callback_data=f"tb_unskip:{tb['id']}"
                ))
            else:
                builder.row(InlineKeyboardButton(
                    text=f"⏭ {t('skip', lang)} {tb['title']}",
                    callback_data=f"tb_skip:{tb['id']}"
                ))
    
    # Дії
    builder.row(
        InlineKeyboardButton(text=f"➕ {t('btn_add_task', lang)}", callback_data="task:add"),
        InlineKeyboardButton(text=f"✅ {t('habits', lang)}", callback_data="habits:today")
    )
    builder.row(
        InlineKeyboardButton(text=f"🏢 {t('manage_blocks', lang)}", callback_data="blocks:manage"),
        InlineKeyboardButton(text="🔄", callback_data="today:refresh")
    )
    
    return builder.as_markup()


# ============== COMMANDS ==============

@router.message(Command("today"))
async def cmd_today(message: Message) -> None:
    """Показати розклад на сьогодні."""
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    
    schedule = await tq.get_today_schedule(user_id)
    text = format_today_schedule(schedule, lang)
    
    await message.answer(text, reply_markup=get_today_keyboard(schedule, lang))


@router.message(F.text.in_(["📅 Сьогодні", "📅 Today"]))
async def btn_today(message: Message) -> None:
    await cmd_today(message)


@router.callback_query(F.data == "today:refresh")
async def refresh_today(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    
    schedule = await tq.get_today_schedule(user_id)
    text = format_today_schedule(schedule, lang)
    
    await callback.message.edit_text(text, reply_markup=get_today_keyboard(schedule, lang))
    await callback.answer(t("refreshed", lang))


# ============== TIME BLOCK SKIP ==============

@router.callback_query(F.data.startswith("tb_skip:"))
async def skip_time_block(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    tb_id = int(callback.data.split(":")[1])
    
    await tq.skip_time_block(tb_id, user_id)
    
    # Перерозподіляємо гнучкі задачі
    rescheduled = await tq.reschedule_flexible_tasks(user_id)
    
    # Оновлюємо розклад
    schedule = await tq.get_today_schedule(user_id)
    text = format_today_schedule(schedule, lang)
    
    if rescheduled:
        text += f"\n\n🔄 {t('rescheduled', lang)}: {len(rescheduled)} {t('tasks', lang)}"
    
    await callback.message.edit_text(text, reply_markup=get_today_keyboard(schedule, lang))
    await callback.answer(t("skipped", lang))


@router.callback_query(F.data.startswith("tb_unskip:"))
async def unskip_time_block(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    tb_id = int(callback.data.split(":")[1])
    
    await tq.unskip_time_block(tb_id, user_id)
    
    schedule = await tq.get_today_schedule(user_id)
    text = format_today_schedule(schedule, lang)
    
    await callback.message.edit_text(text, reply_markup=get_today_keyboard(schedule, lang))
    await callback.answer(t("restored", lang))


# ============== TIME BLOCKS MANAGEMENT ==============

@router.callback_query(F.data == "blocks:manage")
async def manage_blocks(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    
    blocks = await tq.get_time_blocks(user_id)
    
    if not blocks:
        text = f"🏢 <b>{t('time_blocks', lang)}</b>\n\n{t('no_blocks', lang)}"
    else:
        text = f"🏢 <b>{t('time_blocks', lang)}</b>\n\n"
        for block in blocks:
            days = format_days(block['days'], lang)
            text += f"• {block['title']}\n  {block['start_time']}-{block['end_time']} ({days})\n"
    
    builder = InlineKeyboardBuilder()
    
    for block in blocks:
        builder.row(InlineKeyboardButton(
            text=f"🗑 {block['title']}",
            callback_data=f"block_delete:{block['id']}"
        ))
    
    builder.row(InlineKeyboardButton(text=f"➕ {t('add_block', lang)}", callback_data="block:add"))
    builder.row(InlineKeyboardButton(text=t("btn_back", lang), callback_data="today:refresh"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


def format_days(days_str: str, lang: str) -> str:
    """Форматує дні для відображення."""
    day_names = {
        'uk': {1: 'Пн', 2: 'Вт', 3: 'Ср', 4: 'Чт', 5: 'Пт', 6: 'Сб', 7: 'Нд'},
        'en': {1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu', 5: 'Fri', 6: 'Sat', 7: 'Sun'}
    }
    names = day_names.get(lang, day_names['uk'])
    days = [int(d) for d in days_str.split(',') if d.strip().isdigit()]
    return ', '.join(names.get(d, str(d)) for d in days)


# ============== CREATE TIME BLOCK ==============

@router.callback_query(F.data == "block:add")
async def start_block_creation(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    
    await state.set_state(TimeBlockCreation.title)
    await state.update_data(lang=lang)
    await callback.message.answer(t("block_add_title", lang), reply_markup=get_cancel_keyboard(lang))
    await callback.answer()


@router.message(TimeBlockCreation.title)
async def process_block_title(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    
    if message.text in ["❌ Скасувати", "❌ Cancel"]:
        await state.clear()
        await message.answer(t("cancelled", lang), reply_markup=get_main_reply_keyboard(lang))
        return
    
    await state.update_data(title=message.text)
    await state.set_state(TimeBlockCreation.start_time)
    await message.answer(t("block_add_start", lang))


@router.message(TimeBlockCreation.start_time)
async def process_block_start(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    
    # Парсимо час
    import re
    match = re.match(r'^(\d{1,2})[:\.]?(\d{2})?$', message.text.strip())
    if not match:
        await message.answer(t("error_invalid_time", lang))
        return
    
    hour = int(match.group(1))
    minute = int(match.group(2)) if match.group(2) else 0
    
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        await message.answer(t("error_invalid_time", lang))
        return
    
    start_time = f"{hour:02d}:{minute:02d}"
    await state.update_data(start_time=start_time)
    await state.set_state(TimeBlockCreation.end_time)
    await message.answer(t("block_add_end", lang))


@router.message(TimeBlockCreation.end_time)
async def process_block_end(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    
    import re
    match = re.match(r'^(\d{1,2})[:\.]?(\d{2})?$', message.text.strip())
    if not match:
        await message.answer(t("error_invalid_time", lang))
        return
    
    hour = int(match.group(1))
    minute = int(match.group(2)) if match.group(2) else 0
    
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        await message.answer(t("error_invalid_time", lang))
        return
    
    end_time = f"{hour:02d}:{minute:02d}"
    await state.update_data(end_time=end_time)
    await state.set_state(TimeBlockCreation.days)
    await message.answer(t("block_add_days", lang))


@router.message(TimeBlockCreation.days)
async def process_block_days(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    user_id = message.from_user.id
    
    # Парсимо дні
    from bot.handlers.goals import parse_schedule_days
    days = parse_schedule_days(message.text)
    
    if not days:
        await message.answer(t("error_invalid_days", lang))
        return
    
    # Створюємо time block
    block_id = await tq.create_time_block(
        user_id=user_id,
        title=data['title'],
        start_time=data['start_time'],
        end_time=data['end_time'],
        days=days,
    )
    
    await state.clear()
    await message.answer(
        t("block_created", lang, title=data['title']),
        reply_markup=get_main_reply_keyboard(lang)
    )


@router.callback_query(F.data.startswith("block_delete:"))
async def delete_block(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    block_id = int(callback.data.split(":")[1])
    
    await tq.delete_time_block(block_id, user_id)
    
    # Оновлюємо список
    blocks = await tq.get_time_blocks(user_id)
    
    if not blocks:
        text = f"🏢 <b>{t('time_blocks', lang)}</b>\n\n{t('no_blocks', lang)}"
    else:
        text = f"🏢 <b>{t('time_blocks', lang)}</b>\n\n"
        for block in blocks:
            days = format_days(block['days'], lang)
            text += f"• {block['title']}\n  {block['start_time']}-{block['end_time']} ({days})\n"
    
    builder = InlineKeyboardBuilder()
    for block in blocks:
        builder.row(InlineKeyboardButton(text=f"🗑 {block['title']}", callback_data=f"block_delete:{block['id']}"))
    builder.row(InlineKeyboardButton(text=f"➕ {t('add_block', lang)}", callback_data="block:add"))
    builder.row(InlineKeyboardButton(text=t("btn_back", lang), callback_data="today:refresh"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer(t("deleted", lang))


# ============== HABITS TODAY (redirect) ==============

@router.callback_query(F.data == "habits:today")
async def habits_today_redirect(callback: CallbackQuery) -> None:
    """Перенаправлення на /habits."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    
    habits = await gq.get_habits_today(user_id)
    
    from bot.handlers.goals import get_habits_today_keyboard
    from bot.keyboards.goals import get_habits_today_keyboard
    
    today_str = date.today().strftime("%d.%m.%Y")
    
    if not habits:
        text = f"✅ <b>{t('habits_title', lang)}</b> ({today_str})\n\n{t('habits_empty', lang)}"
    else:
        done = sum(1 for h in habits if h.get('today_status') == 'done')
        text = f"✅ <b>{t('habits_title', lang)}</b> ({today_str})\n\n"
        text += t('habits_progress', lang, done=done, total=len(habits), percent=int(done/len(habits)*100) if habits else 0)
    
    await callback.message.edit_text(text, reply_markup=get_habits_today_keyboard(habits, lang))
    await callback.answer()
