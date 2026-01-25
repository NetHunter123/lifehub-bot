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
    async with await get_db() as db:
        cursor = await db.execute(
            "SELECT language FROM user_settings WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 'en'


async def update_user_language(user_id: int, language: str) -> None:
    """Оновити мову користувача."""
    async with await get_db() as db:
        await db.execute(
            """
            INSERT INTO user_settings (user_id, language) 
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET language = ?
            """,
            (user_id, language, language)
        )
        await db.commit()


async def get_user_settings(user_id: int) -> Optional[Dict[str, Any]]:
    """Отримати налаштування користувача."""
    async with await get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM user_settings WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def create_user_settings(user_id: int, language: str = 'en') -> None:
    """Створити налаштування користувача."""
    async with await get_db() as db:
        await db.execute(
            "INSERT OR IGNORE INTO user_settings (user_id, language) VALUES (?, ?)",
            (user_id, language)
        )
        await db.commit()


# ============== TASKS CRUD ==============

async def create_task(
    user_id: int,
    title: str,
    description: Optional[str] = None,
    priority: int = 2,
    deadline: Optional[datetime] = None,
    scheduled_start: Optional[datetime] = None,
    estimated_duration: Optional[int] = None,
    travel_time_before: int = 0,
    location: Optional[str] = None,
    goal_id: Optional[int] = None,
    is_recurring: bool = False,
    recurrence_pattern: Optional[str] = None
) -> int:
    """Створити нову задачу. Повертає ID."""
    async with await get_db() as db:
        cursor = await db.execute(
            """
            INSERT INTO tasks (
                user_id, title, description, priority, deadline,
                scheduled_start, estimated_duration, travel_time_before,
                location, goal_id, is_recurring, recurrence_pattern
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, title, description, priority, deadline,
             scheduled_start, estimated_duration, travel_time_before,
             location, goal_id, is_recurring, recurrence_pattern)
        )
        await db.commit()
        return cursor.lastrowid


async def get_task_by_id(task_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Отримати задачу за ID."""
    async with await get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_tasks_today(user_id: int) -> List[Dict[str, Any]]:
    """Отримати задачі на сьогодні."""
    today = date.today().isoformat()
    
    async with await get_db() as db:
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


async def get_tasks_inbox(user_id: int) -> List[Dict[str, Any]]:
    """Отримати необроблені задачі (inbox)."""
    async with await get_db() as db:
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


async def get_all_tasks(user_id: int, include_completed: bool = False) -> List[Dict[str, Any]]:
    """Отримати всі задачі користувача."""
    async with await get_db() as db:
        query = "SELECT * FROM tasks WHERE user_id = ?"
        if not include_completed:
            query += " AND is_completed = 0"
        query += " ORDER BY priority ASC, deadline ASC"
        
        cursor = await db.execute(query, (user_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def complete_task(task_id: int, user_id: int) -> bool:
    """Позначити задачу виконаною."""
    async with await get_db() as db:
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


async def uncomplete_task(task_id: int, user_id: int) -> bool:
    """Зняти позначку виконання."""
    async with await get_db() as db:
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


async def delete_task(task_id: int, user_id: int) -> bool:
    """Видалити задачу."""
    async with await get_db() as db:
        cursor = await db.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0


async def update_task(task_id: int, user_id: int, **kwargs) -> bool:
    """Оновити поля задачі."""
    if not kwargs:
        return False
    
    fields = ", ".join(f"{key} = ?" for key in kwargs.keys())
    values = list(kwargs.values()) + [task_id, user_id]
    
    async with await get_db() as db:
        cursor = await db.execute(
            f"UPDATE tasks SET {fields} WHERE id = ? AND user_id = ?",
            values
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_tasks_stats(user_id: int) -> Dict[str, Any]:
    """Отримати статистику задач."""
    today = date.today().isoformat()
    
    async with await get_db() as db:
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


async def get_completed_tasks_recent(user_id: int, days: int = 2) -> List[Dict[str, Any]]:
    """Отримати виконані задачі за останні N днів (для скасування)."""
    since_date = (date.today() - timedelta(days=days)).isoformat()
    
    async with await get_db() as db:
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
