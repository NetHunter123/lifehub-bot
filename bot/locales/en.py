"""English translations."""

TEXTS = {
    # ========== GENERAL ==========
    "welcome": (
        "👋 <b>Hello!</b>\n\n"
        "I'm <b>LifeHub Bot</b> — your personal assistant for:\n\n"
        "📋 Task and goal management\n"
        "✅ Habit tracking\n"
        "📚 Book library\n"
        "🇩🇪 Language learning\n\n"
        "Use the menu below 👇"
    ),
    "help_title": "📖 <b>Bot Commands</b>",
    "help_general": (
        "<b>General:</b>\n"
        "/start — Welcome\n"
        "/help — This help\n"
        "/today — Today's dashboard\n"
        "/language — Change language"
    ),
    "help_tasks": (
        "<b>Tasks:</b>\n"
        "/tasks — Today's tasks\n"
        "/task_add — Add task\n"
        "/task_done &lt;id&gt; — Complete"
    ),
    "help_goals": (
        "<b>Goals:</b>\n"
        "/goals — List goals\n"
        "/goal_add — Add goal"
    ),
    "help_habits": (
        "<b>Habits:</b>\n"
        "/habits — Today's habits\n"
        "/habit_add — Add habit"
    ),
    
    # ========== BUTTONS ==========
    "btn_cancel": "❌ Cancel",
    "btn_skip": "⏭ Skip",
    "btn_back": "◀️ Back",
    "btn_back_menu": "◀️ Back to menu",
    "btn_done": "✅ Done",
    "btn_yes": "✅ Yes",
    "btn_no": "❌ No",
    "btn_refresh": "🔄 Refresh",
    "btn_edit": "✏️ Edit",
    "btn_delete": "🗑 Delete",
    "btn_undo": "↩️ Undo",
    "btn_add_note": "📝 Add note",
    "btn_add_task": "➕ Add task",
    
    # Main menu
    "btn_tasks": "📋 Tasks",
    "btn_goals": "🎯 Goals",
    "btn_habits": "✅ Habits",
    "btn_books": "📚 Books",
    "btn_words": "🇩🇪 Words",
    "btn_stats": "📊 Statistics",
    "btn_settings": "⚙️ Settings",
    "btn_today": "📊 Today",
    "btn_add": "➕ Add",
    
    # Cancel
    "cancelled": "❌ Cancelled.",
    "action_cancelled": "❌ Action cancelled.",
    
    # Menu
    "menu_title": "🏠 <b>Main Menu</b>\n\nChoose section:",
    "section_in_dev": "🚧 This section is under development...",
    
    # ========== LANGUAGE ==========
    "language_select": "🌐 Choose language / Обери мову:",
    "language_changed": "✅ Language changed!",
    
    # ========== TASKS ==========
    "tasks_today_title": "📋 <b>Today's Tasks</b> ({date})",
    "tasks_all_title": "📋 <b>All Tasks</b>",
    "tasks_inbox_title": "📥 <b>Inbox</b> (unprocessed)",
    "tasks_empty": "📭 No tasks",
    "tasks_completed": "✅ Completed: {done}/{total}",
    
    # Priorities
    "priority_urgent": "🔴 Urgent",
    "priority_high": "🟠 High",
    "priority_medium": "🟡 Medium",
    "priority_low": "🟢 Low",
    
    # Task creation
    "task_add_title": "📝 <b>New Task</b>\n\nEnter title:",
    "task_add_description": "📝 Add description (or skip):",
    "task_add_priority": "🎯 Choose priority:",
    "task_add_deadline": "📅 Choose deadline:",
    "task_add_time": "⏰ Start time?",
    "task_add_duration": "⏱ Duration?",
    "task_add_travel": "🚶 Travel time?",
    "task_add_location": "📍 Location (optional):",
    "task_add_recurring": "🔄 Recurring task?",
    
    # Deadlines
    "deadline_today": "📅 Today",
    "deadline_tomorrow": "📆 Tomorrow",
    "deadline_week": "🗓 This week",
    "deadline_pick": "✏️ Pick date",
    "deadline_none": "❌ No deadline",
    
    # Time
    "time_none": "❌ No time",
    "time_pick": "⏰ Pick time",
    "duration_30m": "30min",
    "duration_1h": "1h",
    "duration_1_5h": "1.5h",
    "duration_2h": "2h",
    "duration_4h": "4h",
    "duration_other": "Other",
    "travel_none": "❌ Not needed",
    "travel_15m": "15min",
    "travel_30m": "30min",
    "travel_45m": "45min",
    "travel_1h": "1h",
    
    # Recurring
    "recurring_no": "❌ No, one-time",
    "recurring_daily": "📅 Daily",
    "recurring_weekdays": "📅 Weekdays",
    "recurring_weekly": "📅 Weekly",
    "recurring_custom": "📅 Custom days",
    
    # Results
    "task_created": (
        "✅ <b>Task created!</b>\n\n"
        "📝 {title}\n"
        "🎯 Priority: {priority}\n"
        "{deadline}"
        "{time}"
        "\n🆔 ID: {task_id}"
    ),
    "task_created_deadline": "📅 Deadline: {deadline}\n",
    "task_created_time": "⏰ Time: {time}\n",
    
    "task_done": "✅ Task #{task_id} completed!",
    "task_done_stats": "📊 Completed today: {count}",
    "task_deleted": "🗑 Task #{task_id} deleted.",
    "task_not_found": "❌ Task not found.",
    "task_undo_done": "✅ Completion undone. Task is active again.",
    
    # View
    "task_view_description": "📝 {description}",
    "task_view_deadline": "📅 Deadline: {deadline}",
    "task_view_overdue": " ⚠️ <i>overdue!</i>",
    
    # Confirmation
    "task_delete_confirm": "🗑 <b>Delete task?</b>\n\nThis cannot be undone.",
    
    # Commands
    "task_done_usage": "❓ Specify task ID: /task_done 5",
    "task_delete_usage": "❓ Specify task ID: /task_delete 5",
    "task_id_invalid": "❌ ID must be a number",
    
    "what_next": "What's next?",
    
    # ========== GOALS ==========
    "goals_title": "🎯 <b>My Goals</b>",
    "goals_empty": "📭 No goals yet. Create your first!",
    
    "goal_add_title": "🎯 <b>New Goal</b>\n\nEnter title:",
    "goal_add_type": "Goal type?",
    
    "goal_type_learning": "📚 Learning",
    "goal_type_fitness": "💪 Fitness",
    "goal_type_project": "🛠 Project",
    "goal_type_habit": "🔄 Habit Building",
    "goal_type_collection": "📊 Collection",
    "goal_type_financial": "💰 Financial",
    
    "goal_created": "✅ <b>Goal created!</b>",
    
    # ========== HABITS ==========
    "habits_title": "✅ <b>Today's Habits</b> ({date})",
    "habits_empty": "📭 No habits yet. Create your first!",
    "habits_progress": "Progress: {done}/{total} ({percent}%)",
    
    "habit_add_title": "✅ <b>New Habit</b>\n\nTitle:",
    "habit_created": "✅ <b>Habit created!</b>",
    "habit_done": "✅ {title} — done!\n🔥 Streak: {streak} days!",
    
    # ========== DASHBOARD ==========
    "dashboard_title": "📊 <b>TODAY</b> — {date}",
    "dashboard_schedule": "⏰ <b>SCHEDULE:</b>",
    "dashboard_tasks": "📋 <b>TASKS:</b>",
    "dashboard_habits": "✅ <b>HABITS:</b>",
    "dashboard_progress": "📈 Day progress: {done}/{total} ({percent}%)",
    
    # ========== BOOKS ==========
    "books_title": "📚 <b>My Library</b>",
    "books_empty": "📭 Library is empty.",
    
    # ========== WORDS ==========
    "words_title": "🇩🇪 <b>Word Learning</b>",
    "words_empty": "📭 Dictionary is empty.",
    
    # ========== ERRORS ==========
    "error_general": "❌ An error occurred. Try again.",
    "error_not_found": "❌ Not found.",
    "error_invalid_input": "❌ Invalid input.",
}
