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
    "help_general": "<b>General:</b>\n/start — Welcome\n/help — This help\n/today — Today's dashboard\n/language — Change language",
    "help_tasks": "<b>Tasks:</b>\n/tasks — Today's tasks\n/task_add — Add task\n/task_done &lt;id&gt; — Complete",
    "help_goals": "<b>Goals:</b>\n/goals — List goals\n/goal_add — Add goal\n/habits — Today's habits",
    "help_habits": "<b>Habits:</b>\n/habits — Today's habits\n/habit_add — Add habit",
    
    # ========== BUTTONS ==========
    "btn_cancel": "❌ Cancel",
    "btn_skip": "⏭ Skip",
    "btn_back": "◀️ Back",
    "btn_back_menu": "◀️ Back to menu",
    "btn_done": "✅ Done",
    "btn_yes": "✅ Yes",
    "btn_no": "❌ No",
    "btn_refresh": "🔄 Refresh",
    "btn_edit": "✏️",
    "btn_delete": "🗑",
    "btn_undo": "↩️ Undo",
    "btn_restore": "🔄 Restore",
    "btn_add_task": "➕ Add task",
    "btn_add_another": "➕ Add another",
    "btn_view_tasks": "📋 View tasks",
    
    "btn_today": "📅 Today",
    "btn_tasks": "📋 Tasks",
    "btn_goals": "🎯 Goals",
    "btn_habits": "✅ Habits",
    "btn_books": "📚 Books",
    "btn_words": "🇩🇪 Words",
    "btn_stats": "📊 Statistics",
    "btn_settings": "⚙️ Settings",
    
    "cancelled": "❌ Cancelled.",
    "action_cancelled": "❌ Action cancelled.",
    "menu_title": "🏠 <b>Main Menu</b>\n\nChoose section:",
    "section_in_dev": "🚧 This section is under development...",
    
    "language_select": "🌐 Choose language / Обери мову:",
    "language_changed": "✅ Language changed!",
    
    # ========== TASKS ==========
    "tasks_today_title": "📋 <b>Today's Tasks</b> ({date})",
    "tasks_all_title": "📋 <b>All Tasks</b>",
    "tasks_inbox_title": "📥 <b>Inbox</b>",
    "tasks_history_title": "📜 <b>Tasks History</b>",
    "tasks_empty": "📭 No tasks",
    "tasks_completed": "✅ Completed: {done}/{total}",
    
    "filter_today": "📅 Today",
    "filter_all": "📋 All",
    "filter_history": "📜 History",
    "filter_active": "📌 Active",
    "filter_completed": "✅ Completed",
    
    "priority_urgent": "🔴 Urgent",
    "priority_high": "🟠 High",
    "priority_medium": "🟡 Medium",
    "priority_low": "🟢 Low",
    
    "task_add_title": "📝 <b>New Task</b>\n\nEnter title:",
    "task_add_description": "📝 Add description (or skip):",
    "task_add_priority": "🎯 Choose priority:",
    "task_add_deadline": "📅 Choose deadline:",
    "task_add_time": "⏰ Start time?",
    "task_add_duration": "⏱ Duration?",
    
    "deadline_today": "📅 Today",
    "deadline_tomorrow": "📆 Tomorrow",
    "deadline_week": "🗓 This week",
    "deadline_end_week": "📅 End of week",
    "deadline_end_month": "📅 End of month",
    "deadline_end_quarter": "📅 End of quarter",
    "deadline_end_year": "📅 End of year",
    "deadline_custom": "✏️ Enter date",
    "deadline_none": "➖ No deadline",
    
    "task_add_deadline_custom": "📅 Enter date (DD.MM.YYYY):",
    "task_add_time_custom": "⏰ Enter time (HH:MM):",
    "task_add_duration_custom": "⏱ Enter duration (minutes):",
    
    "time_none": "❌ No time",
    "time_custom": "✏️ Other time",
    "duration_15m": "15m",
    "duration_30m": "30m",
    "duration_45m": "45m",
    "duration_1h": "1h",
    "duration_1_5h": "1.5h",
    "duration_2h": "2h",
    "duration_3h": "3h",
    "duration_4h": "4h",
    "duration_custom": "✏️ Other",
    "hour_short": "h",
    "min_short": "m",
    
    "task_created_full": "✅ <b>Task created!</b>\n\n📝 {title}\n🎯 Priority: {priority}\n{deadline}{time}{duration}\n🆔 ID: {task_id}",
    "task_created_deadline": "📅 Deadline: {deadline}\n",
    "task_created_time": "⏰ Time: {time}\n",
    "task_created_duration": "⏱ Duration: {duration}\n",
    
    "task_done": "✅ Task #{task_id} completed!",
    "task_done_stats": "📊 Completed today: {count}",
    "task_deleted": "🗑 Task #{task_id} deleted.",
    "task_not_found": "❌ Task not found.",
    "task_undo_done": "✅ Completion undone.",
    
    "task_view_description": "📝 {description}",
    "task_view_deadline": "📅 Deadline: {deadline}",
    "task_view_time": "Time",
    "task_view_duration": "Duration",
    "task_view_overdue": " ⚠️ <i>overdue!</i>",
    
    "task_delete_confirm": "🗑 <b>Delete task?</b>",
    "what_next": "What's next?",
    
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
    
    # ========== GOALS v3 ==========
    "goals_title": "🎯 <b>My Goals</b>",
    "goals_empty": "📭 No goals yet. Add your first!",
    "goals_active_title": "🎯 <b>Active Goals</b>",
    "goals_completed_title": "✅ <b>Completed Goals</b>",
    "goals_all_title": "📊 <b>All Goals</b>",
    
    "goal_type_task": "Task",
    "goal_type_project": "Project",
    "goal_type_habit": "Habit",
    "goal_type_target": "Target",
    "goal_type_metric": "Metric",
    
    "goal_add_title": "🎯 What do you want to achieve?\n\nEnter title:",
    "goal_add_type": "📊 How will we track it?",
    "goal_add_parent": "🔗 Link to a project?",
    "goal_add_deadline": "📅 When is the deadline?",
    "goal_add_deadline_custom": "📅 Enter date (DD.MM.YYYY):",
    "goal_add_tags": "🏷 Add tags (optional):",
    "goal_add_subgoal_title": "➕ Subgoal title:",
    "goal_no_parent": "➖ No link",
    
    "goal_add_frequency": "📅 How often?",
    "goal_add_schedule_days": "📅 Which days? (1-7 or Mon,Tue,Wed...)",
    "frequency_daily": "📅 Daily",
    "frequency_weekdays": "📅 Weekdays",
    "frequency_3_per_week": "📅 3×/week",
    "frequency_custom": "📅 Pick days",
    "habit_done": "Done",
    "habit_skip": "Skip",
    "habit_add_title": "✅ What habit do you want to build?",
    "habit_logged": "Habit logged!",
    "habit_skipped": "Skipped (streak kept)",
    "habits_today": "Today's Habits",
    "habits_empty": "📭 No habits yet. Add your first!",
    "habits_marked": "habits marked",
    
    "goal_add_target_value": "🎯 What's the target? (number + unit)\n\nExample: 24 books",
    "goal_add_metric_range": "📊 What's the range? (min-max unit)\n\nExample: 75-80 kg",
    "add_entry": "Add entry",
    "add_entry_prompt": "Enter value:",
    "entry_added": "✅ Entry added!",
    "current": "Current",
    
    "streak": "Streak",
    "best": "Best",
    "range": "Range",
    "progress": "Progress",
    "deadline": "Deadline",
    "subgoals": "Subgoals",
    "add_subgoal": "Add subgoal",
    
    "goal_created": "✅ Goal created!",
    "goal_created_short": "Created!",
    "goal_completed": "🎉 Congratulations! Goal achieved!",
    "goal_restored": "🔄 Goal restored to active",
    "goal_deleted": "🗑 Goal deleted",
    "goal_not_found": "❌ Goal not found",
    "goal_delete_confirm": "⚠️ Delete this goal?",
    
    "btn_add_goal": "➕ Add goal",
    "btn_add_habit": "➕ Add habit",
    "btn_complete": "Complete",
    "mark_all_done": "Mark all done",
    
    "edit_field_target": "🎯 Target value",
    "edit_field_frequency": "📅 Frequency",
    "edit_field_tags": "🏷 Tags",
    
    # ========== ERRORS ==========
    "error_general": "❌ An error occurred. Try again.",
    "error_not_found": "❌ Not found.",
    "error_invalid_input": "❌ Invalid input.",
    "error_invalid_date": "❌ Invalid date format. Use DD.MM.YYYY",
    "error_invalid_time": "❌ Invalid time format. Use HH:MM",
    "error_invalid_duration": "❌ Invalid duration format.",
    "error_invalid_days": "❌ Invalid days format. Use 1-7 or Mon,Tue,Wed...",
    "error_invalid_target": "❌ Invalid format. Enter number + unit (24 books)",
    "error_invalid_range": "❌ Invalid format. Enter min-max unit (75-80 kg)",
    "error_invalid_number": "❌ Enter a number",
    
    # ========== ADDITIONAL v3 KEYS ==========
    "goal_type_label": "Type",
    "goal_type_task": "Task",
    "goal_type_project": "Project",
    "goal_type_habit": "Habit",
    "goal_type_target": "Target",
    "goal_type_metric": "Metric",
    "goal_type_detected": "💡 Looks like: {type_name}",
    "goals_stats": "📊 Active: {active} | Completed: {completed}",
    "goals_active_title": "🎯 <b>Active Goals</b>",
    "goals_completed_title": "✅ <b>Completed Goals</b>",
    "goals_all_title": "📊 <b>All Goals</b>",
    "goals_empty": "📭 No goals yet. Add one!",
    
    # Goal creation
    "goal_add_title": "🎯 What do you want to achieve?\n\nEnter title:",
    "goal_add_type": "📊 How will we track it?",
    "goal_add_parent": "🔗 Link to project?",
    "goal_add_deadline": "📅 When is the deadline?",
    "goal_add_deadline_custom": "📅 Enter date (DD.MM.YYYY):",
    "goal_no_parent": "➖ No link",
    "goal_add_frequency": "📅 How often?",
    "goal_add_schedule_days": "📅 Which days? (1-7 or Mon,Tue,Wed...)",
    "goal_add_target_value": "🎯 What's the target? (number + unit)\n\nExample: 24 books",
    "goal_add_metric_range": "📊 What range? (min-max unit)\n\nExample: 75-80 kg",
    "goal_created": "✅ Goal created!",
    
    # Frequency
    "freq_daily": "📅 Daily",
    "freq_weekdays": "📅 Weekdays",
    "freq_3_per_week": "📅 3×/week",
    "freq_custom": "📅 Choose days",
    "frequency": "Frequency",
    
    # Habits
    "habits_title": "Today's habits",
    "habits_progress": "Progress: {done}/{total} ({percent}%)",
    "habits_empty": "📭 No habits yet. Add one!",
    "habit_add_title": "✅ What habit do you want to build?",
    "habit_done": "✅ Habit done! 🔥 Streak: {streak}",
    "habit_skipped": "Skipped (streak saved)",
    
    # Entries
    "goal_add_entry": "➕ Enter value ({unit}):",
    "btn_add_entry": "➕ Add entry",
    "entry_added": "✅ Entry added!",
    
    # View
    "streak": "Streak",
    "best": "Best",
    "range": "Range",
    "progress": "Progress",
    "deadline": "Deadline",
    "current": "Current",
    "created": "Created",
    
    # Filters
    "filter_active": "📌 Active",
    "filter_completed": "✅ Completed",
    "filter_all": "📋 All",
    
    # Edit
    "goal_edit_choose_field": "✏️ <b>Editing:</b> {title}\n\nWhat to change?",
    "goal_edit_title": "📝 Enter new title:",
    "goal_edit_description": "📝 Enter new description:",
    "goal_edit_deadline": "📅 Enter new deadline (DD.MM.YYYY):",
    "goal_edit_target_value": "🎯 Enter new target value:",
    "goal_updated": "✅ Goal updated!",
    "goal_completed": "🎉 Congratulations! Goal achieved!",
    "goal_restored": "🔄 Goal restored to active",
    "goal_deleted": "🗑 Goal deleted",
    
    # Domains
    "domain_health": "Health",
    "domain_learning": "Learning",
    "domain_career": "Career",
    "domain_finance": "Finance",
    "domain_relationships": "Relationships",
    "domain_growth": "Growth",
    
    # Deadlines
    "deadline_end_week": "📅 End of week",
    "deadline_end_month": "📅 End of month",
    "deadline_end_quarter": "📅 End of quarter",
    "deadline_end_year": "📅 End of year",
    "deadline_custom": "✏️ Enter date",
    "deadline_none": "➖ No deadline",
    
    # Buttons
    "btn_progress": "📈 Progress",
    
    # ========== NEW KEYS ==========
    "time": "Time",
    "duration": "Duration",
    "minutes": "min",
    "goal_add_reminder_time": "⏰ What time to remind? (HH:MM or 'skip')",
    "goal_add_duration": "⏱ How long does it take? (minutes or 'skip')\n\nExample: 30, 1h",
    "no_subgoals": "No subgoals yet",
    "hint_add_subgoal": "Add a habit, metric or task to this project",
    "freq_custom": "Custom days",
    
    # ========== TODAY DASHBOARD ==========
    "today_title": "Today",
    "time_blocks": "Time blocks",
    "skipped_today": "Skipped today",
    "scheduled": "Scheduled",
    "tasks": "Tasks",
    "habits": "Habits",
    "skip": "Skip",
    "skipped": "Skipped!",
    "restored": "Restored!",
    "refreshed": "Refreshed!",
    "rescheduled": "Rescheduled",
    "manage_blocks": "Manage blocks",
    "no_blocks": "No time blocks yet. Add school, work, etc.",
    "add_block": "Add block",
    "block_add_title": "🏢 Block name?\n\nExample: School, Work, Training",
    "block_add_start": "⏰ Start time? (HH:MM)\n\nExample: 08:30",
    "block_add_end": "⏰ End time? (HH:MM)\n\nExample: 12:30",
    "block_add_days": "📅 Which days? (1-7 or Mon,Tue,Wed...)\n\nExample: 1,2,3,4",
    "block_created": "✅ Block '{title}' created!",
    "deleted": "Deleted!",
    "btn_add_task": "Add task",
}
