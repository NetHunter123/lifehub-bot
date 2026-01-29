"""
SQL запити для роботи з даними.
"""

import aiosqlite
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from bot.config import config


async def get_db() -> aiosqlite.Connection:
    """Отримати з'єднання з БД."""
    db = await aiosqlite.connect(config.DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    return db


# ============== USER SETTINGS ==============

async def get_user_language(user_id: int) -> str:
    """Отримати мову користувача."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT language FROM user_settings WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 'en'
    finally:
        await db.close()


async def update_user_language(user_id: int, language: str) -> None:
    """Оновити мову користувача."""
    db = await get_db()
    try:
        await db.execute(
            """
            INSERT INTO user_settings (user_id, language) 
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET language = ?
            """,
            (user_id, language, language)
        )
        await db.commit()
    finally:
        await db.close()


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


async def create_user_settings(user_id: int, language: str = 'en') -> None:
    """Створити налаштування користувача."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR IGNORE INTO user_settings (user_id, language) VALUES (?, ?)",
            (user_id, language)
        )
        await db.commit()
    finally:
        await db.close()


# ============== TASKS CRUD ==============

async def create_task(
    user_id: int,
    title: str,
    description: Optional[str] = None,
    priority: int = 2,
    deadline: Optional[str] = None,
    scheduled_start: Optional[str] = None,
    estimated_duration: Optional[int] = None,
    goal_id: Optional[int] = None,
) -> int:
    """Створити нову задачу. Повертає ID."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            INSERT INTO tasks (
                user_id, title, description, priority, deadline,
                scheduled_start, estimated_duration, goal_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, title, description, priority, deadline,
             scheduled_start, estimated_duration, goal_id)
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
            "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def get_tasks_today(user_id: int) -> List[Dict[str, Any]]:
    """Отримати задачі на сьогодні."""
    today = date.today().isoformat()
    
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM tasks 
            WHERE user_id = ? 
              AND is_completed = 0
              AND (
                  deadline IS NULL 
                  OR date(deadline) <= ?
              )
            ORDER BY priority ASC, deadline ASC
            """,
            (user_id, today)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_tasks_inbox(user_id: int) -> List[Dict[str, Any]]:
    """Отримати необроблені задачі (inbox)."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM tasks 
            WHERE user_id = ? 
              AND is_completed = 0
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


async def get_all_tasks(user_id: int, include_completed: bool = False) -> List[Dict[str, Any]]:
    """Отримати всі задачі користувача."""
    db = await get_db()
    try:
        query = "SELECT * FROM tasks WHERE user_id = ?"
        if not include_completed:
            query += " AND is_completed = 0"
        query += " ORDER BY priority ASC, deadline ASC"
        
        cursor = await db.execute(query, (user_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def complete_task(task_id: int, user_id: int) -> bool:
    """Позначити задачу виконаною."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            UPDATE tasks 
            SET is_completed = 1, completed_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (datetime.now().isoformat(), task_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def uncomplete_task(task_id: int, user_id: int) -> bool:
    """Зняти позначку виконання."""
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


async def get_tasks_stats(user_id: int) -> Dict[str, Any]:
    """Отримати статистику задач."""
    today = date.today().isoformat()
    
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM tasks WHERE user_id = ? AND is_completed = 0",
            (user_id,)
        )
        total = (await cursor.fetchone())[0]
        
        cursor = await db.execute(
            """
            SELECT COUNT(*) FROM tasks 
            WHERE user_id = ? AND is_completed = 1 
              AND date(completed_at) = ?
            """,
            (user_id, today)
        )
        completed_today = (await cursor.fetchone())[0]
        
        cursor = await db.execute(
            """
            SELECT COUNT(*) FROM tasks 
            WHERE user_id = ? AND is_completed = 0 
              AND deadline IS NOT NULL AND date(deadline) < ?
            """,
            (user_id, today)
        )
        overdue = (await cursor.fetchone())[0]
        
        return {
            "total": total,
            "completed_today": completed_today,
            "overdue": overdue
        }
    finally:
        await db.close()


async def get_completed_tasks_recent(user_id: int, days: int = 2) -> List[Dict[str, Any]]:
    """Отримати виконані задачі за останні N днів (для скасування)."""
    since_date = (date.today() - timedelta(days=days)).isoformat()
    
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM tasks 
            WHERE user_id = ? 
              AND is_completed = 1
              AND date(completed_at) >= ?
            ORDER BY completed_at DESC
            """,
            (user_id, since_date)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_completed_tasks(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Отримати всі виконані задачі (історія)."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM tasks 
            WHERE user_id = ? 
              AND is_completed = 1
            ORDER BY completed_at DESC
            LIMIT ?
            """,
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_tasks_history(user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """Отримати історію задач (виконані, без активних)."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM tasks 
            WHERE user_id = ?
              AND is_completed = 1
            ORDER BY completed_at DESC
            LIMIT ?
            """,
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


# ============== ЦІЛІ ==============

async def create_goal(
    user_id: int,
    title: str,
    goal_type: str,
    description: str = None,
    parent_id: int = None,
    deadline: str = None
) -> int:
    """Створити нову ціль. Повертає ID створеної цілі."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            INSERT INTO goals (user_id, title, description, goal_type, parent_id, deadline)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, title, description, goal_type, parent_id, deadline)
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_goal_by_id(goal_id: int, user_id: int) -> Dict[str, Any] | None:
    """Отримати ціль за ID."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM goals WHERE id = ? AND user_id = ?",
            (goal_id, user_id)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def get_goals_active(user_id: int) -> List[Dict[str, Any]]:
    """Отримати активні цілі користувача."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM goals 
            WHERE user_id = ? AND status = 'active'
            ORDER BY 
                CASE goal_type 
                    WHEN 'yearly' THEN 1 
                    WHEN 'quarterly' THEN 2 
                    WHEN 'monthly' THEN 3 
                    WHEN 'weekly' THEN 4 
                END,
                created_at DESC
            """,
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_goals_completed(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Отримати завершені цілі."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM goals 
            WHERE user_id = ? AND status = 'completed'
            ORDER BY completed_at DESC
            LIMIT ?
            """,
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_goals_all(user_id: int) -> List[Dict[str, Any]]:
    """Отримати всі цілі користувача."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM goals 
            WHERE user_id = ?
            ORDER BY 
                status ASC,
                CASE goal_type 
                    WHEN 'yearly' THEN 1 
                    WHEN 'quarterly' THEN 2 
                    WHEN 'monthly' THEN 3 
                    WHEN 'weekly' THEN 4 
                END,
                created_at DESC
            """,
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_goals_by_type(user_id: int, goal_type: str) -> List[Dict[str, Any]]:
    """Отримати цілі за типом."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM goals 
            WHERE user_id = ? AND goal_type = ? AND status = 'active'
            ORDER BY created_at DESC
            """,
            (user_id, goal_type)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_parent_goals(user_id: int) -> List[Dict[str, Any]]:
    """Отримати цілі, які можуть бути батьківськими (yearly, quarterly, monthly)."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM goals 
            WHERE user_id = ? 
              AND status = 'active'
              AND goal_type IN ('yearly', 'quarterly', 'monthly')
            ORDER BY 
                CASE goal_type 
                    WHEN 'yearly' THEN 1 
                    WHEN 'quarterly' THEN 2 
                    WHEN 'monthly' THEN 3 
                END,
                created_at DESC
            """,
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def update_goal(goal_id: int, user_id: int, **kwargs) -> bool:
    """Оновити поля цілі."""
    if not kwargs:
        return False
    
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


async def update_goal_progress(goal_id: int, user_id: int, progress: int) -> bool:
    """Оновити прогрес цілі."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "UPDATE goals SET progress = ? WHERE id = ? AND user_id = ?",
            (progress, goal_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def complete_goal(goal_id: int, user_id: int) -> bool:
    """Позначити ціль як завершену."""
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


async def get_child_goals(goal_id: int, user_id: int) -> List[Dict[str, Any]]:
    """Отримати дочірні цілі."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM goals 
            WHERE user_id = ? AND parent_id = ?
            ORDER BY created_at DESC
            """,
            (user_id, goal_id)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_goal_tasks(goal_id: int, user_id: int) -> List[Dict[str, Any]]:
    """Отримати задачі, пов'язані з ціллю."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM tasks 
            WHERE user_id = ? AND goal_id = ?
            ORDER BY is_completed ASC, deadline ASC
            """,
            (user_id, goal_id)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_goals_stats(user_id: int) -> Dict[str, Any]:
    """Отримати статистику по цілях."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                AVG(CASE WHEN status = 'active' THEN progress ELSE NULL END) as avg_progress
            FROM goals WHERE user_id = ?
            """,
            (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else {"total": 0, "active": 0, "completed": 0, "avg_progress": 0}
    finally:
        await db.close()
