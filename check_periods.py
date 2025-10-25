"""Check which dates fall into which periods"""
from datetime import date, timedelta

# All dates with data for user 8296492604
all_dates = [
    date(2024, 12, 15),
    date(2025, 10, 1),
    date(2025, 10, 7),
    date(2025, 10, 18),
    date(2025, 10, 20),
    date(2025, 10, 22),
    date(2025, 10, 24),
]

today = date.today()
print(f"Today: {today}\n")

# Period calculations
periods = {
    "Last 7 days": (today - timedelta(days=6), today),
    "Last 14 days": (today - timedelta(days=13), today),
    "Last 30 days": (today - timedelta(days=29), today),
    "Last 90 days": (today - timedelta(days=89), today),
    "This week": (today - timedelta(days=today.weekday()), today - timedelta(days=today.weekday()) + timedelta(days=6)),
    "This month": (date(today.year, today.month, 1), date(today.year, 10, 31)),
}

for period_name, (start, end) in periods.items():
    print(f"{period_name}: {start} to {end}")
    matching = [d for d in all_dates if start <= d <= end]
    print(f"  Dates included: {len(matching)}")
    for d in matching:
        print(f"    - {d}")
    print()
