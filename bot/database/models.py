"""
Моделі бази даних.
Версія 3.0 — 5 структурних типів цілей.
"""

import aiosqlite
from bot.config import config


async def init_database() -> None:
    """Ініціалізує базу даних та створює таблиці."""
    
    config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        
        # ============== НАЛАШТУВАННЯ КОРИСТУВАЧА ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'uk',
                morning_time TIME DEFAULT '08:00',
                evening_time TIME DEFAULT '21:00',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ============== ЦІЛІ (5 структурних типів) ==============
        # goal_type: task, project, habit, target, metric
        await db.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                
                -- Структурний тип (визначає логіку трекінгу)
                goal_type TEXT NOT NULL CHECK(goal_type IN ('task', 'project', 'habit', 'target', 'metric')),
                
                -- Ієрархія
                parent_id INTEGER,
                
                -- Теги доменів (JSON array: ["health", "learning"])
                domain_tags TEXT DEFAULT '[]',
                
                -- Для Habit
                frequency TEXT,                    -- daily, weekly, 3_per_week
                schedule_days TEXT,                -- "1,2,3,4,5" (Пн-Пт)
                reminder_time TIME,
                duration_minutes INTEGER,          -- Тривалість в хвилинах
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                
                -- Для Target
                target_value REAL,
                current_value REAL DEFAULT 0,
                unit TEXT,                         -- "книг", "км", "€"
                
                -- Для Metric
                target_min REAL,
                target_max REAL,
                
                -- Загальне
                deadline DATE,
                progress INTEGER DEFAULT 0,        -- 0-100, auto для project/target
                status TEXT DEFAULT 'active' CHECK(status IN ('active', 'completed', 'archived')),
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                
                FOREIGN KEY (parent_id) REFERENCES goals(id) ON DELETE SET NULL
            )
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS ix_goals_user_id ON goals(user_id)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS ix_goals_parent_id ON goals(parent_id)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS ix_goals_type ON goals(goal_type)
        """)
        
        # ============== ЛОГИ ЗВИЧОК (для Habit) ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS habit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('done', 'skipped', 'missed')),
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE,
                UNIQUE(goal_id, date)
            )
        """)
        
        # ============== ЗАПИСИ ЦІЛЕЙ (для Target/Metric) ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS goal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                value REAL NOT NULL,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
            )
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS ix_goal_entries_goal_id ON goal_entries(goal_id)
        """)
        
        # ============== TIME BLOCKS (школа, робота) ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS time_blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                days TEXT NOT NULL,                -- "1,2,3,4" (Пн-Чт)
                is_fixed INTEGER DEFAULT 1,        -- Фіксований час (не зсувається)
                is_skippable INTEGER DEFAULT 1,    -- Чи можна пропустити
                is_active INTEGER DEFAULT 1,
                color TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблиця для щоденних пропусків time_blocks
        await db.execute("""
            CREATE TABLE IF NOT EXISTS time_block_skips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time_block_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                skip_date DATE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (time_block_id) REFERENCES time_blocks(id) ON DELETE CASCADE,
                UNIQUE(time_block_id, skip_date)
            )
        """)
        
        # ============== ЗАДАЧІ ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                priority INTEGER DEFAULT 2,        -- 0=urgent, 1=high, 2=medium, 3=low
                deadline DATETIME,
                scheduled_start DATETIME,
                scheduled_end DATETIME,
                estimated_duration INTEGER,        -- хвилини
                reminder_time DATETIME,
                goal_id INTEGER,                   -- Прив'язка до Project
                is_fixed INTEGER DEFAULT 0,        -- 1=фіксований час, 0=гнучкий
                is_completed INTEGER DEFAULT 0,
                completed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE SET NULL
            )
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS ix_tasks_user_id ON tasks(user_id)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS ix_tasks_goal_id ON tasks(goal_id)
        """)
        
        # ============== КНИГИ ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                author TEXT,
                year INTEGER,
                pages INTEGER,
                current_page INTEGER DEFAULT 0,
                status TEXT DEFAULT 'want_to_read',
                rating INTEGER,
                tags TEXT,
                notes TEXT,
                file_path TEXT,
                file_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ============== СЛОВНИК ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                word TEXT NOT NULL,
                translation TEXT NOT NULL,
                language TEXT DEFAULT 'de',
                part_of_speech TEXT,
                example TEXT,
                tags TEXT,
                ease_factor REAL DEFAULT 2.5,
                interval INTEGER DEFAULT 0,
                repetitions INTEGER DEFAULT 0,
                due_date DATE,
                last_review DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ============== МОТИВАЦІЙНІ ЦИТАТИ ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS motivation_quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote TEXT NOT NULL,
                author TEXT,
                category TEXT
            )
        """)
        
        await db.execute("""
            INSERT OR IGNORE INTO motivation_quotes (id, quote, category) VALUES
            (1, 'Тягар втраченої можливості важчий за тягар дисципліни', 'discipline'),
            (2, 'Маленький крок сьогодні — великий результат завтра', 'consistency'),
            (3, '5 хвилин краще ніж 0 хвилин', 'discipline'),
            (4, 'Дисципліна — це міст між цілями та досягненнями', 'discipline'),
            (5, 'Успіх — це сума маленьких зусиль, що повторюються день за днем', 'consistency')
        """)
        
        await db.commit()


async def get_db() -> aiosqlite.Connection:
    """Повертає з'єднання з базою даних."""
    return await aiosqlite.connect(config.DATABASE_PATH)
