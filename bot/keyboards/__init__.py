"""Клавіатури бота."""

from bot.keyboards.menu import get_main_menu_keyboard, get_back_to_menu_keyboard
from bot.keyboards.reply import get_main_reply_keyboard, get_cancel_keyboard, get_skip_cancel_keyboard
from bot.keyboards.common import get_language_keyboard, get_confirm_keyboard
from bot.keyboards.tasks import (
    get_priority_keyboard,
    get_deadline_keyboard,
    get_task_actions_keyboard,
    get_tasks_list_keyboard,
)

__all__ = [
    "get_main_menu_keyboard",
    "get_back_to_menu_keyboard",
    "get_main_reply_keyboard",
    "get_cancel_keyboard",
    "get_skip_cancel_keyboard",
    "get_language_keyboard",
    "get_confirm_keyboard",
    "get_priority_keyboard",
    "get_deadline_keyboard",
    "get_task_actions_keyboard",
    "get_tasks_list_keyboard",
]
