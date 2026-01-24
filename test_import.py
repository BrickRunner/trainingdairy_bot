#!/usr/bin/env python3
"""Тест импорта всех модулей"""

print("Testing imports...")

try:
    print("1. Importing coach.coach_handlers...")
    from coach.coach_handlers import router as coach_router
    print("   ✓ OK")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

try:
    print("2. Importing coach.coach_competitions_handlers...")
    from coach.coach_competitions_handlers import router as coach_competitions_router
    print("   ✓ OK")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

try:
    print("3. Importing coach.coach_queries...")
    from coach.coach_queries import get_coach_students
    print("   ✓ OK")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

try:
    print("4. Importing bot.fsm...")
    from bot.fsm import CoachStates
    print("   ✓ OK")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

print("\nAll imports completed!")
