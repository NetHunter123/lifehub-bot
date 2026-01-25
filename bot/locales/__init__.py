"""
Модуль локалізації (i18n).

Використання:
    from bot.locales import t, get_user_lang, set_user_lang
    
    lang = get_user_lang(user_id)
    text = t("welcome", lang)
    text = t("task_done", lang, task_id=5)
"""

from typing import Optional

# Імпортуємо словники перекладів
from bot.locales import uk, en, ru, de

LANGUAGES = {
    'uk': uk.TEXTS,
    'en': en.TEXTS,
    'ru': ru.TEXTS,
    'de': de.TEXTS,
}

DEFAULT_LANG = 'en'

# Кеш мов користувачів (user_id -> lang)
_user_languages: dict[int, str] = {}


def t(key: str, lang: str = DEFAULT_LANG, **kwargs) -> str:
    """
    Отримати переклад за ключем.
    
    Args:
        key: Ключ перекладу (наприклад, "task_created")
        lang: Код мови (uk, en, ru, de)
        **kwargs: Змінні для підстановки
    
    Returns:
        Перекладений текст
    
    Приклади:
        t("welcome", "uk")
        t("task_done", "uk", task_id=5)
    """
    texts = LANGUAGES.get(lang, LANGUAGES[DEFAULT_LANG])
    text = texts.get(key)
    
    # Fallback на англійську якщо ключ не знайдено
    if text is None:
        text = LANGUAGES[DEFAULT_LANG].get(key, f"[{key}]")
    
    try:
        return text.format(**kwargs) if kwargs else text
    except KeyError as e:
        # Якщо не вистачає змінної — повертаємо текст як є
        return text


def get_user_lang(user_id: int) -> str:
    """Отримати мову користувача з кешу."""
    return _user_languages.get(user_id, DEFAULT_LANG)


def set_user_lang(user_id: int, lang: str) -> None:
    """Встановити мову користувача в кеш."""
    if lang in LANGUAGES:
        _user_languages[user_id] = lang


def get_available_languages() -> list[str]:
    """Список доступних мов."""
    return list(LANGUAGES.keys())


def get_language_name(lang_code: str) -> str:
    """Назва мови за кодом."""
    names = {
        'uk': '🇺🇦 Українська',
        'en': '🇬🇧 English',
        'ru': '🇷🇺 Русский',
        'de': '🇩🇪 Deutsch',
    }
    return names.get(lang_code, lang_code)
