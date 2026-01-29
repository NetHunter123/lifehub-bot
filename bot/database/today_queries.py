"""
Запити для /today dashboard та time blocks.
Об'єднує tasks, habits, time_blocks в один розклад.
"""

from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional
from bot.config import config
import aiosqlite


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(config.DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    return db


# ============== TIME BLOCKS ==============

async def create_time_block(
    user_id: int,
    title: str,
    start_time: str,
    end_time: str,
    days: str,
    is_fixed: bool = True,
    is_skippable: bool = True,
) -> int:
    """Створити time block (школа, робота)."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            INSERT INTO time_blocks (user_id, title, start_time, end_time, days, is_fixed, is_skippable)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, title, start_time, end_time, days, int(is_fixed), int(is_skippable))
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_time_blocks(user_id: int) -> List[Dict[str, Any]]:
    """Отримати всі time blocks."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM time_blocks WHERE user_id = ? AND is_active = 1",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_time_blocks_for_today(user_id: int) -> List[Dict[str, Any]]:
    """Отримати time blocks на сьогодні (з урахуванням пропусків)."""
    db = await get_db()
    try:
        today = date.today()
        weekday = today.isoweekday()
        today_iso = today.isoformat()
        
        cursor = await db.execute(
            """
            SELECT tb.*, 
                   CASE WHEN tbs.id IS NOT NULL THEN 1 ELSE 0 END as is_skipped
            FROM time_blocks tb
            LEFT JOIN time_block_skips tbs ON tb.id = tbs.time_block_id AND tbs.skip_date = ?
            WHERE tb.user_id = ? 
              AND tb.is_active = 1
              AND tb.days LIKE '%' || ? || '%'
            ORDER BY tb.start_time
            """,
            (today_iso, user_id, str(weekday))
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def skip_time_block(time_block_id: int, user_id: int, skip_date: date = None) -> bool:
    """Пропустити time block на дату."""
    db = await get_db()
    try:
        skip_date = skip_date or date.today()
        await db.execute(
            """
            INSERT INTO time_block_skips (time_block_id, user_id, skip_date)
            VALUES (?, ?, ?)
            ON CONFLICT(time_block_id, skip_date) DO NOTHING
            """,
            (time_block_id, user_id, skip_date.isoformat())
        )
        await db.commit()
        return True
    finally:
        await db.close()


async def unskip_time_block(time_block_id: int, user_id: int, skip_date: date = None) -> bool:
    """Скасувати пропуск time block."""
    db = await get_db()
    try:
        skip_date = skip_date or date.today()
        cursor = await db.execute(
            "DELETE FROM time_block_skips WHERE time_block_id = ? AND user_id = ? AND skip_date = ?",
            (time_block_id, user_id, skip_date.isoformat())
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def delete_time_block(time_block_id: int, user_id: int) -> bool:
    """Видалити time block."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "DELETE FROM time_blocks WHERE id = ? AND user_id = ?",
            (time_block_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


# ============== TODAY DASHBOARD ==============

async def get_today_schedule(user_id: int) -> Dict[str, Any]:
    """
    Отримати повний розклад на сьогодні.
    Повертає: time_blocks, tasks, habits — відсортовані по часу.
    """
    db = await get_db()
    try:
        today = date.today()
        today_iso = today.isoformat()
        weekday = today.isoweekday()
        
        schedule = {
            'date': today_iso,
            'weekday': weekday,
            'time_blocks': [],
            'tasks': [],
            'habits': [],
            'timeline': []  # Об'єднаний таймлайн
        }
        
        # 1. Time blocks на сьогодні
        cursor = await db.execute(
            """
            SELECT tb.*, 
                   CASE WHEN tbs.id IS NOT NULL THEN 1 ELSE 0 END as is_skipped
            FROM time_blocks tb
            LEFT JOIN time_block_skips tbs ON tb.id = tbs.time_block_id AND tbs.skip_date = ?
            WHERE tb.user_id = ? 
              AND tb.is_active = 1
              AND tb.days LIKE '%' || ? || '%'
            ORDER BY tb.start_time
            """,
            (today_iso, user_id, str(weekday))
        )
        rows = await cursor.fetchall()
        schedule['time_blocks'] = [dict(row) for row in rows]
        
        # 2. Tasks на сьогодні (з часом або дедлайном сьогодні)
        tomorrow = (today + timedelta(days=1)).isoformat()
        cursor = await db.execute(
            """
            SELECT t.*, g.title as goal_title
            FROM tasks t
            LEFT JOIN goals g ON t.goal_id = g.id
            WHERE t.user_id = ? 
              AND t.is_completed = 0
              AND (
                  DATE(t.scheduled_start) = ?
                  OR DATE(t.deadline) = ?
                  OR (t.scheduled_start IS NULL AND t.deadline IS NULL)
              )
            ORDER BY t.is_fixed DESC, t.scheduled_start, t.priority, t.deadline
            """,
            (user_id, today_iso, today_iso)
        )
        rows = await cursor.fetchall()
        schedule['tasks'] = [dict(row) for row in rows]
        
        # 3. Habits на сьогодні
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
        schedule['habits'] = [dict(row) for row in rows]
        
        # 4. Формуємо таймлайн (все з часом)
        timeline = []
        
        # Time blocks
        for tb in schedule['time_blocks']:
            if not tb['is_skipped']:
                timeline.append({
                    'type': 'time_block',
                    'id': tb['id'],
                    'title': tb['title'],
                    'start_time': tb['start_time'],
                    'end_time': tb['end_time'],
                    'is_fixed': tb['is_fixed'],
                    'is_skippable': tb['is_skippable'],
                })
        
        # Tasks з часом
        for task in schedule['tasks']:
            if task['scheduled_start']:
                start_dt = datetime.fromisoformat(task['scheduled_start'])
                timeline.append({
                    'type': 'task',
                    'id': task['id'],
                    'title': task['title'],
                    'start_time': start_dt.strftime('%H:%M'),
                    'end_time': task.get('scheduled_end', ''),
                    'is_fixed': task['is_fixed'],
                    'priority': task['priority'],
                    'goal_title': task.get('goal_title'),
                })
        
        # Habits з часом
        for habit in schedule['habits']:
            if habit['reminder_time']:
                timeline.append({
                    'type': 'habit',
                    'id': habit['id'],
                    'title': habit['title'],
                    'start_time': habit['reminder_time'],
                    'duration': habit.get('duration_minutes'),
                    'is_fixed': False,
                    'streak': habit.get('current_streak', 0),
                    'today_status': habit.get('today_status'),
                })
        
        # Сортуємо по часу
        timeline.sort(key=lambda x: x.get('start_time', '99:99'))
        schedule['timeline'] = timeline
        
        return schedule
    finally:
        await db.close()


async def get_free_slots(user_id: int, date_: date = None) -> List[Dict[str, str]]:
    """
    Отримати вільні слоти на день.
    Враховує time_blocks та tasks з is_fixed=True.
    """
    db = await get_db()
    try:
        date_ = date_ or date.today()
        date_iso = date_.isoformat()
        weekday = date_.isoweekday()
        
        # Зайняті слоти
        busy_slots = []
        
        # Time blocks (не skipped)
        cursor = await db.execute(
            """
            SELECT tb.start_time, tb.end_time
            FROM time_blocks tb
            LEFT JOIN time_block_skips tbs ON tb.id = tbs.time_block_id AND tbs.skip_date = ?
            WHERE tb.user_id = ? 
              AND tb.is_active = 1
              AND tb.days LIKE '%' || ? || '%'
              AND tbs.id IS NULL
            """,
            (date_iso, user_id, str(weekday))
        )
        rows = await cursor.fetchall()
        for row in rows:
            busy_slots.append((row['start_time'], row['end_time']))
        
        # Fixed tasks
        cursor = await db.execute(
            """
            SELECT TIME(scheduled_start) as start_time, TIME(scheduled_end) as end_time
            FROM tasks
            WHERE user_id = ? 
              AND DATE(scheduled_start) = ?
              AND is_fixed = 1
              AND is_completed = 0
            """,
            (user_id, date_iso)
        )
        rows = await cursor.fetchall()
        for row in rows:
            if row['start_time'] and row['end_time']:
                busy_slots.append((row['start_time'], row['end_time']))
        
        # Розраховуємо вільні слоти (спрощено: 06:00 - 23:00)
        busy_slots.sort()
        
        free_slots = []
        day_start = "06:00"
        day_end = "23:00"
        
        current = day_start
        for start, end in busy_slots:
            if start > current:
                free_slots.append({'start': current, 'end': start})
            current = max(current, end)
        
        if current < day_end:
            free_slots.append({'start': current, 'end': day_end})
        
        return free_slots
    finally:
        await db.close()


async def reschedule_flexible_tasks(user_id: int, date_: date = None) -> List[Dict[str, Any]]:
    """
    Перерозподілити гнучкі задачі у вільні слоти.
    Викликається після skip time_block або задачі.
    """
    db = await get_db()
    try:
        date_ = date_ or date.today()
        date_iso = date_.isoformat()
        
        # Отримуємо вільні слоти
        free_slots = await get_free_slots(user_id, date_)
        
        # Отримуємо гнучкі задачі без часу або з часом що потребує перерозподілу
        cursor = await db.execute(
            """
            SELECT * FROM tasks
            WHERE user_id = ? 
              AND DATE(scheduled_start) = ?
              AND is_fixed = 0
              AND is_completed = 0
            ORDER BY priority, deadline
            """,
            (user_id, date_iso)
        )
        flexible_tasks = [dict(row) for row in await cursor.fetchall()]
        
        # Отримуємо гнучкі habits
        weekday = date_.isoweekday()
        cursor = await db.execute(
            """
            SELECT id, title, reminder_time, duration_minutes 
            FROM goals
            WHERE user_id = ? 
              AND goal_type = 'habit' 
              AND status = 'active'
              AND (frequency = 'daily' OR schedule_days LIKE '%' || ? || '%')
            ORDER BY reminder_time
            """,
            (user_id, str(weekday))
        )
        habits = [dict(row) for row in await cursor.fetchall()]
        
        rescheduled = []
        
        # Простий алгоритм: призначаємо задачі/звички у вільні слоти
        slot_index = 0
        for task in flexible_tasks:
            if slot_index >= len(free_slots):
                break
            
            duration = task.get('estimated_duration') or 30  # Default 30 min
            slot = free_slots[slot_index]
            
            # Перевіряємо чи вміщується
            slot_start = datetime.strptime(slot['start'], '%H:%M')
            slot_end = datetime.strptime(slot['end'], '%H:%M')
            slot_duration = (slot_end - slot_start).seconds // 60
            
            if slot_duration >= duration:
                # Призначаємо
                new_start = datetime.combine(date_, slot_start.time())
                new_end = new_start + timedelta(minutes=duration)
                
                await db.execute(
                    "UPDATE tasks SET scheduled_start = ?, scheduled_end = ? WHERE id = ?",
                    (new_start.isoformat(), new_end.isoformat(), task['id'])
                )
                
                rescheduled.append({
                    'type': 'task',
                    'id': task['id'],
                    'title': task['title'],
                    'new_time': slot['start']
                })
                
                # Оновлюємо слот
                new_slot_start = new_end.strftime('%H:%M')
                if new_slot_start < slot['end']:
                    free_slots[slot_index] = {'start': new_slot_start, 'end': slot['end']}
                else:
                    slot_index += 1
        
        await db.commit()
        return rescheduled
    finally:
        await db.close()
