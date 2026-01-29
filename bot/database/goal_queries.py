"""
SQL запити для роботи з цілями v3.
5 структурних типів: task, project, habit, target, metric.
"""

import json
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from bot.config import config
import aiosqlite


async def get_db() -> aiosqlite.Connection:
    """Отримати з'єднання з БД."""
    db = await aiosqlite.connect(config.DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    return db


# ============== GOALS CRUD ==============

async def create_goal(
    user_id: int,
    title: str,
    goal_type: str,
    description: str = None,
    parent_id: int = None,
    deadline: str = None,
    domain_tags: List[str] = None,
    frequency: str = None,
    schedule_days: str = None,
    reminder_time: str = None,
    duration_minutes: int = None,
    target_value: float = None,
    unit: str = None,
    target_min: float = None,
    target_max: float = None,
) -> int:
    """Створити нову ціль."""
    db = await get_db()
    try:
        tags_json = json.dumps(domain_tags or [])
        cursor = await db.execute(
            """
            INSERT INTO goals (
                user_id, title, description, goal_type, parent_id, 
                domain_tags, deadline, frequency, schedule_days, 
                reminder_time, duration_minutes, target_value, unit, target_min, target_max
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, title, description, goal_type, parent_id,
             tags_json, deadline, frequency, schedule_days,
             reminder_time, duration_minutes, target_value, unit, target_min, target_max)
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
        if row:
            goal = dict(row)
            goal['domain_tags'] = json.loads(goal.get('domain_tags') or '[]')
            return goal
        return None
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
    """Отримати всі цілі користувача."""
    db = await get_db()
    try:
        if status:
            cursor = await db.execute(
                "SELECT * FROM goals WHERE user_id = ? AND status = ? ORDER BY goal_type, created_at DESC",
                (user_id, status)
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM goals WHERE user_id = ? ORDER BY status, goal_type, created_at DESC",
                (user_id,)
            )
        rows = await cursor.fetchall()
        return [_parse_goal(row) for row in rows]
    finally:
        await db.close()


async def get_child_goals(parent_id: int, user_id: int) -> List[Dict[str, Any]]:
    """Отримати дочірні цілі."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM goals WHERE user_id = ? AND parent_id = ? ORDER BY goal_type, created_at DESC",
            (user_id, parent_id)
        )
        rows = await cursor.fetchall()
        return [_parse_goal(row) for row in rows]
    finally:
        await db.close()


async def get_projects(user_id: int) -> List[Dict[str, Any]]:
    """Отримати проєкти для вибору батьківської цілі."""
    return await get_goals_by_type(user_id, 'project', 'active')


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
    """Позначити ціль завершеною."""
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
        return cursor.rowcount > 0
    finally:
        await db.close()


async def restore_goal(goal_id: int, user_id: int) -> bool:
    """Повернути ціль в активні."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "UPDATE goals SET status = 'active', completed_at = NULL WHERE id = ? AND user_id = ?",
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


def _parse_goal(row) -> Dict[str, Any]:
    """Парсинг рядка в словник з JSON полями."""
    goal = dict(row)
    goal['domain_tags'] = json.loads(goal.get('domain_tags') or '[]')
    return goal


# ============== HABIT LOGS ==============

async def log_habit(goal_id: int, user_id: int, status: str, notes: str = None) -> int:
    """Залогувати виконання звички."""
    db = await get_db()
    try:
        today = date.today().isoformat()
        cursor = await db.execute(
            """
            INSERT INTO habit_logs (goal_id, user_id, date, status, notes)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(goal_id, date) DO UPDATE SET status = ?, notes = ?
            """,
            (goal_id, user_id, today, status, notes, status, notes)
        )
        await db.commit()
        await _update_habit_streak(goal_id, user_id, db)
        return cursor.lastrowid
    finally:
        await db.close()


async def _update_habit_streak(goal_id: int, user_id: int, db: aiosqlite.Connection) -> None:
    """Перераховує streak для звички."""
    cursor = await db.execute(
        "SELECT date, status FROM habit_logs WHERE goal_id = ? ORDER BY date DESC LIMIT 365",
        (goal_id,)
    )
    logs = await cursor.fetchall()
    
    if not logs:
        return
    
    current_streak = 0
    today = date.today()
    
    for log in logs:
        log_date = date.fromisoformat(log['date'])
        expected_date = today - timedelta(days=current_streak)
        
        if log_date == expected_date and log['status'] in ('done', 'skipped'):
            current_streak += 1
        elif log_date < expected_date:
            break
    
    cursor = await db.execute("SELECT longest_streak FROM goals WHERE id = ?", (goal_id,))
    row = await cursor.fetchone()
    longest = row['longest_streak'] if row else 0
    new_longest = max(longest, current_streak)
    
    await db.execute(
        "UPDATE goals SET current_streak = ?, longest_streak = ? WHERE id = ?",
        (current_streak, new_longest, goal_id)
    )
    await db.commit()


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
              AND (g.frequency = 'daily' OR g.schedule_days LIKE '%' || ? || '%' OR g.schedule_days IS NULL)
            ORDER BY g.reminder_time, g.title
            """,
            (today_iso, user_id, str(weekday))
        )
        rows = await cursor.fetchall()
        return [_parse_goal(row) for row in rows]
    finally:
        await db.close()


# ============== GOAL ENTRIES (Target/Metric) ==============

async def add_goal_entry(goal_id: int, user_id: int, value: float, notes: str = None) -> int:
    """Додати запис для Target/Metric."""
    db = await get_db()
    try:
        today = date.today().isoformat()
        cursor = await db.execute(
            "INSERT INTO goal_entries (goal_id, user_id, date, value, notes) VALUES (?, ?, ?, ?, ?)",
            (goal_id, user_id, today, value, notes)
        )
        await db.commit()
        await _update_target_progress(goal_id, db)
        return cursor.lastrowid
    finally:
        await db.close()


async def _update_target_progress(goal_id: int, db: aiosqlite.Connection) -> None:
    """Оновлює прогрес Target цілі."""
    cursor = await db.execute(
        "SELECT goal_type, target_value FROM goals WHERE id = ?",
        (goal_id,)
    )
    row = await cursor.fetchone()
    
    if not row or row['goal_type'] != 'target' or not row['target_value']:
        return
    
    cursor = await db.execute(
        "SELECT SUM(value) as total FROM goal_entries WHERE goal_id = ?",
        (goal_id,)
    )
    sum_row = await cursor.fetchone()
    total = sum_row['total'] or 0
    progress = min(100, int((total / row['target_value']) * 100))
    
    await db.execute(
        "UPDATE goals SET current_value = ?, progress = ? WHERE id = ?",
        (total, progress, goal_id)
    )
    await db.commit()


async def get_goal_entries(goal_id: int, user_id: int, days: int = 30) -> List[Dict[str, Any]]:
    """Отримати записи цілі за останні N днів."""
    db = await get_db()
    try:
        since_date = (date.today() - timedelta(days=days)).isoformat()
        cursor = await db.execute(
            "SELECT * FROM goal_entries WHERE goal_id = ? AND user_id = ? AND date >= ? ORDER BY date DESC",
            (goal_id, user_id, since_date)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


# ============== PROJECT PROGRESS ==============

async def recalculate_project_progress(goal_id: int, user_id: int) -> int:
    """Перераховує прогрес Project."""
    db = await get_db()
    try:
        # Дочірні цілі
        cursor = await db.execute(
            "SELECT progress, status FROM goals WHERE parent_id = ? AND user_id = ?",
            (goal_id, user_id)
        )
        children = await cursor.fetchall()
        
        # Пов'язані задачі
        cursor = await db.execute(
            "SELECT is_completed FROM tasks WHERE goal_id = ? AND user_id = ?",
            (goal_id, user_id)
        )
        tasks = await cursor.fetchall()
        
        if not children and not tasks:
            return 0
        
        total_items = len(children) + len(tasks)
        total_progress = 0
        
        for child in children:
            total_progress += 100 if child['status'] == 'completed' else (child['progress'] or 0)
        
        for task in tasks:
            total_progress += 100 if task['is_completed'] else 0
        
        avg_progress = int(total_progress / total_items) if total_items > 0 else 0
        
        await db.execute("UPDATE goals SET progress = ? WHERE id = ?", (avg_progress, goal_id))
        await db.commit()
        
        return avg_progress
    finally:
        await db.close()


# ============== STATISTICS ==============

async def get_goals_stats(user_id: int) -> Dict[str, Any]:
    """Статистика по цілях."""
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
