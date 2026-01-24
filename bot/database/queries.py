"""
SQL запити для роботи з задачами.
"""

import aiosqlite
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from bot.config import config


def get_db():
    """Отримати з'єднання з БД."""
    db = aiosqlite.connect(config.DATABASE_PATH)
    return db


# ============== TASKS CRUD ==============

async def create_task(
    user_id: int,
    title: str,
    description: Optional[str] = None,
    priority: int = 2,
    deadline: Optional[datetime] = None,
    goal_id: Optional[int] = None,
    is_recurring: bool = False,
    recurrence_pattern: Optional[str] = None
) -> int:
    """Створити нову задачу. Повертає ID створеної задачі."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            INSERT INTO tasks (
                user_id, title, description, priority, deadline,
                goal_id, is_recurring, recurrence_pattern
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, title, description, priority, deadline,
             goal_id, is_recurring, recurrence_pattern)
        )
        await db.commit()
        return cursor.lastrowid


async def get_task_by_id(task_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Отримати задачу за ID."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_tasks_today(user_id: int) -> List[Dict[str, Any]]:
    """Отримати задачі на сьогодні."""
    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    
    async with get_db() as db:
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
    async with get_db() as db:
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
    async with get_db() as db:
        query = "SELECT * FROM tasks WHERE user_id = ?"
        if not include_completed:
            query += " AND is_completed = 0"
        query += " ORDER BY priority ASC, deadline ASC"
        
        cursor = await db.execute(query, (user_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def complete_task(task_id: int, user_id: int) -> bool:
    """Позначити задачу виконаною."""
    async with get_db() as db:
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
    async with get_db() as db:
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
    async with get_db() as db:
        cursor = await db.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0


async def update_task(
    task_id: int,
    user_id: int,
    **kwargs
) -> bool:
    """Оновити поля задачі."""
    if not kwargs:
        return False
    
    # Формуємо SQL динамічно
    fields = ", ".join(f"{key} = ?" for key in kwargs.keys())
    values = list(kwargs.values()) + [task_id, user_id]
    
    async with get_db() as db:
        cursor = await db.execute(
            f"UPDATE tasks SET {fields} WHERE id = ? AND user_id = ?",
            values
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_tasks_stats(user_id: int) -> Dict[str, Any]:
    """Отримати статистику задач."""
    today = date.today().isoformat()
    
    async with get_db() as db:
        # Всього задач
        cursor = await db.execute(
            "SELECT COUNT(*) FROM tasks WHERE user_id = ? AND is_completed = 0",
            (user_id,)
        )
        total = (await cursor.fetchone())[0]
        
        # Виконано сьогодні
        cursor = await db.execute(
            """
            SELECT COUNT(*) FROM tasks 
            WHERE user_id = ? AND is_completed = 1 
              AND date(completed_at) = ?
            """,
            (user_id, today)
        )
        completed_today = (await cursor.fetchone())[0]
        
        # Прострочені
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
