"""
Test script to verify competition reminder timing
"""
import asyncio
import aiosqlite
import os
from datetime import datetime, timedelta, date

DB_PATH = os.getenv('DB_PATH', 'bot_data.db')


async def check_reminder_timing():
    """Check when reminders are scheduled and sent"""

    print("=" * 60)
    print("COMPETITION REMINDER TIMING REPORT")
    print("=" * 60)
    print()

    # 1. Check reminder configuration
    print("1. REMINDER CONFIGURATION (from reminder_scheduler.py)")
    print("-" * 60)
    reminder_periods = {
        '30days': 30,
        '14days': 14,
        '7days': 7,
        '3days': 3,
        '1day': 1
    }
    print("Reminders are sent at the following intervals before competition:")
    for reminder_type, days_before in reminder_periods.items():
        print(f"  • {reminder_type}: {days_before} days before competition")
    print(f"  • result_input: 1 day AFTER competition")
    print()

    # 2. Check sending time
    print("2. SENDING TIME")
    print("-" * 60)
    print("According to reminder_scheduler.py lines 259-261:")
    print("  • Reminders are checked every 5 minutes")
    print("  • Reminders are SENT at 9:00 AM (when hour == 9 and minute < 5)")
    print("  • This means reminders send between 9:00-9:04 AM daily")
    print()

    # 3. Check actual reminders in database
    print("3. ACTUAL REMINDERS IN DATABASE")
    print("-" * 60)

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            # Get all reminders
            async with db.execute(
                """
                SELECT
                    r.id,
                    r.user_id,
                    r.reminder_type,
                    r.scheduled_date,
                    r.sent,
                    r.sent_at,
                    c.name as competition_name,
                    c.date as competition_date
                FROM competition_reminders r
                JOIN competitions c ON r.competition_id = c.id
                ORDER BY r.scheduled_date, r.reminder_type
                """
            ) as cursor:
                reminders = await cursor.fetchall()

                if not reminders:
                    print("No reminders found in database.")
                else:
                    print(f"Found {len(reminders)} reminder(s):\n")

                    for reminder in reminders:
                        comp_date = datetime.strptime(reminder['competition_date'], '%Y-%m-%d').date()
                        sched_date = datetime.strptime(reminder['scheduled_date'], '%Y-%m-%d').date()
                        days_diff = (comp_date - sched_date).days

                        status = "✅ SENT" if reminder['sent'] else "⏳ PENDING"
                        sent_info = f"on {reminder['sent_at']}" if reminder['sent'] else ""

                        print(f"Reminder #{reminder['id']}")
                        print(f"  Competition: {reminder['competition_name']}")
                        print(f"  Competition Date: {reminder['competition_date']}")
                        print(f"  Type: {reminder['reminder_type']}")
                        print(f"  Scheduled Date: {reminder['scheduled_date']}")

                        if reminder['reminder_type'] != 'result_input':
                            print(f"  Days Before Competition: {days_diff}")
                        else:
                            print(f"  Days After Competition: {abs(days_diff)}")

                        print(f"  Status: {status} {sent_info}")
                        print()

    except Exception as e:
        print(f"Error accessing database: {e}")

    # 4. Example timeline
    print("4. EXAMPLE TIMELINE")
    print("-" * 60)
    example_date = date.today() + timedelta(days=35)
    print(f"If you register for a competition on {example_date.strftime('%Y-%m-%d')}:")
    print(f"  • 30 days before ({(example_date - timedelta(days=30)).strftime('%Y-%m-%d')}): Reminder at 9:00 AM")
    print(f"  • 14 days before ({(example_date - timedelta(days=14)).strftime('%Y-%m-%d')}): Reminder at 9:00 AM")
    print(f"  • 7 days before  ({(example_date - timedelta(days=7)).strftime('%Y-%m-%d')}): Reminder at 9:00 AM")
    print(f"  • 3 days before  ({(example_date - timedelta(days=3)).strftime('%Y-%m-%d')}): Reminder at 9:00 AM")
    print(f"  • 1 day before   ({(example_date - timedelta(days=1)).strftime('%Y-%m-%d')}): Reminder at 9:00 AM")
    print(f"  • Competition day: {example_date.strftime('%Y-%m-%d')}")
    print(f"  • 1 day after    ({(example_date + timedelta(days=1)).strftime('%Y-%m-%d')}): Result input reminder at 9:00 AM")
    print()

    print("=" * 60)
    print("REPORT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(check_reminder_timing())
