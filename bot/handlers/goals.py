"""
Обробники цілей (project, target, metric).
LifeHub Bot v4.0

ВАЖЛИВО: Habits — окремий файл handlers/habits.py
"""

from datetime import date, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.database import queries
from bot.states.states import GoalCreation, GoalEntry
from bot.keyboards import goals as kb
from bot.keyboards.reply import get_main_menu, get_cancel_keyboard, get_skip_cancel_keyboard
from bot.locales import uk


router = Router()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                              КОМАНДИ                                         ║
# ╚════════════════════════════════════════════════════════════════════════════╝

@router.message(Command("goals"))
async def cmd_goals(message: Message):
    """Показати всі цілі та проєкти."""
    user_id = message.from_user.id
    goals = await queries.get_all_goals(user_id, status='active')
    
    # Фільтруємо тільки project, target, metric (habits окремо)
    goals = [g for g in goals if g['goal_type'] in ('project', 'target', 'metric')]
    
    if not goals:
        text = f"{uk.GOALS['title_all']}\n\n{uk.GOALS['empty']}"
        await message.answer(text, parse_mode="HTML")
        return
    
    text = uk.GOALS['title_all'] + "\n\n"
    
    # Групуємо по типу
    projects = [g for g in goals if g['goal_type'] == 'project']
    targets = [g for g in goals if g['goal_type'] == 'target']
    metrics = [g for g in goals if g['goal_type'] == 'metric']
    
    if projects:
        text += "<b>📁 Проєкти:</b>\n"
        for p in projects:
            progress = p.get('progress', 0)
            bar = _progress_bar(progress)
            text += f"  • {p['title']} {bar} {progress}%\n"
        text += "\n"
    
    if targets:
        text += "<b>🎯 Цілі (Targets):</b>\n"
        for t in targets:
            current = t.get('current_value', 0)
            target = t.get('target_value', 1)
            unit = t.get('unit', '')
            progress = t.get('progress', 0)
            bar = _progress_bar(progress)
            text += f"  • {t['title']} ({current}/{target} {unit}) {bar}\n"
        text += "\n"
    
    if metrics:
        text += "<b>📊 Метрики:</b>\n"
        for m in metrics:
            text += f"  • {m['title']}\n"
    
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=kb.get_goals_list(goals)
    )


def _progress_bar(progress: int, length: int = 10) -> str:
    """Генерує текстовий прогрес-бар."""
    filled = int(progress / 100 * length)
    empty = length - filled
    return f"[{'█' * filled}{'░' * empty}]"


@router.message(Command("goal_add"))
async def cmd_goal_add(message: Message, state: FSMContext):
    """Почати створення цілі."""
    await state.clear()
    await state.set_state(GoalCreation.title)
    
    await message.answer(
        uk.GOALS['create_title'],
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                         ДІАЛОГ СТВОРЕННЯ                                     ║
# ╚════════════════════════════════════════════════════════════════════════════╝

@router.message(GoalCreation.title)
async def goal_title(message: Message, state: FSMContext):
    """Отримуємо назву цілі."""
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer(uk.CANCELLED, reply_markup=get_main_menu())
        return
    
    await state.update_data(title=message.text)
    await state.set_state(GoalCreation.goal_type)
    
    await message.answer(
        uk.GOALS['create_type'],
        reply_markup=kb.get_goal_type_keyboard()
    )


@router.callback_query(GoalCreation.goal_type, F.data.startswith("goal:type:"))
async def goal_type(callback: CallbackQuery, state: FSMContext):
    """Отримуємо тип цілі."""
    goal_type = callback.data.replace("goal:type:", "")
    await state.update_data(goal_type=goal_type)
    
    await state.set_state(GoalCreation.description)
    await callback.message.edit_text(
        uk.GOALS['create_description'],
        parse_mode="HTML"
    )
    
    # Показуємо reply клавіатуру
    await callback.message.answer(
        "⬇️",
        reply_markup=get_skip_cancel_keyboard()
    )
    await callback.answer()


@router.message(GoalCreation.description)
async def goal_description(message: Message, state: FSMContext):
    """Отримуємо опис."""
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer(uk.CANCELLED, reply_markup=get_main_menu())
        return
    
    description = None if message.text == "⏭ Пропустити" else message.text
    await state.update_data(description=description)
    
    # Перевіряємо чи є проєкти для вкладення
    user_id = message.from_user.id
    projects = await queries.get_projects(user_id)
    
    if projects:
        await state.set_state(GoalCreation.parent)
        await message.answer(
            uk.GOALS['create_parent'],
            reply_markup=kb.get_parent_keyboard(projects)
        )
    else:
        await _ask_deadline(message, state)


@router.callback_query(GoalCreation.parent, F.data.startswith("goal:parent:"))
async def goal_parent(callback: CallbackQuery, state: FSMContext):
    """Отримуємо батьківський проєкт."""
    parent_value = callback.data.replace("goal:parent:", "")
    
    parent_id = None if parent_value == "none" else int(parent_value)
    await state.update_data(parent_id=parent_id)
    
    await _ask_deadline(callback.message, state)
    await callback.answer()


async def _ask_deadline(message: Message, state: FSMContext):
    """Питаємо про дедлайн."""
    await state.set_state(GoalCreation.deadline)
    await message.answer(
        uk.GOALS['create_deadline'],
        reply_markup=kb.get_deadline_keyboard()
    )


@router.callback_query(GoalCreation.deadline, F.data.startswith("goal:deadline:"))
async def goal_deadline(callback: CallbackQuery, state: FSMContext):
    """Отримуємо дедлайн."""
    deadline_type = callback.data.replace("goal:deadline:", "")
    
    if deadline_type == "custom":
        await state.set_state(GoalCreation.deadline_custom)
        await callback.message.edit_text("📅 Введи дату (ДД.ММ.РРРР):")
        await callback.answer()
        return
    
    # Визначаємо дату
    deadline = None
    today = date.today()
    
    if deadline_type == "month":
        # Кінець поточного місяця
        if today.month == 12:
            deadline = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            deadline = date(today.year, today.month + 1, 1) - timedelta(days=1)
        deadline = deadline.isoformat()
    elif deadline_type == "quarter":
        # Кінець кварталу
        quarter_end_month = ((today.month - 1) // 3 + 1) * 3
        if quarter_end_month > 12:
            deadline = date(today.year + 1, 3, 31)
        else:
            next_month = quarter_end_month + 1 if quarter_end_month < 12 else 1
            next_year = today.year if quarter_end_month < 12 else today.year + 1
            deadline = date(next_year, next_month, 1) - timedelta(days=1)
        deadline = deadline.isoformat()
    elif deadline_type == "year":
        deadline = date(today.year, 12, 31).isoformat()
    # none — deadline залишається None
    
    await state.update_data(deadline=deadline)
    
    # В залежності від типу цілі — різні наступні кроки
    data = await state.get_data()
    goal_type = data.get('goal_type')
    
    if goal_type == 'target':
        await state.set_state(GoalCreation.target_value)
        await callback.message.edit_text(uk.GOALS['create_target_value'])
    elif goal_type == 'metric':
        await state.set_state(GoalCreation.target_range)
        await callback.message.edit_text(uk.GOALS['create_target_range'])
    else:  # project
        await _ask_tags(callback, state)
    
    await callback.answer()


@router.message(GoalCreation.deadline_custom)
async def goal_deadline_custom(message: Message, state: FSMContext):
    """Кастомна дата дедлайну."""
    text = message.text.strip()
    
    try:
        parts = text.split(".")
        if len(parts) == 3:
            day, month, year = parts
            deadline = date(int(year), int(month), int(day)).isoformat()
        else:
            await message.answer("❌ Введи дату як ДД.ММ.РРРР")
            return
    except ValueError:
        await message.answer("❌ Невірна дата. Спробуй ще раз.")
        return
    
    await state.update_data(deadline=deadline)
    
    data = await state.get_data()
    goal_type = data.get('goal_type')
    
    if goal_type == 'target':
        await state.set_state(GoalCreation.target_value)
        await message.answer(uk.GOALS['create_target_value'])
    elif goal_type == 'metric':
        await state.set_state(GoalCreation.target_range)
        await message.answer(uk.GOALS['create_target_range'])
    else:
        await state.set_state(GoalCreation.domain_tags)
        await message.answer(
            uk.GOALS['create_tags'],
            reply_markup=kb.get_domain_tags_keyboard([])
        )


@router.message(GoalCreation.target_value)
async def goal_target_value(message: Message, state: FSMContext):
    """Отримуємо цільове значення."""
    try:
        target_value = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("❌ Введи число (наприклад: 24, 100, 5.5)")
        return
    
    await state.update_data(target_value=target_value)
    await state.set_state(GoalCreation.unit)
    
    await message.answer(uk.GOALS['create_unit'])


@router.message(GoalCreation.unit)
async def goal_unit(message: Message, state: FSMContext):
    """Отримуємо одиницю виміру."""
    await state.update_data(unit=message.text.strip())
    await state.set_state(GoalCreation.domain_tags)
    
    await message.answer(
        uk.GOALS['create_tags'],
        reply_markup=kb.get_domain_tags_keyboard([])
    )


@router.message(GoalCreation.target_range)
async def goal_target_range(message: Message, state: FSMContext):
    """Отримуємо діапазон для метрики."""
    text = message.text.strip()
    
    try:
        if "-" in text:
            parts = text.split("-")
            target_min = float(parts[0].strip().replace(",", "."))
            target_max = float(parts[1].strip().replace(",", "."))
        else:
            await message.answer("❌ Введи діапазон як MIN-MAX (наприклад: 73-77)")
            return
    except (ValueError, IndexError):
        await message.answer("❌ Невірний формат. Введи як MIN-MAX")
        return
    
    await state.update_data(target_min=target_min, target_max=target_max)
    await state.set_state(GoalCreation.domain_tags)
    
    await message.answer(
        uk.GOALS['create_tags'],
        reply_markup=kb.get_domain_tags_keyboard([])
    )


async def _ask_tags(callback: CallbackQuery, state: FSMContext):
    """Питаємо про теги."""
    await state.update_data(selected_tags=[])
    await state.set_state(GoalCreation.domain_tags)
    await callback.message.edit_text(
        uk.GOALS['create_tags'],
        parse_mode="HTML",
        reply_markup=kb.get_domain_tags_keyboard([])
    )


@router.callback_query(GoalCreation.domain_tags, F.data.startswith("goal:tag:"))
async def goal_select_tag(callback: CallbackQuery, state: FSMContext):
    """Вибір тегу."""
    tag = callback.data.replace("goal:tag:", "")
    data = await state.get_data()
    selected = data.get('selected_tags', [])
    
    if tag in selected:
        selected.remove(tag)
    else:
        selected.append(tag)
    
    await state.update_data(selected_tags=selected)
    await callback.message.edit_reply_markup(
        reply_markup=kb.get_domain_tags_keyboard(selected)
    )
    await callback.answer()


@router.callback_query(GoalCreation.domain_tags, F.data == "goal:tags:done")
async def goal_tags_done(callback: CallbackQuery, state: FSMContext):
    """Завершення вибору тегів."""
    data = await state.get_data()
    domain_tags = data.get('selected_tags', [])
    
    await state.update_data(domain_tags=domain_tags)
    await _create_goal(callback, state)


async def _create_goal(callback: CallbackQuery, state: FSMContext):
    """Фінальне створення цілі."""
    data = await state.get_data()
    user_id = callback.from_user.id
    
    goal_id = await queries.create_goal(
        user_id=user_id,
        title=data['title'],
        goal_type=data['goal_type'],
        description=data.get('description'),
        parent_id=data.get('parent_id'),
        deadline=data.get('deadline'),
        domain_tags=data.get('domain_tags', []),
        target_value=data.get('target_value'),
        unit=data.get('unit'),
        target_min=data.get('target_min'),
        target_max=data.get('target_max'),
    )
    
    await state.clear()
    
    # Форматуємо відповідь
    type_emojis = {'project': '📁', 'target': '🎯', 'metric': '📊'}
    type_names = {'project': 'Проєкт', 'target': 'Ціль (Target)', 'metric': 'Метрика'}
    
    parent_str = "—"
    if data.get('parent_id'):
        parent = await queries.get_goal_by_id(data['parent_id'], user_id)
        if parent:
            parent_str = parent['title']
    
    tags_str = ", ".join(data.get('domain_tags', [])) or "—"
    
    text = uk.GOALS['create_confirm'].format(
        type_emoji=type_emojis.get(data['goal_type'], '🎯'),
        title=data['title'],
        goal_type=type_names.get(data['goal_type'], data['goal_type']),
        parent=parent_str,
        deadline=data.get('deadline') or '—',
        tags=tags_str
    )
    
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer("✅ Ціль створено!")


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                            CALLBACK ACTIONS                                  ║
# ╚════════════════════════════════════════════════════════════════════════════╝

@router.callback_query(F.data == "goal:add")
async def callback_goal_add(callback: CallbackQuery, state: FSMContext):
    """Додати ціль через inline."""
    await state.clear()
    await state.set_state(GoalCreation.title)
    
    await callback.message.answer(
        uk.GOALS['create_title'],
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "goals:list")
async def callback_goals_list(callback: CallbackQuery):
    """Повернутись до списку цілей."""
    await cmd_goals(callback.message)
    await callback.answer()


@router.callback_query(F.data.startswith("goal:view:"))
async def callback_goal_view(callback: CallbackQuery):
    """Переглянути деталі цілі."""
    goal_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    goal = await queries.get_goal_by_id(goal_id, user_id)
    
    if not goal:
        await callback.answer("❌ Ціль не знайдено", show_alert=True)
        return
    
    type_emojis = {'project': '📁', 'target': '🎯', 'metric': '📊'}
    emoji = type_emojis.get(goal['goal_type'], '🎯')
    
    text = f"{emoji} <b>{goal['title']}</b>\n\n"
    
    if goal.get('description'):
        text += f"📝 {goal['description']}\n\n"
    
    if goal['goal_type'] == 'project':
        progress = goal.get('progress', 0)
        bar = _progress_bar(progress)
        text += f"📊 Прогрес: {bar} {progress}%\n"
        
        # Рахуємо дочірні
        children = await queries.get_child_goals(goal_id, user_id)
        tasks = await queries.get_tasks_by_goal(goal_id, user_id)
        
        if children:
            text += f"🎯 Дочірні цілі: {len(children)}\n"
        if tasks:
            done_tasks = sum(1 for t in tasks if t['is_completed'])
            text += f"📋 Задачі: {done_tasks}/{len(tasks)}\n"
    
    elif goal['goal_type'] == 'target':
        current = goal.get('current_value', 0)
        target = goal.get('target_value', 1)
        unit = goal.get('unit', '')
        progress = goal.get('progress', 0)
        bar = _progress_bar(progress)
        
        text += f"🎯 Прогрес: {current}/{target} {unit} {bar} {progress}%\n"
        
        # Pace calculation
        if goal.get('deadline'):
            deadline = date.fromisoformat(goal['deadline'])
            created = date.fromisoformat(goal['created_at'][:10])
            today = date.today()
            
            days_total = (deadline - created).days
            days_elapsed = (today - created).days
            
            if days_total > 0 and days_elapsed > 0:
                expected = (days_elapsed / days_total) * target
                if current >= expected:
                    text += f"📈 {uk.GOALS['pace_on_track']}\n"
                elif current >= expected * 0.8:
                    text += f"⚠️ Трохи відстаєш\n"
                else:
                    text += f"🔴 {uk.GOALS['pace_behind']}\n"
    
    elif goal['goal_type'] == 'metric':
        target_min = goal.get('target_min')
        target_max = goal.get('target_max')
        if target_min and target_max:
            text += f"📊 Цільовий діапазон: {target_min}-{target_max}\n"
    
    if goal.get('deadline'):
        text += f"📅 Дедлайн: {goal['deadline']}\n"
    
    tags = goal.get('domain_tags', [])
    if tags:
        text += f"🏷 Теги: {', '.join(tags)}\n"
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=kb.get_goal_actions(goal_id, goal['goal_type'])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("goal:entry:"))
async def callback_goal_entry(callback: CallbackQuery, state: FSMContext):
    """Почати додавання запису для Target/Metric."""
    goal_id = int(callback.data.split(":")[-1])
    
    await state.clear()
    await state.update_data(goal_id=goal_id)
    await state.set_state(GoalEntry.value)
    
    await callback.message.edit_text(uk.GOALS['entry_value'])
    await callback.answer()


@router.message(GoalEntry.value)
async def goal_entry_value(message: Message, state: FSMContext):
    """Отримуємо значення запису."""
    try:
        value = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("❌ Введи число")
        return
    
    data = await state.get_data()
    goal_id = data['goal_id']
    user_id = message.from_user.id
    
    await queries.add_goal_entry(goal_id, user_id, value)
    
    goal = await queries.get_goal_by_id(goal_id, user_id)
    progress = goal.get('progress', 0) if goal else 0
    
    await state.clear()
    await message.answer(
        uk.GOALS['entry_added'].format(progress=progress),
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data.startswith("goal:complete:"))
async def callback_goal_complete(callback: CallbackQuery):
    """Завершити ціль."""
    goal_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    success = await queries.complete_goal(goal_id, user_id)
    
    if success:
        await callback.answer("✅ Ціль завершено!", show_alert=True)
        await cmd_goals(callback.message)
    else:
        await callback.answer("❌ Помилка", show_alert=True)


@router.callback_query(F.data.startswith("goal:delete:"))
async def callback_goal_delete(callback: CallbackQuery):
    """Підтвердження видалення."""
    goal_id = int(callback.data.split(":")[-1])
    
    await callback.message.edit_text(
        "🗑 <b>Видалити ціль?</b>\n\nВесь прогрес буде втрачено.",
        parse_mode="HTML",
        reply_markup=kb.get_delete_confirm(goal_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("goal:delete_confirm:"))
async def callback_goal_delete_confirm(callback: CallbackQuery):
    """Фінальне видалення."""
    goal_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    success = await queries.delete_goal(goal_id, user_id)
    
    if success:
        await callback.message.edit_text("🗑 Ціль видалено.")
        await callback.answer("🗑 Видалено")
    else:
        await callback.answer("❌ Помилка", show_alert=True)


@router.callback_query(F.data.startswith("goal:tasks:"))
async def callback_goal_tasks(callback: CallbackQuery):
    """Показати задачі проєкту."""
    goal_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    goal = await queries.get_goal_by_id(goal_id, user_id)
    tasks = await queries.get_tasks_by_goal(goal_id, user_id)
    
    if not tasks:
        text = f"📁 <b>{goal['title']}</b>\n\n📋 Задач немає."
    else:
        text = f"📁 <b>{goal['title']}</b>\n\n📋 <b>Задачі:</b>\n"
        for task in tasks:
            status = "✅" if task['is_completed'] else "⬜"
            text += f"  {status} [{task['id']}] {task['title']}\n"
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Додати задачу", callback_data=f"task:add_to_goal:{goal_id}")
    builder.button(text="◀️ Назад", callback_data=f"goal:view:{goal_id}")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("goal:children:"))
async def callback_goal_children(callback: CallbackQuery):
    """Показати дочірні цілі проєкту."""
    goal_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    goal = await queries.get_goal_by_id(goal_id, user_id)
    children = await queries.get_child_goals(goal_id, user_id)
    
    if not children:
        text = f"📁 <b>{goal['title']}</b>\n\n🎯 Дочірніх цілей немає."
    else:
        text = f"📁 <b>{goal['title']}</b>\n\n🎯 <b>Дочірні цілі:</b>\n"
        type_emojis = {'project': '📁', 'habit': '✅', 'target': '🎯', 'metric': '📊'}
        for child in children:
            emoji = type_emojis.get(child['goal_type'], '🎯')
            progress = child.get('progress', 0)
            text += f"  {emoji} {child['title']} [{progress}%]\n"
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Додати ціль", callback_data="goal:add")
    builder.button(text="◀️ Назад", callback_data=f"goal:view:{goal_id}")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


# Ігноруємо натискання на headers
@router.callback_query(F.data.startswith("goals:header:"))
async def callback_goals_header(callback: CallbackQuery):
    """Ігноруємо натискання на заголовки."""
    await callback.answer()
