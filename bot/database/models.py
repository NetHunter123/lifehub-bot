"""
Моделі бази даних.
Ініціалізація SQLite та створення таблиць.
"""

import aiosqlite
from bot.config import config


async def init_database() -> None:
    """Ініціалізує базу даних та створює таблиці."""
    
    # Створюємо директорію для БД якщо не існує
    config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        
        # ============== ЗАДАЧІ ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                priority INTEGER DEFAULT 2,
                deadline DATETIME,
                reminder_time DATETIME,
                goal_id INTEGER,
                is_recurring INTEGER DEFAULT 0,
                recurrence_pattern TEXT,
                is_completed INTEGER DEFAULT 0,
                completed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE SET NULL
            )
        """)
        
        # Індекс для швидкого пошуку по user_id
        await db.execute("""
            CREATE INDEX IF NOT EXISTS ix_tasks_user_id ON tasks(user_id)
        """)
        
        # ============== ЦІЛІ ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                goal_type TEXT NOT NULL,  -- yearly, quarterly, monthly, weekly
                deadline DATE,
                parent_id INTEGER,
                progress INTEGER DEFAULT 0,  -- 0-100
                is_completed INTEGER DEFAULT 0,
                completed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES goals(id) ON DELETE SET NULL
            )
        """)
        
        # ============== ЗВИЧКИ ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                frequency TEXT NOT NULL,  -- daily, weekdays, weekends, custom
                custom_days TEXT,  -- JSON: [1,2,3,4,5] для custom
                reminder_time TIME,
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS habit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                date DATE NOT NULL,
                status TEXT NOT NULL,  -- done, skipped, missed
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
                UNIQUE(habit_id, date)
            )
        """)
        
        # ============== КНИГИ ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT,
                year INTEGER,
                pages INTEGER,
                current_page INTEGER DEFAULT 0,
                status TEXT DEFAULT 'want_to_read',  -- reading, want_to_read, completed
                rating INTEGER,  -- 1-5
                tags TEXT,  -- JSON array
                notes TEXT,
                file_path TEXT,
                file_id TEXT,  -- Telegram file_id
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ============== СЛОВНИК ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                translation TEXT NOT NULL,
                language TEXT DEFAULT 'de',  -- de, en
                part_of_speech TEXT,  -- noun, verb, adjective, etc.
                gender TEXT,  -- der, die, das (для німецької)
                plural TEXT,
                example TEXT,
                tags TEXT,  -- JSON array
                cefr_level TEXT,  -- A1, A2, B1, B2, C1, C2
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS word_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER NOT NULL,
                ease_factor REAL DEFAULT 2.5,
                interval INTEGER DEFAULT 0,  -- днів до наступного повторення
                repetitions INTEGER DEFAULT 0,
                due_date DATE,
                last_review DATETIME,
                lapses INTEGER DEFAULT 0,  -- кількість забувань
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
                category TEXT  -- discipline, consistency, learning
            )
        """)
        
        # ============== НАЛАШТУВАННЯ ==============
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        # Вставляємо початкові мотиваційні цитати
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
    """Повертає з''єднання з базою даних."""
    return await aiosqlite.connect(config.DATABASE_PATH)
