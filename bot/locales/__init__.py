"""
Система локалізації.
LifeHub Bot v4.0
"""

from bot.locales import uk

# Словник доступних мов
LANGUAGES = {
    'uk': uk,
    # 'en': en,  # Додати пізніше
}

DEFAULT_LANGUAGE = 'uk'


def get_locale(lang: str = None):
    """Отримати модуль локалізації за кодом мови."""
    return LANGUAGES.get(lang or DEFAULT_LANGUAGE, uk)


def get_text(key: str, lang: str = None, **kwargs) -> str:
    """
    Отримати текст за ключем.
    
    Приклад:
        get_text('TASKS.empty', 'uk')
        get_text('HABITS.marked_done', 'uk', title='Медитація', streak=5)
    """
    locale = get_locale(lang)
    
    # Розбираємо ключ (наприклад, 'TASKS.empty')
    parts = key.split('.')
    
    try:
        value = getattr(locale, parts[0])
        for part in parts[1:]:
            if isinstance(value, dict):
                value = value[part]
            else:
                value = getattr(value, part)
        
        # Форматуємо якщо є kwargs
        if kwargs and isinstance(value, str):
            return value.format(**kwargs)
        return value
    except (KeyError, AttributeError):
        return f"[{key}]"


# Короткий alias
_ = get_text
