"""
Обробники команд для роботи з цілями.
"""

from datetime import datetime, date, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.states.goal_states import GoalCreation, GoalEdit, GoalProgress
from bot.keyboards.goals import (
    get_goal_type_keyboard,
    get_goal_parent_keyboard,
    get_goal_deadline_keyboard,
    get_goals_list_keyboard,
    get_goal_actions_keyboard,
    get_goal_edit_keyboard,
    get_goal_confirm_keyboard,
    get_progress_keyboard,
    GoalCallback,
    GoalAction,
    GoalTypeCallback,
    GoalParentCallback,
    GoalEditCallback,
    GoalEditField,
    GoalType,
    GOAL_TYPE_EMOJI,
)
from bot.keyboards.reply import get_main_reply_keyboard, get_cancel_keyboard, get_skip_cancel_keyboard
from bot.locales import t, get_user_lang
from bot.database import queries

router = Router()


# ============== ДОПОМІЖНІ ФУНКЦІЇ ==============

def format_goal(goal: dict, lang: str) -> str:
    """Форматує ціль для відображення."""
    emoji = GOAL_TYPE_EMOJI.get(GoalType(goal["goal_type"]), "🎯")
    goal_type_name = t(f"goal_type_{goal['goal_type']}", lang)
    
    status_emoji = "✅" if goal.get("status") == "completed" else "📌"
    
    lines = [
        f"{status_emoji} <b>{goal['title']}</b>",
        f"",
        f"📊 {t('goal_type_label', lang)}: {emoji} {goal_type_name}",
    ]
    
    # Прогрес
    progress = goal.get("progress", 0)
    progress_bar = get_progress_bar(progress)
    lines.append(f"📈 {t('progress', lang)}: {progress_bar} {progress}%")
    
    # Опис
    if goal.get("description"):
        lines.append(f"")
        lines.append(f"📝 {goal['description']}")
    
    # Дедлайн
    if goal.get("deadline"):
        deadline_date = datetime.fromisoformat(goal["deadline"]).strftime("%d.%m.%Y")
        lines.append(f"📅 {t('deadline', lang)}: {deadline_date}")
    
    # Батьківська ціль
    if goal.get("parent_id"):
        lines.append(f"🔗 {t('goal_parent', lang)}: #{goal['parent_id']}")
    
    # Дата створення
    created = datetime.fromisoformat(goal["created_at"]).strftime("%d.%m.%Y")
    lines.append(f"")
    lines.append(f"🕐 {t('created', lang)}: {created}")
    
    # Дата завершення
    if goal.get("completed_at"):
        completed = datetime.fromisoformat(goal["completed_at"]).strftime("%d.%m.%Y")
        lines.append(f"✅ {t('completed', lang)}: {completed}")
    
    return "\n".join(lines)


def get_progress_bar(progress: int, length: int = 10) -> str:
    """Створює текстовий прогрес-бар."""
    filled = int(progress / 100 * length)
    empty = length - filled
    return "█" * filled + "░" * empty


def format_goals_list(goals: list, title: str, lang: str) -> str:
    """Форматує список цілей."""
    if not goals:
        return f"{title}\n\n{t('goals_empty', lang)}"
    
    lines = [title, ""]
    
    # Групуємо за типом
    by_type = {}
    for goal in goals:
        goal_type = goal["goal_type"]
        if goal_type not in by_type:
            by_type[goal_type] = []
        by_type[goal_type].append(goal)
    
    # Виводимо у порядку: yearly -> quarterly -> monthly -> weekly
    type_order = ["yearly", "quarterly", "monthly", "weekly"]
    
    for goal_type in type_order:
        if goal_type in by_type:
            emoji = GOAL_TYPE_EMOJI.get(GoalType(goal_type), "🎯")
            type_name = t(f"goal_type_{goal_type}", lang)
            lines.append(f"{emoji} <b>{type_name}</b>:")
            
            for goal in by_type[goal_type]:
                status = "✅" if goal.get("status") == "completed" else "⬜"
                progress = goal.get("progress", 0)
                lines.append(f"  {status} {goal['title']} [{progress}%]")
            
            lines.append("")
    
    # Статистика
    stats = {
        "total": len(goals),
        "completed": sum(1 for g in goals if g.get("status") == "completed"),
        "active": sum(1 for g in goals if g.get("status") == "active")
    }
    lines.append(f"📊 {t('goals_stats', lang, active=stats['active'], completed=stats['completed'])}")
    
    return "\n".join(lines)


def calculate_deadline(option: str) -> str | None:
    """Обчислює дату дедлайну на основі опції."""
    today = date.today()
    
    if option == "end_week":
        # Кінець тижня (неділя)
        days_until_sunday = 6 - today.weekday()
        deadline = today + timedelta(days=days_until_sunday)
    elif option == "end_month":
        # Кінець місяця
        if today.month == 12:
            deadline = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            deadline = date(today.year, today.month + 1, 1) - timedelta(days=1)
    elif option == "end_quarter":
        # Кінець кварталу
        quarter = (today.month - 1) // 3 + 1
        if quarter == 4:
            deadline = date(today.year, 12, 31)
        else:
            deadline = date(today.year, quarter * 3 + 1, 1) - timedelta(days=1)
    elif option == "end_year":
        # Кінець року
        deadline = date(today.year, 12, 31)
    elif option == "none":
        return None
    else:
        return None
    
    return deadline.isoformat()


# ============== КОМАНДИ ==============

@router.message(Command("goals"))
async def cmd_goals(message: Message) -> None:
    """Показати список цілей."""
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    goals = await queries.get_goals_active(user_id)
    
    title = t("goals_active_title", lang)
    text = format_goals_list(goals, title, lang)
    
    await message.answer(text, reply_markup=get_goals_list_keyboard(goals, lang, filter_type="active"))


@router.message(F.text.in_(["🎯 Цілі", "🎯 Goals"]))
async def btn_goals(message: Message) -> None:
    """Кнопка меню для цілей."""
    await cmd_goals(message)


# ============== ФІЛЬТРИ ==============

@router.callback_query(F.data == "goals_filter:active")
async def filter_goals_active(callback: CallbackQuery) -> None:
    """Фільтр: активні цілі."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    goals = await queries.get_goals_active(user_id)
    
    title = t("goals_active_title", lang)
    text = format_goals_list(goals, title, lang)
    
    await callback.message.edit_text(text, reply_markup=get_goals_list_keyboard(goals, lang, filter_type="active"))
    await callback.answer()


@router.callback_query(F.data == "goals_filter:completed")
async def filter_goals_completed(callback: CallbackQuery) -> None:
    """Фільтр: завершені цілі."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    goals = await queries.get_goals_completed(user_id)
    
    title = t("goals_completed_title", lang)
    text = format_goals_list(goals, title, lang)
    
    await callback.message.edit_text(text, reply_markup=get_goals_list_keyboard(goals, lang, filter_type="completed"))
    await callback.answer()


@router.callback_query(F.data == "goals_filter:all")
async def filter_goals_all(callback: CallbackQuery) -> None:
    """Фільтр: всі цілі."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    goals = await queries.get_goals_all(user_id)
    
    title = t("goals_all_title", lang)
    text = format_goals_list(goals, title, lang)
    
    await callback.message.edit_text(text, reply_markup=get_goals_list_keyboard(goals, lang, filter_type="all"))
    await callback.answer()


# ============== СТВОРЕННЯ ЦІЛІ (FSM) ==============

@router.message(Command("goal_add"))
async def start_goal_creation_cmd(message: Message, state: FSMContext) -> None:
    """Почати створення цілі (команда)."""
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    await state.set_state(GoalCreation.title)
    await state.update_data(lang=lang)
    await message.answer(t("goal_add_title", lang), reply_markup=get_cancel_keyboard(lang))


@router.callback_query(F.data == "goal:add")
async def start_goal_creation_cb(callback: CallbackQuery, state: FSMContext) -> None:
    """Почати створення цілі (callback)."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    await state.set_state(GoalCreation.title)
    await state.update_data(lang=lang)
    await callback.message.answer(t("goal_add_title", lang), reply_markup=get_cancel_keyboard(lang))
    await callback.answer()


# --- Крок 1: Назва ---
@router.message(GoalCreation.title)
async def process_goal_title(message: Message, state: FSMContext) -> None:
    """Обробка назви цілі."""
    data = await state.get_data()
    lang = data.get("lang", "en")
    
    if message.text.lower() in ["/cancel", "❌ скасувати", "❌ cancel"]:
        await state.clear()
        await message.answer(t("cancelled", lang), reply_markup=get_main_reply_keyboard(lang))
        return
    
    await state.update_data(title=message.text)
    await state.set_state(GoalCreation.description)
    await message.answer(t("goal_add_description", lang), reply_markup=get_skip_cancel_keyboard(lang))


# --- Крок 2: Опис ---
@router.message(GoalCreation.description)
async def process_goal_description(message: Message, state: FSMContext) -> None:
    """Обробка опису цілі."""
    data = await state.get_data()
    lang = data.get("lang", "en")
    
    if message.text.lower() in ["/cancel", "❌ скасувати", "❌ cancel"]:
        await state.clear()
        await message.answer(t("cancelled", lang), reply_markup=get_main_reply_keyboard(lang))
        return
    
    description = None
    if message.text.lower() not in ["skip", "пропустити", "⏭ skip", "⏭ пропустити"]:
        description = message.text
    
    await state.update_data(description=description)
    await state.set_state(GoalCreation.goal_type)
    await message.answer(
        t("goal_add_type", lang),
        reply_markup=get_goal_type_keyboard(lang)
    )


# --- Крок 3: Тип цілі ---
@router.callback_query(GoalCreation.goal_type, GoalTypeCallback.filter())
async def process_goal_type(callback: CallbackQuery, callback_data: GoalTypeCallback, state: FSMContext) -> None:
    """Обробка типу цілі."""
    data = await state.get_data()
    lang = data.get("lang", "en")
    user_id = callback.from_user.id
    
    await state.update_data(goal_type=callback_data.goal_type.value)
    
    # Отримуємо можливі батьківські цілі
    parent_goals = await queries.get_parent_goals(user_id)
    
    if parent_goals:
        await state.set_state(GoalCreation.parent)
        await callback.message.edit_text(
            t("goal_add_parent", lang),
            reply_markup=get_goal_parent_keyboard(parent_goals, lang)
        )
    else:
        # Пропускаємо вибір батьківської цілі
        await state.update_data(parent_id=None)
        await state.set_state(GoalCreation.deadline)
        await callback.message.edit_text(
            t("goal_add_deadline", lang),
            reply_markup=get_goal_deadline_keyboard(lang)
        )
    
    await callback.answer()


# --- Крок 4: Батьківська ціль ---
@router.callback_query(GoalCreation.parent, GoalParentCallback.filter())
async def process_goal_parent(callback: CallbackQuery, callback_data: GoalParentCallback, state: FSMContext) -> None:
    """Обробка батьківської цілі."""
    data = await state.get_data()
    lang = data.get("lang", "en")
    
    parent_id = callback_data.parent_id if callback_data.parent_id > 0 else None
    await state.update_data(parent_id=parent_id)
    
    await state.set_state(GoalCreation.deadline)
    await callback.message.edit_text(
        t("goal_add_deadline", lang),
        reply_markup=get_goal_deadline_keyboard(lang)
    )
    await callback.answer()


# --- Крок 5: Дедлайн ---
@router.callback_query(GoalCreation.deadline, F.data.startswith("goal_deadline:"))
async def process_goal_deadline(callback: CallbackQuery, state: FSMContext) -> None:
    """Обробка дедлайну цілі."""
    data = await state.get_data()
    lang = data.get("lang", "en")
    user_id = callback.from_user.id
    
    option = callback.data.split(":")[1]
    
    if option == "custom":
        # Перехід до текстового вводу
        await callback.message.edit_text(t("goal_add_deadline_custom", lang))
        return
    
    deadline = calculate_deadline(option)
    
    # Створюємо ціль
    goal_id = await queries.create_goal(
        user_id=user_id,
        title=data["title"],
        goal_type=data["goal_type"],
        description=data.get("description"),
        parent_id=data.get("parent_id"),
        deadline=deadline
    )
    
    await state.clear()
    
    # Показуємо підтвердження
    goal = await queries.get_goal_by_id(goal_id, user_id)
    await callback.message.edit_text(
        t("goal_created", lang, goal_id=goal_id) + "\n\n" + format_goal(goal, lang),
        reply_markup=get_goal_actions_keyboard(goal_id, lang)
    )
    await callback.answer(t("goal_created_short", lang), show_alert=True)


# --- Текстовий ввід дедлайну ---
@router.message(GoalCreation.deadline)
async def process_goal_deadline_text(message: Message, state: FSMContext) -> None:
    """Обробка текстового вводу дедлайну."""
    data = await state.get_data()
    lang = data.get("lang", "en")
    user_id = message.from_user.id
    
    # Парсимо дату
    from bot.handlers.tasks import parse_date
    parsed_date = parse_date(message.text)
    
    if not parsed_date:
        await message.answer(t("error_invalid_date", lang))
        return
    
    deadline = parsed_date.isoformat()
    
    # Створюємо ціль
    goal_id = await queries.create_goal(
        user_id=user_id,
        title=data["title"],
        goal_type=data["goal_type"],
        description=data.get("description"),
        parent_id=data.get("parent_id"),
        deadline=deadline
    )
    
    await state.clear()
    
    # Показуємо підтвердження
    goal = await queries.get_goal_by_id(goal_id, user_id)
    await message.answer(
        t("goal_created", lang, goal_id=goal_id) + "\n\n" + format_goal(goal, lang),
        reply_markup=get_goal_actions_keyboard(goal_id, lang)
    )


# ============== ДІЇ З ЦІЛЯМИ ==============

@router.callback_query(GoalCallback.filter(F.action == GoalAction.view))
async def view_goal(callback: CallbackQuery, callback_data: GoalCallback) -> None:
    """Перегляд цілі."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    goal = await queries.get_goal_by_id(callback_data.goal_id, user_id)
    
    if not goal:
        await callback.answer(t("goal_not_found", lang), show_alert=True)
        return
    
    is_completed = goal.get("status") == "completed"
    await callback.message.edit_text(
        format_goal(goal, lang),
        reply_markup=get_goal_actions_keyboard(goal["id"], lang, is_completed=is_completed)
    )
    await callback.answer()


@router.callback_query(GoalCallback.filter(F.action == GoalAction.complete))
async def complete_goal(callback: CallbackQuery, callback_data: GoalCallback) -> None:
    """Завершити ціль."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    
    success = await queries.complete_goal(callback_data.goal_id, user_id)
    
    if success:
        await callback.answer(t("goal_completed", lang), show_alert=True)
        # Показуємо оновлену ціль
        goal = await queries.get_goal_by_id(callback_data.goal_id, user_id)
        if goal:
            await callback.message.edit_text(
                format_goal(goal, lang),
                reply_markup=get_goal_actions_keyboard(goal["id"], lang, is_completed=True)
            )
    else:
        await callback.answer(t("error_general", lang), show_alert=True)


@router.callback_query(GoalCallback.filter(F.action == GoalAction.restore))
async def restore_goal(callback: CallbackQuery, callback_data: GoalCallback) -> None:
    """Повернути ціль в активні."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    
    success = await queries.restore_goal(callback_data.goal_id, user_id)
    
    if success:
        await callback.answer(t("goal_restored", lang), show_alert=True)
        goal = await queries.get_goal_by_id(callback_data.goal_id, user_id)
        if goal:
            await callback.message.edit_text(
                format_goal(goal, lang),
                reply_markup=get_goal_actions_keyboard(goal["id"], lang, is_completed=False)
            )
    else:
        await callback.answer(t("error_general", lang), show_alert=True)


@router.callback_query(GoalCallback.filter(F.action == GoalAction.delete))
async def delete_goal_confirm(callback: CallbackQuery, callback_data: GoalCallback) -> None:
    """Підтвердження видалення цілі."""
    lang = get_user_lang(callback.from_user.id)
    await callback.message.edit_text(
        t("goal_delete_confirm", lang),
        reply_markup=get_goal_confirm_keyboard(callback_data.goal_id, "delete", lang)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("goal_confirm:delete:"))
async def delete_goal_execute(callback: CallbackQuery) -> None:
    """Виконати видалення цілі."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    goal_id = int(callback.data.split(":")[2])
    
    success = await queries.delete_goal(goal_id, user_id)
    
    if success:
        await callback.answer(t("goal_deleted", lang), show_alert=True)
        # Повертаємося до списку
        goals = await queries.get_goals_active(user_id)
        title = t("goals_active_title", lang)
        text = format_goals_list(goals, title, lang)
        await callback.message.edit_text(text, reply_markup=get_goals_list_keyboard(goals, lang))
    else:
        await callback.answer(t("error_general", lang), show_alert=True)


# ============== ПРОГРЕС ==============

@router.callback_query(GoalCallback.filter(F.action == GoalAction.progress))
async def show_progress_options(callback: CallbackQuery, callback_data: GoalCallback, state: FSMContext) -> None:
    """Показати опції оновлення прогресу."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    
    await state.update_data(progress_goal_id=callback_data.goal_id, lang=lang)
    
    goal = await queries.get_goal_by_id(callback_data.goal_id, user_id)
    current_progress = goal.get("progress", 0) if goal else 0
    
    await callback.message.edit_text(
        t("goal_progress_prompt", lang, current=current_progress),
        reply_markup=get_progress_keyboard(lang)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("goal_progress_quick:"))
async def process_quick_progress(callback: CallbackQuery, state: FSMContext) -> None:
    """Швидке оновлення прогресу."""
    user_id = callback.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "en")
    goal_id = data.get("progress_goal_id")
    
    if not goal_id:
        await callback.answer(t("error_general", lang), show_alert=True)
        return
    
    progress = int(callback.data.split(":")[1])
    
    success = await queries.update_goal_progress(goal_id, user_id, progress)
    await state.clear()
    
    if success:
        await callback.answer(t("goal_progress_updated", lang, progress=progress), show_alert=True)
        goal = await queries.get_goal_by_id(goal_id, user_id)
        if goal:
            await callback.message.edit_text(
                format_goal(goal, lang),
                reply_markup=get_goal_actions_keyboard(goal_id, lang)
            )
    else:
        await callback.answer(t("error_general", lang), show_alert=True)


@router.callback_query(F.data == "goal_progress_custom")
async def start_custom_progress(callback: CallbackQuery, state: FSMContext) -> None:
    """Почати ввід кастомного прогресу."""
    data = await state.get_data()
    lang = data.get("lang", "en")
    
    await state.set_state(GoalProgress.enter_progress)
    await callback.message.edit_text(t("goal_progress_enter", lang))
    await callback.answer()


@router.message(GoalProgress.enter_progress)
async def process_custom_progress(message: Message, state: FSMContext) -> None:
    """Обробка кастомного прогресу."""
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "en")
    goal_id = data.get("progress_goal_id")
    
    try:
        progress = int(message.text.replace("%", "").strip())
        if progress < 0 or progress > 100:
            raise ValueError()
    except ValueError:
        await message.answer(t("error_invalid_progress", lang))
        return
    
    success = await queries.update_goal_progress(goal_id, user_id, progress)
    await state.clear()
    
    if success:
        await message.answer(t("goal_progress_updated", lang, progress=progress), reply_markup=get_main_reply_keyboard(lang))
        goal = await queries.get_goal_by_id(goal_id, user_id)
        if goal:
            await message.answer(
                format_goal(goal, lang),
                reply_markup=get_goal_actions_keyboard(goal_id, lang)
            )
    else:
        await message.answer(t("error_general", lang), reply_markup=get_main_reply_keyboard(lang))


# ============== РЕДАГУВАННЯ ==============

@router.callback_query(GoalCallback.filter(F.action == GoalAction.edit))
async def edit_goal_menu(callback: CallbackQuery, callback_data: GoalCallback) -> None:
    """Показати меню редагування цілі."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    goal = await queries.get_goal_by_id(callback_data.goal_id, user_id)
    
    if not goal:
        await callback.answer(t("goal_not_found", lang), show_alert=True)
        return
    
    await callback.message.edit_text(
        t("goal_edit_choose_field", lang, title=goal["title"]),
        reply_markup=get_goal_edit_keyboard(callback_data.goal_id, lang)
    )
    await callback.answer()


@router.callback_query(GoalEditCallback.filter())
async def edit_goal_field(callback: CallbackQuery, callback_data: GoalEditCallback, state: FSMContext) -> None:
    """Обробка вибору поля для редагування."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    
    await state.update_data(edit_goal_id=callback_data.goal_id, edit_field=callback_data.field.value, lang=lang)
    
    if callback_data.field == GoalEditField.goal_type:
        await state.set_state(GoalEdit.waiting_for_value)
        await callback.message.edit_text(
            t("goal_edit_type", lang),
            reply_markup=get_goal_type_keyboard(lang)
        )
    elif callback_data.field == GoalEditField.deadline:
        await state.set_state(GoalEdit.waiting_for_value)
        await callback.message.edit_text(
            t("goal_edit_deadline", lang),
            reply_markup=get_goal_deadline_keyboard(lang)
        )
    else:
        # Текстовий ввід (title, description)
        await state.set_state(GoalEdit.waiting_for_value)
        prompt_key = f"goal_edit_{callback_data.field.value}"
        await callback.message.edit_text(t(prompt_key, lang))
    
    await callback.answer()


# --- Текстовий ввід при редагуванні ---
@router.message(GoalEdit.waiting_for_value)
async def process_edit_goal_text(message: Message, state: FSMContext) -> None:
    """Обробка текстового вводу при редагуванні цілі."""
    user_id = message.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "en")
    goal_id = data.get("edit_goal_id")
    field = data.get("edit_field")
    
    if not goal_id or not field:
        await state.clear()
        await message.answer(t("error_general", lang), reply_markup=get_main_reply_keyboard(lang))
        return
    
    update_data = {}
    
    if field == "title":
        update_data["title"] = message.text
    elif field == "description":
        update_data["description"] = message.text
    elif field == "deadline":
        from bot.handlers.tasks import parse_date
        parsed_date = parse_date(message.text)
        if not parsed_date:
            await message.answer(t("error_invalid_date", lang))
            return
        update_data["deadline"] = parsed_date.isoformat()
    
    success = await queries.update_goal(goal_id, user_id, **update_data)
    await state.clear()
    
    if success:
        await message.answer(t("goal_updated", lang), reply_markup=get_main_reply_keyboard(lang))
        goal = await queries.get_goal_by_id(goal_id, user_id)
        if goal:
            await message.answer(
                format_goal(goal, lang),
                reply_markup=get_goal_actions_keyboard(goal_id, lang)
            )
    else:
        await message.answer(t("error_general", lang), reply_markup=get_main_reply_keyboard(lang))


# --- Редагування типу цілі ---
@router.callback_query(GoalEdit.waiting_for_value, GoalTypeCallback.filter())
async def process_edit_goal_type(callback: CallbackQuery, callback_data: GoalTypeCallback, state: FSMContext) -> None:
    """Редагування типу цілі."""
    user_id = callback.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "en")
    goal_id = data.get("edit_goal_id")
    
    success = await queries.update_goal(goal_id, user_id, goal_type=callback_data.goal_type.value)
    await state.clear()
    
    if success:
        await callback.answer(t("goal_updated", lang))
        goal = await queries.get_goal_by_id(goal_id, user_id)
        if goal:
            await callback.message.edit_text(
                format_goal(goal, lang),
                reply_markup=get_goal_actions_keyboard(goal_id, lang)
            )
    else:
        await callback.answer(t("error_general", lang), show_alert=True)


# --- Редагування дедлайну ---
@router.callback_query(GoalEdit.waiting_for_value, F.data.startswith("goal_deadline:"))
async def process_edit_goal_deadline(callback: CallbackQuery, state: FSMContext) -> None:
    """Редагування дедлайну цілі."""
    user_id = callback.from_user.id
    data = await state.get_data()
    lang = data.get("lang", "en")
    goal_id = data.get("edit_goal_id")
    
    option = callback.data.split(":")[1]
    
    if option == "custom":
        await callback.message.edit_text(t("goal_add_deadline_custom", lang))
        await callback.answer()
        return
    
    deadline = calculate_deadline(option)
    
    success = await queries.update_goal(goal_id, user_id, deadline=deadline)
    await state.clear()
    
    if success:
        await callback.answer(t("goal_updated", lang))
        goal = await queries.get_goal_by_id(goal_id, user_id)
        if goal:
            await callback.message.edit_text(
                format_goal(goal, lang),
                reply_markup=get_goal_actions_keyboard(goal_id, lang)
            )
    else:
        await callback.answer(t("error_general", lang), show_alert=True)


# ============== НАВІГАЦІЯ ==============

@router.callback_query(F.data == "goals:back")
async def back_to_goals(callback: CallbackQuery) -> None:
    """Повернутися до списку цілей."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    goals = await queries.get_goals_active(user_id)
    
    title = t("goals_active_title", lang)
    text = format_goals_list(goals, title, lang)
    
    await callback.message.edit_text(text, reply_markup=get_goals_list_keyboard(goals, lang))
    await callback.answer()
