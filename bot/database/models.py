"""
Моделі бази даних.
Ініціалізація SQLite та створення таблиць.
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
                language TEXT DEFAULT 'en',
                group_chat_id INTEGER,
                topic_main_id INTEGER,
                topic_tasks_id INTEGER,
                topic_books_id INTEGER,
                topic_words_id INTEGER,
                morning_time TIME DEFAULT '08:00',
                evening_time TIME DEFAULT '21:00',
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
                priority INTEGER DEFAULT 2,
                deadline DATETIME,
                scheduled_start DATETIME,
                estimated_duration INTEGER,
                travel_time_before INTEGER DEFAULT 0,
                location TEXT,
                reminder_time DATETIME,
                goal_id INTEGER,
                is_recurring INTEGER DEFAULT 0,
                recurrence_pattern TEXT,
                is_completed INTEGER DEFAULT 0,
                completed_at DATETIME,
                status_notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE SET NULL
            )
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS ix_tasks_user_id ON tasks(user_id)
        """)
        
        # ============== ЦІЛІ ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                goal_type TEXT NOT NULL,
                parent_id INTEGER,
                progress INTEGER DEFAULT 0,
                progress_mode TEXT DEFAULT 'auto',
                target_value REAL,
                current_value REAL DEFAULT 0,
                schedule_days TEXT,
                schedule_time TIME,
                duration_minutes INTEGER,
                status TEXT DEFAULT 'active',
                deadline DATE,
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                FOREIGN KEY (parent_id) REFERENCES goals(id) ON DELETE SET NULL
            )
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS ix_goals_user_id ON goals(user_id)
        """)
        
        # ============== ЕТАПИ ЦІЛЕЙ ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS goal_milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                order_num INTEGER NOT NULL,
                progress_current INTEGER DEFAULT 0,
                progress_target INTEGER DEFAULT 4,
                status TEXT DEFAULT 'pending',
                attempts_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
            )
        """)
        
        # ============== ЛОГИ ЕТАПІВ ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS milestone_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                milestone_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                progress_before INTEGER,
                progress_after INTEGER,
                status TEXT NOT NULL,
                skip_reason TEXT,
                duration_minutes INTEGER,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (milestone_id) REFERENCES goal_milestones(id) ON DELETE CASCADE
            )
        """)
        
        # ============== МЕТРИКИ ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS goal_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                unit TEXT,
                target_value REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS metric_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_id INTEGER NOT NULL,
                value REAL NOT NULL,
                date DATE NOT NULL,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (metric_id) REFERENCES goal_metrics(id) ON DELETE CASCADE
            )
        """)
        
        # ============== ЗВИЧКИ ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                frequency TEXT NOT NULL,
                custom_days TEXT,
                reminder_time TIME,
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS habit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                status TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
                UNIQUE(habit_id, date)
            )
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
                gender TEXT,
                plural TEXT,
                example TEXT,
                tags TEXT,
                cefr_level TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS word_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                ease_factor REAL DEFAULT 2.5,
                interval INTEGER DEFAULT 0,
                repetitions INTEGER DEFAULT 0,
                due_date DATE,
                last_review DATETIME,
                lapses INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE,
                UNIQUE(word_id)
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
            (5, 'Успіх — це сума маленьких зусиль, що повторюються день за днем', 'consistency'),
            (6, 'Не зупиняйся, коли втомився. Зупиняйся, коли закінчив', 'discipline'),
            (7, 'Кожен експерт колись був початківцем', 'learning'),
            (8, 'Найкращий час посадити дерево був 20 років тому. Другий найкращий час — зараз', 'consistency')
        """)
        
        await db.commit()


async def get_db() -> aiosqlite.Connection:
    """Повертає з'єднання з базою даних."""
    return await aiosqlite.connect(config.DATABASE_PATH)
