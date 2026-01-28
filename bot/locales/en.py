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
    "btn_restore": "🔄 Restore to active",
    "btn_add_note": "📝 Add note",
    "btn_add_task": "➕ Add task",
    "btn_add_another": "➕ Add another",
    "btn_view_tasks": "📋 View tasks",
    
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
    "tasks_history_title": "📜 <b>Tasks History</b>",
    "tasks_empty": "📭 No tasks",
    "tasks_completed": "✅ Completed: {done}/{total}",
    
    # Filters
    "filter_today": "📅 Today",
    "filter_all": "📋 All",
    "filter_history": "📜 History",
    
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
    "deadline_custom": "📅 Pick date",
    "deadline_none": "❌ No deadline",
    
    # Custom input
    "task_add_deadline_custom": "📅 Enter date in format <b>DD.MM.YYYY</b>\n\nExample: 28.01.2026 or 28.01",
    "task_add_time_custom": "⏰ Enter time in format <b>HH:MM</b>\n\nExample: 14:30 or 9:00",
    "task_add_duration_custom": "⏱ Enter duration in minutes\n\nExample: 45 or 90\nOr: 1h 30m",
    
    # Time
    "time_none": "❌ No time",
    "time_custom": "✏️ Other time",
    "duration_15m": "15min",
    "duration_30m": "30min",
    "duration_45m": "45min",
    "duration_1h": "1h",
    "duration_1_5h": "1.5h",
    "duration_2h": "2h",
    "duration_3h": "3h",
    "duration_4h": "4h",
    "duration_custom": "✏️ Other",
    
    # Time units
    "hour_short": "h",
    "min_short": "m",
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
    "task_created_full": (
        "✅ <b>Task created!</b>\n\n"
        "📝 {title}\n"
        "🎯 Priority: {priority}\n"
        "{deadline}"
        "{time}"
        "{duration}"
        "\n🆔 ID: {task_id}"
    ),
    "task_created_deadline": "📅 Deadline: {deadline}\n",
    "task_created_time": "⏰ Time: {time}\n",
    "task_created_duration": "⏱ Duration: {duration}\n",
    
    "task_done": "✅ Task #{task_id} completed!",
    "task_done_stats": "📊 Completed today: {count}",
    "task_deleted": "🗑 Task #{task_id} deleted.",
    "task_not_found": "❌ Task not found.",
    "task_undo_done": "✅ Completion undone. Task is active again.",
    
    # View
    "task_view_description": "📝 {description}",
    "task_view_deadline": "📅 Deadline: {deadline}",
    "task_view_time": "Time",
    "task_view_duration": "Duration",
    "task_view_overdue": " ⚠️ <i>overdue!</i>",
    
    # Confirmation
    "task_delete_confirm": "🗑 <b>Delete task?</b>\n\nThis cannot be undone.",
    
    # Commands
    "task_done_usage": "❓ Specify task ID: /task_done 5",
    "task_delete_usage": "❓ Specify task ID: /task_delete 5",
    "task_id_invalid": "❌ ID must be a number",
    
    "what_next": "What's next?",

    # Task editing
    "task_edit_choose_field": "✏️ <b>Editing:</b> {title}\n\nWhat to change?",
    "task_edit_title": "📝 Enter new title:",
    "task_edit_description": "📋 Enter new description:",
    "task_edit_priority": "🎯 Choose new priority:",
    "task_edit_deadline": "📅 Choose new deadline:",
    "task_edit_time": "⏰ Choose new time:",
    "task_edit_duration": "⏱ Choose new duration:",
    "task_updated": "✅ Task updated!",
    
    "edit_field_title": "📝 Title",
    "edit_field_description": "📋 Description",
    "edit_field_priority": "🎯 Priority",
    "edit_field_deadline": "📅 Deadline",
    "edit_field_time": "⏰ Time",
    "edit_field_duration": "⏱ Duration",
    
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
    
    # ========== GOALS ==========
    "goals_active_title": "🎯 <b>Active Goals</b>",
    "goals_completed_title": "✅ <b>Completed Goals</b>",
    "goals_all_title": "📊 <b>All Goals</b>",
    "goals_empty": "📭 No goals yet. Add your first!",
    "goals_stats": "📊 Active: {active} | Completed: {completed}",
    
    # Goal types
    "goal_type_yearly": "Yearly",
    "goal_type_quarterly": "Quarterly",
    "goal_type_monthly": "Monthly",
    "goal_type_weekly": "Weekly",
    "goal_type_label": "Type",
    
    # Goal creation
    "goal_add_title": "🎯 What goal do you want to set?\n\nEnter goal title:",
    "goal_add_description": "📝 Add description (or skip):",
    "goal_add_type": "📊 What type of goal?",
    "goal_add_parent": "🔗 Link to parent goal?",
    "goal_add_deadline": "📅 When is the deadline?",
    "goal_add_deadline_custom": "📅 Enter date in format <b>DD.MM.YYYY</b>:",
    "goal_no_parent": "➖ No parent",
    
    # Deadlines
    "deadline_end_week": "📅 End of week",
    "deadline_end_month": "📅 End of month",
    "deadline_end_quarter": "📅 End of quarter",
    "deadline_end_year": "📅 End of year",
    "deadline_custom": "✏️ Enter date",
    "deadline_none": "➖ No deadline",
    
    # Goal view
    "goal_parent": "Parent goal",
    "progress": "Progress",
    "deadline": "Deadline",
    "created": "Created",
    "completed": "Completed",
    
    # Results
    "goal_created": "✅ Goal #{goal_id} created!",
    "goal_created_short": "Goal created!",
    "goal_updated": "✅ Goal updated!",
    "goal_deleted": "🗑 Goal deleted.",
    "goal_completed": "🎉 Congratulations! Goal achieved!",
    "goal_restored": "🔄 Goal restored to active.",
    "goal_not_found": "❌ Goal not found.",
    "goal_delete_confirm": "⚠️ Delete this goal?",
    
    # Progress
    "goal_progress_prompt": "📈 Current progress: {current}%\n\nChoose new or enter manually:",
    "goal_progress_enter": "📈 Enter progress (0-100):",
    "goal_progress_updated": "📈 Progress updated: {progress}%",
    "progress_custom": "✏️ Enter manually",
    "error_invalid_progress": "❌ Enter a number from 0 to 100.",
    
    # Editing
    "goal_edit_choose_field": "✏️ <b>Editing:</b> {title}\n\nWhat to change?",
    "goal_edit_title": "📝 Enter new title:",
    "goal_edit_description": "📝 Enter new description:",
    "goal_edit_deadline": "📅 Choose new deadline:",
    "goal_edit_type": "📊 Choose new type:",
    "edit_field_type": "📊 Goal type",
    
    # Filters
    "filter_active": "📌 Active",
    "filter_completed": "✅ Completed",
    
    # Goal buttons
    "btn_add_goal": "➕ Add goal",
    "btn_progress": "📈 Progress",
    "btn_complete": "🏆 Complete",

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
    "error_invalid_date": "❌ Invalid date format. Use DD.MM.YYYY (example: 28.01.2026)",
    "error_invalid_time": "❌ Invalid time format. Use HH:MM (example: 14:30)",
    "error_invalid_duration": "❌ Invalid duration. Enter number of minutes (example: 45)",
}
