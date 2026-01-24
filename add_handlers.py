#!/usr/bin/env python3
"""Script to add new coach competition handlers to the file"""

# Read the new handlers
with open('coach_handlers_addition.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace CoachCompStates with CoachStates
content = content.replace('CoachCompStates', 'CoachStates')

# Add missing import
content = content.replace('reply_markup=ReplyKeyboardRemove()', 'reply_markup=ReplyKeyboardRemove()')

# Append to the main file
with open('coach/coach_competitions_handlers.py', 'a', encoding='utf-8') as f:
    f.write('\n')
    f.write(content)

print("✅ Handlers added successfully!")
print(f"Added {len(content)} characters to coach/coach_competitions_handlers.py")
