"""
Моделі бази даних.
LifeHub Bot v4.0

Таблиці:
- user_settings
- tasks (з recurring підтримкою)
- task_occurrences (для recurring tasks)
- goals (project, habit, target, metric)
- habit_logs
- goal_entries
- books (Фаза 3)
- words (Фаза 3)
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
                timezone TEXT DEFAULT 'Europe/Berlin',
                morning_time TEXT DEFAULT '08:00',
                evening_time TEXT DEFAULT '21:00',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ============== ЗАДАЧІ ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                
                -- Пріоритет (Eisenhower: 0=urgent, 1=high, 2=medium, 3=low)
                priority INTEGER DEFAULT 2,
                
                -- Час (розділені поля для гнучкості)
                deadline DATE,                    -- Тільки дата
                scheduled_time TEXT,              -- '08:30' (час початку)
                scheduled_end TEXT,               -- '12:30' (час завершення)
                estimated_minutes INTEGER,        -- Тривалість
                
                -- Повторення
                is_recurring INTEGER DEFAULT 0,   -- 0=one-time, 1=recurring
                recurrence_rule TEXT,             -- 'daily', 'weekdays', 'weekly', 'custom'
                recurrence_days TEXT,             -- '1,2,3,4' для custom (ISO weekday)
                
                -- Фіксований час (не зсувається автоматично)
                is_fixed INTEGER DEFAULT 0,
                
                -- Прив'язка до проєкту
                goal_id INTEGER,
                
                -- Статус (для one-time задач)
                is_completed INTEGER DEFAULT 0,
                completed_at DATETIME,
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE SET NULL
            )
        """)
        
        await db.execute("CREATE INDEX IF NOT EXISTS ix_tasks_user ON tasks(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS ix_tasks_deadline ON tasks(deadline)")
        await db.execute("CREATE INDEX IF NOT EXISTS ix_tasks_goal ON tasks(goal_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS ix_tasks_recurring ON tasks(is_recurring)")
        
        # ============== ВХОДЖЕННЯ ЗАДАЧ (для recurring) ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS task_occurrences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                
                date DATE NOT NULL,
                occurrence_number INTEGER,        -- Порядковий номер: 1, 2, 3...
                status TEXT DEFAULT 'pending',    -- pending, done, skipped
                
                notes TEXT,
                completed_at DATETIME,
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                UNIQUE(task_id, date)
            )
        """)
        
        await db.execute("CREATE INDEX IF NOT EXISTS ix_task_occ_date ON task_occurrences(date)")
        await db.execute("CREATE INDEX IF NOT EXISTS ix_task_occ_task ON task_occurrences(task_id)")
        
        # ============== ЦІЛІ (Goals v3) ==============
        # Типи: project, habit, target, metric
        # ВАЖЛИВО: 'task' — НЕ тип Goal, tasks — окрема таблиця!
        await db.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                
                -- Структурний тип (визначає логіку трекінгу)
                -- БЕЗ 'task' — tasks це окрема таблиця!
                goal_type TEXT NOT NULL CHECK(goal_type IN ('project', 'habit', 'target', 'metric')),
                
                -- Ієрархія (тільки project може мати parent)
                parent_id INTEGER,
                
                -- Теги доменів (JSON array)
                domain_tags TEXT DEFAULT '[]',
                
                -- === Для Habit ===
                frequency TEXT,                   -- 'daily', 'weekdays', '3_per_week', 'custom'
                schedule_days TEXT,               -- '1,2,3,4,5' (ISO weekday: 1=Пн)
                reminder_time TEXT,               -- '08:00'
                duration_minutes INTEGER,
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                
                -- === Для Target ===
                target_value REAL,                -- 24 (книги)
                current_value REAL DEFAULT 0,
                unit TEXT,                        -- 'книг', 'км', '€'
                
                -- === Для Metric ===
                target_min REAL,                  -- 73 (кг)
                target_max REAL,                  -- 77 (кг)
                
                -- === Загальне ===
                deadline DATE,
                progress INTEGER DEFAULT 0,       -- 0-100, auto для project/target
                status TEXT DEFAULT 'active' CHECK(status IN ('active', 'completed', 'archived')),
                
                completed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (parent_id) REFERENCES goals(id) ON DELETE SET NULL
            )
        """)
        
        await db.execute("CREATE INDEX IF NOT EXISTS ix_goals_user ON goals(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS ix_goals_type ON goals(goal_type)")
        await db.execute("CREATE INDEX IF NOT EXISTS ix_goals_parent ON goals(parent_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS ix_goals_status ON goals(status)")
        
        # ============== ЛОГИ ЗВИЧОК ==============
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
        
        await db.execute("CREATE INDEX IF NOT EXISTS ix_habit_logs_date ON habit_logs(date)")
        await db.execute("CREATE INDEX IF NOT EXISTS ix_habit_logs_goal ON habit_logs(goal_id)")
        
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
        
        await db.execute("CREATE INDEX IF NOT EXISTS ix_goal_entries_goal ON goal_entries(goal_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS ix_goal_entries_date ON goal_entries(date)")
        
        # ============== КНИГИ (Фаза 3) ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                author TEXT,
                year INTEGER,
                pages INTEGER,
                current_page INTEGER DEFAULT 0,
                status TEXT DEFAULT 'want_to_read' CHECK(status IN ('want_to_read', 'reading', 'completed')),
                rating INTEGER CHECK(rating BETWEEN 1 AND 5),
                tags TEXT DEFAULT '[]',           -- JSON array
                notes TEXT,
                file_id TEXT,                     -- Telegram file_id
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("CREATE INDEX IF NOT EXISTS ix_books_user ON books(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS ix_books_status ON books(status)")
        
        # ============== СЛОВНИК (Фаза 3, SM-2) ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                word TEXT NOT NULL,
                translation TEXT NOT NULL,
                language TEXT DEFAULT 'de',
                part_of_speech TEXT,
                example TEXT,
                tags TEXT DEFAULT '[]',
                
                -- SM-2 algorithm fields
                ease_factor REAL DEFAULT 2.5,
                interval INTEGER DEFAULT 0,
                repetitions INTEGER DEFAULT 0,
                due_date DATE,
                last_review DATETIME,
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("CREATE INDEX IF NOT EXISTS ix_words_user ON words(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS ix_words_due ON words(due_date)")
        
        # ============== МОТИВАЦІЙНІ ЦИТАТИ ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote TEXT NOT NULL,
                author TEXT,
                category TEXT
            )
        """)
        
        # Seed quotes
        await db.execute("""
            INSERT OR IGNORE INTO quotes (id, quote, category) VALUES
            (1, 'Тягар втраченої можливості важчий за тягар дисципліни', 'discipline'),
            (2, 'Маленький крок сьогодні — великий результат завтра', 'consistency'),
            (3, '5 хвилин краще ніж 0 хвилин', 'motivation'),
            (4, 'Дисципліна — це міст між цілями та досягненнями', 'discipline'),
            (5, 'Успіх — це сума маленьких зусиль, що повторюються день за днем', 'consistency')
        """)
        
        await db.commit()
        
        print("✅ База даних ініціалізована (v4.0)")


async def get_db() -> aiosqlite.Connection:
    """Повертає з'єднання з базою даних."""
    db = await aiosqlite.connect(config.DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    return db
