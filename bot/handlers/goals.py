"""
Обробники цілей: project, target, metric.
LifeHub Bot v4.0

ВАЖЛИВО: Habits — в окремому файлі handlers/habits.py!
Goals тут: тільки project, target, metric.
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
    """Показати всі цілі (project, target, metric)."""
    user_id = message.from_user.id
    goals = await queries.get_all_goals(user_id, status='active')
    
    # Фільтруємо тільки project, target, metric (habits окремо)
    goals = [g for g in goals if g['goal_type'] in ('project', 'target', 'metric')]
    
    if not goals:
        await message.answer(
            f"{uk.GOALS['title_all']}\n\n{uk.GOALS['empty']}",
            parse_mode="HTML"
        )
        return
    
    text = uk.GOALS['title_all'] + "\n\n"
    
    # Групуємо по типу
    projects = [g for g in goals if g['goal_type'] == 'project']
    targets = [g for g in goals if g['goal_type'] == 'target']
    metrics = [g for g in goals if g['goal_type'] == 'metric']
    
    if projects:
        text += "<b>📁 ПРОЄКТИ:</b>\n"
        for g in projects:
            progress = g.get('progress', 0)
            text += f"  • [{g['id']}] {g['title']} — {progress}%\n"
        text += "\n"
    
    if targets:
        text += "<b>🎯 ЦІЛІ:</b>\n"
        for g in targets:
            current = g.get('current_value', 0) or 0
            target = g.get('target_value', 1) or 1
            unit = g.get('unit', '')
            text += f"  • [{g['id']}] {g['title']} — {current}/{target} {unit}\n"
        text += "\n"
    
    if metrics:
        text += "<b>📊 МЕТРИКИ:</b>\n"
        for g in metrics:
            min_v = g.get('target_min') or '?'
            max_v = g.get('target_max') or '?'
            text += f"  • [{g['id']}] {g['title']} ({min_v}-{max_v})\n"
    
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=kb.get_goals_list(goals)
    )


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
    
    if goal_type == "target":
        # Для Target — питаємо target_value
        await state.set_state(GoalCreation.target_value)
        await callback.message.edit_text(uk.GOALS['create_target_value'])
    elif goal_type == "metric":
        # Для Metric — питаємо range
        await state.set_state(GoalCreation.target_range)
        await callback.message.edit_text(uk.GOALS['create_target_range'])
    else:
        # Для Project — питаємо опис
        await state.set_state(GoalCreation.description)
        await callback.message.edit_text(
            uk.GOALS['create_description'],
            reply_markup=None
        )
        await callback.message.answer(
            "Введи опис або натисни кнопку:",
            reply_markup=get_skip_cancel_keyboard()
        )
    
    await callback.answer()


@router.message(GoalCreation.target_value)
async def goal_target_value(message: Message, state: FSMContext):
    """Отримуємо цільове значення для Target."""
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer(uk.CANCELLED, reply_markup=get_main_menu())
        return
    
    try:
        target_value = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer(uk.ERRORS['invalid_number'])
        return
    
    await state.update_data(target_value=target_value)
    await state.set_state(GoalCreation.unit)
    
    await message.answer(uk.GOALS['create_unit'])


@router.message(GoalCreation.unit)
async def goal_unit(message: Message, state: FSMContext):
    """Отримуємо одиницю виміру."""
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer(uk.CANCELLED, reply_markup=get_main_menu())
        return
    
    await state.update_data(unit=message.text)
    await state.set_state(GoalCreation.deadline)
    
    await message.answer(
        uk.GOALS['create_deadline'],
        reply_markup=kb.get_deadline_keyboard()
    )


@router.message(GoalCreation.target_range)
async def goal_target_range(message: Message, state: FSMContext):
    """Отримуємо діапазон для Metric."""
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer(uk.CANCELLED, reply_markup=get_main_menu())
        return
    
    try:
        if "-" in message.text:
            parts = message.text.split("-")
            target_min = float(parts[0].strip().replace(",", "."))
            target_max = float(parts[1].strip().replace(",", "."))
        else:
            await message.answer("❌ Введи діапазон у форматі МІН-МАКС (наприклад: 73-77)")
            return
    except (ValueError, IndexError):
        await message.answer("❌ Введи діапазон у форматі МІН-МАКС (наприклад: 73-77)")
        return
    
    await state.update_data(target_min=target_min, target_max=target_max)
    await state.set_state(GoalCreation.deadline)
    
    await message.answer(
        uk.GOALS['create_deadline'],
        reply_markup=kb.get_deadline_keyboard()
    )


@router.message(GoalCreation.description)
async def goal_description(message: Message, state: FSMContext):
    """Отримуємо опис."""
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer(uk.CANCELLED, reply_markup=get_main_menu())
        return
    
    description = None if message.text == "⏭ Пропустити" else message.text
    await state.update_data(description=description)
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
    
    deadline = None
    today = date.today()
    
    if deadline_type == "month":
        # Кінець поточного місяця
        next_month = today.replace(day=28) + timedelta(days=4)
        deadline = (next_month - timedelta(days=next_month.day)).isoformat()
    elif deadline_type == "quarter":
        # Кінець кварталу
        quarter_end_month = ((today.month - 1) // 3 + 1) * 3
        if quarter_end_month > 12:
            quarter_end_month = 12
        deadline = date(today.year, quarter_end_month, 28).isoformat()
    elif deadline_type == "year":
        deadline = date(today.year, 12, 31).isoformat()
    
    await state.update_data(deadline=deadline)
    
    # Перевіряємо чи є проєкти для вибору батьківського
    user_id = callback.from_user.id
    projects = await queries.get_projects(user_id)
    
    data = await state.get_data()
    # Project не може бути дочірнім до себе, тому показуємо вибір тільки для target/metric
    if projects and data.get('goal_type') != 'project':
        await state.set_state(GoalCreation.parent)
        await callback.message.edit_text(
            uk.GOALS['create_parent'],
            reply_markup=kb.get_parent_keyboard(projects)
        )
    else:
        await state.set_state(GoalCreation.domain_tags)
        await callback.message.edit_text(
            uk.GOALS['create_tags'],
            reply_markup=kb.get_domain_tags_keyboard([])
        )
    
    await callback.answer()


@router.message(GoalCreation.deadline_custom)
async def goal_deadline_custom(message: Message, state: FSMContext):
    """Отримуємо кастомну дату дедлайну."""
    text = message.text.strip()
    
    try:
        if "." in text:
            parts = text.split(".")
            if len(parts) == 3:
                day, month, year = parts
            else:
                day, month = parts
                year = date.today().year
            deadline = date(int(year), int(month), int(day)).isoformat()
        else:
            await message.answer(uk.ERRORS['invalid_date'])
            return
    except ValueError:
        await message.answer(uk.ERRORS['invalid_date'])
        return
    
    await state.update_data(deadline=deadline)
    
    user_id = message.from_user.id
    projects = await queries.get_projects(user_id)
    data = await state.get_data()
    
    if projects and data.get('goal_type') != 'project':
        await state.set_state(GoalCreation.parent)
        await message.answer(
            uk.GOALS['create_parent'],
            reply_markup=kb.get_parent_keyboard(projects)
        )
    else:
        await state.set_state(GoalCreation.domain_tags)
        await message.answer(
            uk.GOALS['create_tags'],
            reply_markup=kb.get_domain_tags_keyboard([])
        )


@router.callback_query(GoalCreation.parent, F.data.startswith("goal:parent:"))
async def goal_parent(callback: CallbackQuery, state: FSMContext):
    """Отримуємо батьківський проєкт."""
    parent_value = callback.data.replace("goal:parent:", "")
    
    parent_id = None if parent_value == "none" else int(parent_value)
    await state.update_data(parent_id=parent_id)
    
    await state.set_state(GoalCreation.domain_tags)
    await state.update_data(selected_tags=[])
    
    await callback.message.edit_text(
        uk.GOALS['create_tags'],
        reply_markup=kb.get_domain_tags_keyboard([])
    )
    await callback.answer()


@router.callback_query(GoalCreation.domain_tags, F.data.startswith("goal:tag:"))
async def goal_tag_toggle(callback: CallbackQuery, state: FSMContext):
    """Перемикання тегу."""
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
    """Завершення вибору тегів і створення цілі."""
    data = await state.get_data()
    user_id = callback.from_user.id
    
    # Створюємо ціль
    goal_id = await queries.create_goal(
        user_id=user_id,
        title=data['title'],
        goal_type=data['goal_type'],
        description=data.get('description'),
        parent_id=data.get('parent_id'),
        deadline=data.get('deadline'),
        domain_tags=data.get('selected_tags', []),
        target_value=data.get('target_value'),
        unit=data.get('unit'),
        target_min=data.get('target_min'),
        target_max=data.get('target_max'),
    )
    
    await state.clear()
    
    # Форматуємо відповідь
    type_emojis = {'project': '📁', 'target': '🎯', 'metric': '📊'}
    
    parent_str = "Без батьківського"
    if data.get('parent_id'):
        parent = await queries.get_goal_by_id(data['parent_id'], user_id)
        if parent:
            parent_str = parent['title']
    
    tags_str = ", ".join(data.get('selected_tags', [])) or "—"
    
    text = uk.GOALS['create_confirm'].format(
        type_emoji=type_emojis.get(data['goal_type'], '🎯'),
        title=data['title'],
        goal_type=data['goal_type'],
        parent=parent_str,
        deadline=data.get('deadline') or 'Без дедлайну',
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


@router.callback_query(F.data.startswith("goal:view:"))
async def callback_goal_view(callback: CallbackQuery):
    """Переглянути деталі цілі."""
    goal_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    goal = await queries.get_goal_by_id(goal_id, user_id)
    
    if not goal:
        await callback.answer("❌ Ціль не знайдено", show_alert=True)
        return
    
    type_labels = {
        'project': '📁 Проєкт',
        'target': '🎯 Ціль',
        'metric': '📊 Метрика'
    }
    
    text = f"""
{type_labels.get(goal['goal_type'], '🎯')} <b>{goal['title']}</b>

📊 Прогрес: {goal.get('progress', 0)}%
📅 Дедлайн: {goal.get('deadline') or 'Без дедлайну'}
"""
    
    if goal['goal_type'] == 'target':
        current = goal.get('current_value', 0) or 0
        target = goal.get('target_value', 0) or 0
        unit = goal.get('unit', '')
        text += f"🎯 Значення: {current}/{target} {unit}\n"
    
    if goal['goal_type'] == 'metric':
        min_v = goal.get('target_min') or '?'
        max_v = goal.get('target_max') or '?'
        text += f"📊 Діапазон: {min_v}-{max_v}\n"
    
    if goal.get('description'):
        text += f"\n📝 {goal['description']}\n"
    
    if goal.get('domain_tags'):
        text += f"🏷 Теги: {', '.join(goal['domain_tags'])}\n"
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=kb.get_goal_actions(goal_id, goal['goal_type'])
    )
    await callback.answer()


@router.callback_query(F.data == "goals:list")
async def callback_goals_list(callback: CallbackQuery):
    """Повернутись до списку цілей."""
    await cmd_goals(callback.message)
    await callback.answer()


@router.callback_query(F.data.startswith("goal:entry:"))
async def callback_goal_entry(callback: CallbackQuery, state: FSMContext):
    """Почати додавання запису для Target/Metric."""
    goal_id = int(callback.data.split(":")[-1])
    
    await state.set_state(GoalEntry.value)
    await state.update_data(goal_id=goal_id)
    
    await callback.message.edit_text(uk.GOALS['entry_value'])
    await callback.answer()


@router.message(GoalEntry.value)
async def goal_entry_value(message: Message, state: FSMContext):
    """Отримуємо значення запису."""
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer(uk.CANCELLED, reply_markup=get_main_menu())
        return
    
    try:
        value = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer(uk.ERRORS['invalid_number'])
        return
    
    data = await state.get_data()
    user_id = message.from_user.id
    
    await queries.add_goal_entry(data['goal_id'], user_id, value)
    
    goal = await queries.get_goal_by_id(data['goal_id'], user_id)
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
        "🗑 <b>Видалити ціль?</b>\n\nЦю дію неможливо скасувати.",
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
        await callback.message.edit_text(uk.GOALS['deleted'])
        await callback.answer("🗑 Видалено")
    else:
        await callback.answer("❌ Помилка", show_alert=True)


@router.callback_query(F.data.startswith("goal:tasks:"))
async def callback_goal_tasks(callback: CallbackQuery):
    """Показати задачі проєкту."""
    goal_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    tasks = await queries.get_tasks_by_goal(goal_id, user_id)
    goal = await queries.get_goal_by_id(goal_id, user_id)
    
    if not tasks:
        await callback.answer("📭 Задач у проєкті немає", show_alert=True)
        return
    
    text = f"📁 <b>{goal['title']}</b>\n\n📋 Задачі:\n"
    
    for task in tasks:
        status = "✅" if task['is_completed'] else "⬜"
        text += f"  {status} [{task['id']}] {task['title']}\n"
    
    done = sum(1 for t in tasks if t['is_completed'])
    text += f"\n📊 {done}/{len(tasks)}"
    
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("goal:children:"))
async def callback_goal_children(callback: CallbackQuery):
    """Показати дочірні цілі проєкту."""
    goal_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    children = await queries.get_child_goals(goal_id, user_id)
    goal = await queries.get_goal_by_id(goal_id, user_id)
    
    if not children:
        await callback.answer("📭 Дочірніх цілей немає", show_alert=True)
        return
    
    text = f"📁 <b>{goal['title']}</b>\n\n🎯 Дочірні цілі:\n"
    
    type_emojis = {'project': '📁', 'habit': '✅', 'target': '🎯', 'metric': '📊'}
    
    for child in children:
        emoji = type_emojis.get(child['goal_type'], '🎯')
        progress = child.get('progress', 0)
        text += f"  {emoji} [{child['id']}] {child['title']} — {progress}%\n"
    
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("goals:header:"))
async def callback_goals_header(callback: CallbackQuery):
    """Ігноруємо кліки на заголовки."""
    await callback.answer()


@router.callback_query(F.data == "goal:cancel")
async def callback_goal_cancel(callback: CallbackQuery, state: FSMContext):
    """Скасування створення цілі."""
    await state.clear()
    await callback.message.edit_text(uk.CANCELLED)
    await callback.answer()
