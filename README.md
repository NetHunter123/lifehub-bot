# 🚀 LifeHub Bot

Персональний Telegram-бот для управління задачами, цілями, звичками, бібліотекою книг та вивчення мов.

## 📋 Функціонал

| Модуль | Опис |
|--------|------|
| 📋 Задачі | Ієрархія цілей, пріоритети, дедлайни, повторювані задачі |
| ✅ Звички | Трекінг з серіями (streaks), статистика |
| 📚 Книги | Бібліотека PDF/FB2, теги, оцінки, пошук |
| 🇩🇪 Слова | Вивчення німецької/англійської, SM-2 алгоритм |
| ⏰ Нагадування | Ранковий/вечірній огляд, мотивація |
| 📊 Статистика | Загальний прогрес, досягнення |

## 🛠 Технології

- **Python 3.10+**
- **aiogram 3.x** — асинхронний Telegram Bot API
- **SQLite + aiosqlite** — база даних
- **APScheduler** — планувальник нагадувань
- **PyMuPDF, ebookmeta** — парсинг книг

## 📁 Структура проєкту

```
lifehub-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Точка входу
│   ├── config.py            # Налаштування
│   ├── handlers/            # Обробники команд
│   │   ├── __init__.py
│   │   ├── common.py        # /start, /help, /menu
│   │   ├── tasks.py         # Задачі
│   │   ├── habits.py        # Звички
│   │   ├── books.py         # Книги
│   │   └── words.py         # Вивчення слів
│   ├── keyboards/           # Inline-клавіатури
│   │   ├── __init__.py
│   │   └── menu.py
│   ├── database/            # Робота з БД
│   │   ├── __init__.py
│   │   ├── models.py        # Схема таблиць
│   │   └── queries.py       # SQL-запити
│   ├── services/            # Бізнес-логіка
│   │   ├── __init__.py
│   │   ├── srs.py           # SM-2 алгоритм
│   │   └── scheduler.py     # APScheduler
│   └── utils/               # Допоміжні функції
│       ├── __init__.py
│       └── helpers.py
├── data/
│   └── dictionaries/        # CSV словники
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## ⚡ Швидкий старт

### 1. Клонування
```bash
git clone https://github.com/NetHunter123/lifehub-bot.git
cd lifehub-bot
```

### 2. Віртуальне середовище
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Залежності
```bash
pip install -r requirements.txt
```

### 4. Конфігурація
```bash
cp .env.example .env
# Відредагуй .env — додай свій BOT_TOKEN
```

### 5. Запуск
```bash
python -m bot.main
```

## 🔐 Змінні середовища

| Змінна | Опис |
|--------|------|
| `BOT_TOKEN` | Токен від @BotFather |
| `ADMIN_ID` | Твій Telegram ID |
| `DATABASE_PATH` | Шлях до SQLite бази |

## 📝 Команди бота

### Загальні
- `/start` — Привітання
- `/help` — Список команд
- `/menu` — Головне меню

### Задачі
- `/tasks` — Задачі на сьогодні
- `/task_add` — Додати задачу
- `/task_done <id>` — Виконати задачу

### Звички
- `/habits` — Звички на сьогодні
- `/habit_add` — Додати звичку
- `/habit_done <id>` — Відмітити виконання

### Книги
- `/books` — Бібліотека
- `/book_add` — Додати книгу

### Слова
- `/learn` — Почати тренування
- `/words` — Статистика вивчення

## 📄 Ліцензія

MIT License

## 👤 Автор

**NetHunter123**
