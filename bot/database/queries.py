"""
SQL запити для роботи з даними.
LifeHub Bot v4.0

Єдиний файл для всіх запитів:
- User settings
- Tasks (one-time + recurring)
- Task occurrences
- Goals (project, habit, target, metric)
- Habit logs
- Goal entries
"""

import json
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from bot.database.models import get_db


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                           USER SETTINGS                                      ║
# ╚════════════════════════════════════════════════════════════════════════════╝

async def get_user_settings(user_id: int) -> Optional[Dict[str, Any]]:
    """Отримати налаштування користувача."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM user_settings WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def get_user_language(user_id: int) -> str:
    """Отримати мову користувача."""
    settings = await get_user_settings(user_id)
    return settings['language'] if settings else 'uk'


async def upsert_user_settings(user_id: int, **kwargs) -> None:
    """Створити або оновити налаштування."""
    db = await get_db()
    try:
        # Спочатку спробуємо вставити
        existing = await get_user_settings(user_id)
        
        if existing:
            if kwargs:
                fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
                values = list(kwargs.values()) + [user_id]
                await db.execute(
                    f"UPDATE user_settings SET {fields} WHERE user_id = ?",
                    values
                )
        else:
            kwargs['user_id'] = user_id
            columns = ", ".join(kwargs.keys())
            placeholders = ", ".join("?" * len(kwargs))
            await db.execute(
                f"INSERT INTO user_settings ({columns}) VALUES ({placeholders})",
                list(kwargs.values())
            )
        
        await db.commit()
    finally:
        await db.close()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                              TASKS                                           ║
# ╚════════════════════════════════════════════════════════════════════════════╝

async def create_task(
    user_id: int,
    title: str,
    description: Optional[str] = None,
    priority: int = 2,
    deadline: Optional[str] = None,
    scheduled_time: Optional[str] = None,
    scheduled_end: Optional[str] = None,
    estimated_minutes: Optional[int] = None,
    is_recurring: bool = False,
    recurrence_rule: Optional[str] = None,
    recurrence_days: Optional[str] = None,
    is_fixed: bool = False,
    goal_id: Optional[int] = None,
) -> int:
    """Створити задачу. Повертає ID."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            INSERT INTO tasks (
                user_id, title, description, priority, deadline,
                scheduled_time, scheduled_end, estimated_minutes,
                is_recurring, recurrence_rule, recurrence_days,
                is_fixed, goal_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, title, description, priority, deadline,
             scheduled_time, scheduled_end, estimated_minutes,
             int(is_recurring), recurrence_rule, recurrence_days,
             int(is_fixed), goal_id)
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_task_by_id(task_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Отримати задачу за ID."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT t.*, g.title as goal_title
            FROM tasks t
            LEFT JOIN goals g ON t.goal_id = g.id
            WHERE t.id = ? AND t.user_id = ?
            """,
            (task_id, user_id)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def get_tasks_today(user_id: int) -> List[Dict[str, Any]]:
    """
    Отримати задачі на сьогодні:
    1. One-time з deadline = today
    2. One-time з deadline < today (прострочені)
    3. НЕ включає задачі без дедлайну (вони в Inbox)
    4. НЕ включає recurring (вони окремо)
    """
    today = date.today().isoformat()
    
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT t.*, g.title as goal_title
            FROM tasks t
            LEFT JOIN goals g ON t.goal_id = g.id
            WHERE t.user_id = ? 
              AND t.is_completed = 0
              AND t.is_recurring = 0
              AND t.deadline IS NOT NULL
              AND DATE(t.deadline) <= ?
            ORDER BY t.priority ASC, t.scheduled_time ASC, t.deadline ASC
            """,
            (user_id, today)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_tasks_inbox(user_id: int) -> List[Dict[str, Any]]:
    """
    GTD Inbox: задачі без дедлайну і без прив'язки до проєкту.
    Це "необроблені" задачі, які потрібно спланувати.
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM tasks 
            WHERE user_id = ? 
              AND is_completed = 0
              AND is_recurring = 0
              AND deadline IS NULL
              AND goal_id IS NULL
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_tasks_all(user_id: int, include_completed: bool = False) -> List[Dict[str, Any]]:
    """Отримати всі задачі (крім recurring)."""
    db = await get_db()
    try:
        query = """
            SELECT t.*, g.title as goal_title
            FROM tasks t
            LEFT JOIN goals g ON t.goal_id = g.id
            WHERE t.user_id = ? AND t.is_recurring = 0
        """
        if not include_completed:
            query += " AND t.is_completed = 0"
        query += " ORDER BY t.priority ASC, t.deadline ASC"
        
        cursor = await db.execute(query, (user_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_tasks_by_goal(goal_id: int, user_id: int) -> List[Dict[str, Any]]:
    """Отримати задачі прив'язані до цілі."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM tasks 
            WHERE user_id = ? AND goal_id = ?
            ORDER BY is_completed ASC, priority ASC, deadline ASC
            """,
            (user_id, goal_id)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def complete_task(task_id: int, user_id: int) -> bool:
    """Позначити one-time задачу виконаною."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            UPDATE tasks 
            SET is_completed = 1, completed_at = ?
            WHERE id = ? AND user_id = ? AND is_recurring = 0
            """,
            (datetime.now().isoformat(), task_id, user_id)
        )
        await db.commit()
        
        # Перерахувати прогрес проєкту якщо є
        task = await get_task_by_id(task_id, user_id)
        if task and task.get('goal_id'):
            await recalculate_project_progress(task['goal_id'], user_id)
        
        return cursor.rowcount > 0
    finally:
        await db.close()


async def uncomplete_task(task_id: int, user_id: int) -> bool:
    """Скасувати виконання задачі."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            UPDATE tasks 
            SET is_completed = 0, completed_at = NULL
            WHERE id = ? AND user_id = ?
            """,
            (task_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def update_task(task_id: int, user_id: int, **kwargs) -> bool:
    """Оновити поля задачі."""
    if not kwargs:
        return False
    
    fields = ", ".join(f"{key} = ?" for key in kwargs.keys())
    values = list(kwargs.values()) + [task_id, user_id]
    
    db = await get_db()
    try:
        cursor = await db.execute(
            f"UPDATE tasks SET {fields} WHERE id = ? AND user_id = ?",
            values
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def delete_task(task_id: int, user_id: int) -> bool:
    """Видалити задачу."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                         RECURRING TASKS                                      ║
# ╚════════════════════════════════════════════════════════════════════════════╝

async def get_recurring_tasks(user_id: int) -> List[Dict[str, Any]]:
    """Отримати всі recurring задачі."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT t.*, g.title as goal_title
            FROM tasks t
            LEFT JOIN goals g ON t.goal_id = g.id
            WHERE t.user_id = ? AND t.is_recurring = 1
            ORDER BY t.scheduled_time ASC
            """,
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_recurring_tasks_for_weekday(user_id: int, weekday: int) -> List[Dict[str, Any]]:
    """
    Отримати recurring задачі для конкретного дня тижня.
    weekday: 1=Пн, 7=Нд (ISO)
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT t.*, g.title as goal_title
            FROM tasks t
            LEFT JOIN goals g ON t.goal_id = g.id
            WHERE t.user_id = ? 
              AND t.is_recurring = 1
              AND (
                  t.recurrence_rule = 'daily'
                  OR (t.recurrence_rule = 'weekdays' AND ? BETWEEN 1 AND 5)
                  OR (t.recurrence_rule = 'custom' AND t.recurrence_days LIKE '%' || ? || '%')
              )
            ORDER BY t.scheduled_time ASC
            """,
            (user_id, weekday, str(weekday))
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                         TASK OCCURRENCES                                     ║
# ╚════════════════════════════════════════════════════════════════════════════╝

async def get_or_create_occurrence(task_id: int, user_id: int, for_date: date = None) -> Dict[str, Any]:
    """
    Отримати або створити occurrence для recurring task на дату.
    Автоматично рахує occurrence_number.
    """
    for_date = for_date or date.today()
    date_str = for_date.isoformat()
    
    db = await get_db()
    try:
        # Спробуємо отримати існуючий
        cursor = await db.execute(
            "SELECT * FROM task_occurrences WHERE task_id = ? AND date = ?",
            (task_id, date_str)
        )
        row = await cursor.fetchone()
        
        if row:
            return dict(row)
        
        # Створюємо новий
        # Рахуємо номер входження
        cursor = await db.execute(
            "SELECT COUNT(*) FROM task_occurrences WHERE task_id = ?",
            (task_id,)
        )
        count = (await cursor.fetchone())[0]
        occurrence_number = count + 1
        
        cursor = await db.execute(
            """
            INSERT INTO task_occurrences (task_id, user_id, date, occurrence_number, status)
            VALUES (?, ?, ?, ?, 'pending')
            """,
            (task_id, user_id, date_str, occurrence_number)
        )
        await db.commit()
        
        return {
            'id': cursor.lastrowid,
            'task_id': task_id,
            'user_id': user_id,
            'date': date_str,
            'occurrence_number': occurrence_number,
            'status': 'pending',
            'notes': None,
            'completed_at': None
        }
    finally:
        await db.close()


async def complete_occurrence(task_id: int, user_id: int, for_date: date = None) -> bool:
    """Позначити occurrence як виконане."""
    for_date = for_date or date.today()
    date_str = for_date.isoformat()
    
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            UPDATE task_occurrences 
            SET status = 'done', completed_at = ?
            WHERE task_id = ? AND user_id = ? AND date = ?
            """,
            (datetime.now().isoformat(), task_id, user_id, date_str)
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def skip_occurrence(task_id: int, user_id: int, for_date: date = None, notes: str = None) -> bool:
    """Пропустити occurrence (звільняє слот часу)."""
    for_date = for_date or date.today()
    date_str = for_date.isoformat()
    
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            UPDATE task_occurrences 
            SET status = 'skipped', notes = ?
            WHERE task_id = ? AND user_id = ? AND date = ?
            """,
            (notes, task_id, user_id, date_str)
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def unskip_occurrence(task_id: int, user_id: int, for_date: date = None) -> bool:
    """Скасувати пропуск occurrence."""
    for_date = for_date or date.today()
    date_str = for_date.isoformat()
    
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            UPDATE task_occurrences 
            SET status = 'pending', notes = NULL
            WHERE task_id = ? AND user_id = ? AND date = ?
            """,
            (task_id, user_id, date_str)
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def get_task_occurrence_stats(task_id: int) -> Dict[str, Any]:
    """Статистика по recurring task."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as done,
                SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped
            FROM task_occurrences WHERE task_id = ?
            """,
            (task_id,)
        )
        row = await cursor.fetchone()
        total = row['total'] or 0
        done = row['done'] or 0
        
        return {
            'total': total,
            'done': done,
            'skipped': row['skipped'] or 0,
            'success_rate': int(done / total * 100) if total > 0 else 0
        }
    finally:
        await db.close()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                               GOALS                                          ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def _parse_goal(row) -> Dict[str, Any]:
    """Парсинг рядка цілі з JSON полями."""
    goal = dict(row)
    try:
        goal['domain_tags'] = json.loads(goal.get('domain_tags') or '[]')
    except:
        goal['domain_tags'] = []
    return goal


async def create_goal(
    user_id: int,
    title: str,
    goal_type: str,
    description: str = None,
    parent_id: int = None,
    deadline: str = None,
    domain_tags: List[str] = None,
    # Habit fields
    frequency: str = None,
    schedule_days: str = None,
    reminder_time: str = None,
    duration_minutes: int = None,
    # Target fields
    target_value: float = None,
    unit: str = None,
    # Metric fields
    target_min: float = None,
    target_max: float = None,
) -> int:
    """Створити ціль."""
    db = await get_db()
    try:
        tags_json = json.dumps(domain_tags or [])
        cursor = await db.execute(
            """
            INSERT INTO goals (
                user_id, title, description, goal_type, parent_id, deadline,
                domain_tags, frequency, schedule_days, reminder_time, duration_minutes,
                target_value, unit, target_min, target_max
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, title, description, goal_type, parent_id, deadline,
             tags_json, frequency, schedule_days, reminder_time, duration_minutes,
             target_value, unit, target_min, target_max)
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_goal_by_id(goal_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Отримати ціль за ID."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM goals WHERE id = ? AND user_id = ?",
            (goal_id, user_id)
        )
        row = await cursor.fetchone()
        return _parse_goal(row) if row else None
    finally:
        await db.close()


async def get_goals_by_type(user_id: int, goal_type: str, status: str = 'active') -> List[Dict[str, Any]]:
    """Отримати цілі за типом."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM goals 
            WHERE user_id = ? AND goal_type = ? AND status = ?
            ORDER BY created_at DESC
            """,
            (user_id, goal_type, status)
        )
        rows = await cursor.fetchall()
        return [_parse_goal(row) for row in rows]
    finally:
        await db.close()


async def get_all_goals(user_id: int, status: str = None) -> List[Dict[str, Any]]:
    """Отримати всі цілі."""
    db = await get_db()
    try:
        if status:
            cursor = await db.execute(
                """
                SELECT * FROM goals 
                WHERE user_id = ? AND status = ?
                ORDER BY goal_type, created_at DESC
                """,
                (user_id, status)
            )
        else:
            cursor = await db.execute(
                """
                SELECT * FROM goals 
                WHERE user_id = ?
                ORDER BY status, goal_type, created_at DESC
                """,
                (user_id,)
            )
        rows = await cursor.fetchall()
        return [_parse_goal(row) for row in rows]
    finally:
        await db.close()


async def get_projects(user_id: int, status: str = 'active') -> List[Dict[str, Any]]:
    """Отримати проєкти для вибору батьківської цілі."""
    return await get_goals_by_type(user_id, 'project', status)


async def get_child_goals(parent_id: int, user_id: int) -> List[Dict[str, Any]]:
    """Отримати дочірні цілі проєкту."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM goals 
            WHERE user_id = ? AND parent_id = ?
            ORDER BY goal_type, created_at DESC
            """,
            (user_id, parent_id)
        )
        rows = await cursor.fetchall()
        return [_parse_goal(row) for row in rows]
    finally:
        await db.close()


async def update_goal(goal_id: int, user_id: int, **kwargs) -> bool:
    """Оновити поля цілі."""
    if not kwargs:
        return False
    
    if 'domain_tags' in kwargs and isinstance(kwargs['domain_tags'], list):
        kwargs['domain_tags'] = json.dumps(kwargs['domain_tags'])
    
    fields = ", ".join(f"{key} = ?" for key in kwargs.keys())
    values = list(kwargs.values()) + [goal_id, user_id]
    
    db = await get_db()
    try:
        cursor = await db.execute(
            f"UPDATE goals SET {fields} WHERE id = ? AND user_id = ?",
            values
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def complete_goal(goal_id: int, user_id: int) -> bool:
    """Завершити ціль."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            UPDATE goals 
            SET status = 'completed', progress = 100, completed_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (datetime.now().isoformat(), goal_id, user_id)
        )
        await db.commit()
        
        # Перерахувати прогрес батьківського проєкту
        goal = await get_goal_by_id(goal_id, user_id)
        if goal and goal.get('parent_id'):
            await recalculate_project_progress(goal['parent_id'], user_id)
        
        return cursor.rowcount > 0
    finally:
        await db.close()


async def restore_goal(goal_id: int, user_id: int) -> bool:
    """Повернути ціль в активні."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            UPDATE goals 
            SET status = 'active', completed_at = NULL
            WHERE id = ? AND user_id = ?
            """,
            (goal_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def delete_goal(goal_id: int, user_id: int) -> bool:
    """Видалити ціль."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "DELETE FROM goals WHERE id = ? AND user_id = ?",
            (goal_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                            PROJECT PROGRESS                                  ║
# ╚════════════════════════════════════════════════════════════════════════════╝

async def recalculate_project_progress(project_id: int, user_id: int) -> int:
    """
    Перераховує прогрес Project на основі:
    1. Дочірніх цілей (habit, target, metric)
    2. Прив'язаних задач
    """
    db = await get_db()
    try:
        # Дочірні цілі
        cursor = await db.execute(
            """
            SELECT progress, status FROM goals 
            WHERE parent_id = ? AND user_id = ?
            """,
            (project_id, user_id)
        )
        children = await cursor.fetchall()
        
        # Пов'язані задачі
        cursor = await db.execute(
            """
            SELECT is_completed FROM tasks 
            WHERE goal_id = ? AND user_id = ? AND is_recurring = 0
            """,
            (project_id, user_id)
        )
        tasks = await cursor.fetchall()
        
        total_items = len(children) + len(tasks)
        if total_items == 0:
            return 0
        
        total_progress = 0
        
        for child in children:
            if child['status'] == 'completed':
                total_progress += 100
            else:
                total_progress += (child['progress'] or 0)
        
        for task in tasks:
            if task['is_completed']:
                total_progress += 100
        
        avg_progress = int(total_progress / total_items)
        
        await db.execute(
            "UPDATE goals SET progress = ? WHERE id = ?",
            (avg_progress, project_id)
        )
        await db.commit()
        
        return avg_progress
    finally:
        await db.close()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                              HABITS                                          ║
# ╚════════════════════════════════════════════════════════════════════════════╝

async def get_habits_today(user_id: int) -> List[Dict[str, Any]]:
    """Отримати звички на сьогодні з їх статусом."""
    db = await get_db()
    try:
        today = date.today()
        weekday = today.isoweekday()
        today_iso = today.isoformat()
        
        cursor = await db.execute(
            """
            SELECT g.*, hl.status as today_status
            FROM goals g
            LEFT JOIN habit_logs hl ON g.id = hl.goal_id AND hl.date = ?
            WHERE g.user_id = ? 
              AND g.goal_type = 'habit' 
              AND g.status = 'active'
              AND (
                  g.frequency = 'daily'
                  OR (g.frequency = 'weekdays' AND ? BETWEEN 1 AND 5)
                  OR g.schedule_days LIKE '%' || ? || '%'
                  OR g.schedule_days IS NULL
              )
            ORDER BY g.reminder_time, g.title
            """,
            (today_iso, user_id, weekday, str(weekday))
        )
        rows = await cursor.fetchall()
        return [_parse_goal(row) for row in rows]
    finally:
        await db.close()


async def log_habit(goal_id: int, user_id: int, status: str, notes: str = None) -> int:
    """Залогувати виконання звички та оновити streak."""
    db = await get_db()
    try:
        today = date.today().isoformat()
        
        # Upsert log
        cursor = await db.execute(
            """
            INSERT INTO habit_logs (goal_id, user_id, date, status, notes)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(goal_id, date) DO UPDATE SET status = ?, notes = ?
            """,
            (goal_id, user_id, today, status, notes, status, notes)
        )
        await db.commit()
        
        # Перерахувати streak
        await _update_habit_streak(goal_id, user_id)
        
        return cursor.lastrowid
    finally:
        await db.close()


async def _update_habit_streak(goal_id: int, user_id: int) -> None:
    """
    ВИПРАВЛЕНИЙ алгоритм розрахунку streak.
    Streak обривається якщо є gap (день без логу).
    """
    db = await get_db()
    try:
        # Отримуємо логи в хронологічному порядку (від нових до старих)
        cursor = await db.execute(
            """
            SELECT date, status FROM habit_logs 
            WHERE goal_id = ? 
            ORDER BY date DESC 
            LIMIT 365
            """,
            (goal_id,)
        )
        logs = await cursor.fetchall()
        
        if not logs:
            await db.execute(
                "UPDATE goals SET current_streak = 0 WHERE id = ?",
                (goal_id,)
            )
            await db.commit()
            return
        
        # Рахуємо streak
        current_streak = 0
        check_date = date.today()
        
        for log in logs:
            log_date = date.fromisoformat(log['date'])
            
            if log_date == check_date:
                # Дата співпадає
                if log['status'] in ('done', 'skipped'):
                    current_streak += 1
                    check_date -= timedelta(days=1)
                else:  # missed
                    break
            elif log_date < check_date:
                # Gap — є пропущені дні без логу
                break
            # Якщо log_date > check_date — ігноруємо (майбутні дати)
        
        # Оновлюємо streak
        cursor = await db.execute(
            "SELECT longest_streak FROM goals WHERE id = ?",
            (goal_id,)
        )
        row = await cursor.fetchone()
        longest = row['longest_streak'] if row else 0
        new_longest = max(longest, current_streak)
        
        await db.execute(
            "UPDATE goals SET current_streak = ?, longest_streak = ? WHERE id = ?",
            (current_streak, new_longest, goal_id)
        )
        await db.commit()
        
        # Якщо звичка належить проєкту — оновити прогрес
        goal = await get_goal_by_id(goal_id, user_id)
        if goal and goal.get('parent_id'):
            await recalculate_project_progress(goal['parent_id'], user_id)
            
    finally:
        await db.close()


async def get_habit_logs(goal_id: int, user_id: int, days: int = 30) -> List[Dict[str, Any]]:
    """Отримати логи звички за останні N днів."""
    db = await get_db()
    try:
        since_date = (date.today() - timedelta(days=days)).isoformat()
        cursor = await db.execute(
            """
            SELECT * FROM habit_logs 
            WHERE goal_id = ? AND user_id = ? AND date >= ?
            ORDER BY date DESC
            """,
            (goal_id, user_id, since_date)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_habit_stats(goal_id: int, user_id: int) -> Dict[str, Any]:
    """Статистика звички."""
    db = await get_db()
    try:
        # Цього місяця
        month_start = date.today().replace(day=1).isoformat()
        cursor = await db.execute(
            """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as done,
                SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped
            FROM habit_logs 
            WHERE goal_id = ? AND date >= ?
            """,
            (goal_id, month_start)
        )
        month = await cursor.fetchone()
        
        # Всього
        cursor = await db.execute(
            """
            SELECT COUNT(*) as total
            FROM habit_logs 
            WHERE goal_id = ? AND status = 'done'
            """,
            (goal_id,)
        )
        total = await cursor.fetchone()
        
        month_total = month['total'] or 0
        month_done = month['done'] or 0
        
        return {
            'month_total': month_total,
            'month_done': month_done,
            'month_rate': int(month_done / month_total * 100) if month_total > 0 else 0,
            'total_done': total['total'] or 0
        }
    finally:
        await db.close()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                            GOAL ENTRIES                                      ║
# ╚════════════════════════════════════════════════════════════════════════════╝

async def add_goal_entry(goal_id: int, user_id: int, value: float, notes: str = None) -> int:
    """Додати запис для Target/Metric."""
    db = await get_db()
    try:
        today = date.today().isoformat()
        cursor = await db.execute(
            """
            INSERT INTO goal_entries (goal_id, user_id, date, value, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (goal_id, user_id, today, value, notes)
        )
        await db.commit()
        
        # Оновити current_value та progress для Target
        await _update_target_progress(goal_id, user_id)
        
        return cursor.lastrowid
    finally:
        await db.close()


async def _update_target_progress(goal_id: int, user_id: int) -> None:
    """Оновлює прогрес Target цілі."""
    db = await get_db()
    try:
        goal = await get_goal_by_id(goal_id, user_id)
        
        if not goal or goal['goal_type'] != 'target' or not goal.get('target_value'):
            return
        
        cursor = await db.execute(
            "SELECT SUM(value) as total FROM goal_entries WHERE goal_id = ?",
            (goal_id,)
        )
        row = await cursor.fetchone()
        total = row['total'] or 0
        
        progress = min(100, int((total / goal['target_value']) * 100))
        
        await db.execute(
            "UPDATE goals SET current_value = ?, progress = ? WHERE id = ?",
            (total, progress, goal_id)
        )
        await db.commit()
        
        # Якщо належить проєкту — оновити його прогрес
        if goal.get('parent_id'):
            await recalculate_project_progress(goal['parent_id'], user_id)
            
    finally:
        await db.close()


async def get_goal_entries(goal_id: int, user_id: int, days: int = 30) -> List[Dict[str, Any]]:
    """Отримати записи цілі за останні N днів."""
    db = await get_db()
    try:
        since_date = (date.today() - timedelta(days=days)).isoformat()
        cursor = await db.execute(
            """
            SELECT * FROM goal_entries 
            WHERE goal_id = ? AND user_id = ? AND date >= ?
            ORDER BY date DESC
            """,
            (goal_id, user_id, since_date)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                              STATISTICS                                      ║
# ╚════════════════════════════════════════════════════════════════════════════╝

async def get_tasks_stats(user_id: int) -> Dict[str, Any]:
    """Статистика задач."""
    today = date.today().isoformat()
    
    db = await get_db()
    try:
        # Активні
        cursor = await db.execute(
            "SELECT COUNT(*) FROM tasks WHERE user_id = ? AND is_completed = 0 AND is_recurring = 0",
            (user_id,)
        )
        active = (await cursor.fetchone())[0]
        
        # Виконано сьогодні
        cursor = await db.execute(
            """
            SELECT COUNT(*) FROM tasks 
            WHERE user_id = ? AND is_completed = 1 AND DATE(completed_at) = ?
            """,
            (user_id, today)
        )
        completed_today = (await cursor.fetchone())[0]
        
        # Прострочені
        cursor = await db.execute(
            """
            SELECT COUNT(*) FROM tasks 
            WHERE user_id = ? AND is_completed = 0 AND is_recurring = 0
              AND deadline IS NOT NULL AND DATE(deadline) < ?
            """,
            (user_id, today)
        )
        overdue = (await cursor.fetchone())[0]
        
        return {
            'active': active,
            'completed_today': completed_today,
            'overdue': overdue
        }
    finally:
        await db.close()


async def get_goals_stats(user_id: int) -> Dict[str, Any]:
    """Статистика цілей."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT 
                goal_type,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM goals WHERE user_id = ? GROUP BY goal_type
            """,
            (user_id,)
        )
        rows = await cursor.fetchall()
        
        stats = {'by_type': {}, 'total': 0, 'active': 0, 'completed': 0}
        for row in rows:
            stats['by_type'][row['goal_type']] = dict(row)
            stats['total'] += row['total']
            stats['active'] += row['active']
            stats['completed'] += row['completed']
        
        return stats
    finally:
        await db.close()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                           TODAY SCHEDULE                                     ║
# ╚════════════════════════════════════════════════════════════════════════════╝

async def get_today_schedule(user_id: int) -> Dict[str, Any]:
    """
    Повний розклад на сьогодні:
    - recurring_tasks (з occurrences)
    - one_time_tasks
    - habits
    - timeline (все з часом, відсортоване)
    """
    today = date.today()
    weekday = today.isoweekday()
    
    schedule = {
        'date': today.isoformat(),
        'weekday': weekday,
        'recurring_tasks': [],
        'one_time_tasks': [],
        'habits': [],
        'timeline': []
    }
    
    # 1. Recurring tasks
    recurring = await get_recurring_tasks_for_weekday(user_id, weekday)
    for task in recurring:
        occ = await get_or_create_occurrence(task['id'], user_id, today)
        schedule['recurring_tasks'].append({
            **task,
            'occurrence': occ
        })
    
    # 2. One-time tasks
    schedule['one_time_tasks'] = await get_tasks_today(user_id)
    
    # 3. Habits
    schedule['habits'] = await get_habits_today(user_id)
    
    # 4. Build timeline
    timeline = []
    
    # Recurring (не skipped)
    for item in schedule['recurring_tasks']:
        if item['occurrence']['status'] != 'skipped' and item.get('scheduled_time'):
            timeline.append({
                'type': 'recurring_task',
                'id': item['id'],
                'title': item['title'],
                'time': item['scheduled_time'],
                'end_time': item.get('scheduled_end'),
                'occurrence': item['occurrence'],
                'is_fixed': item['is_fixed'],
            })
    
    # One-time tasks з часом
    for task in schedule['one_time_tasks']:
        if task.get('scheduled_time'):
            timeline.append({
                'type': 'task',
                'id': task['id'],
                'title': task['title'],
                'time': task['scheduled_time'],
                'priority': task['priority'],
                'goal_title': task.get('goal_title'),
            })
    
    # Habits з часом
    for habit in schedule['habits']:
        if habit.get('reminder_time'):
            timeline.append({
                'type': 'habit',
                'id': habit['id'],
                'title': habit['title'],
                'time': habit['reminder_time'],
                'duration': habit.get('duration_minutes'),
                'streak': habit.get('current_streak', 0),
                'today_status': habit.get('today_status'),
            })
    
    # Сортуємо по часу
    timeline.sort(key=lambda x: x.get('time', '99:99'))
    schedule['timeline'] = timeline
    
    return schedule
