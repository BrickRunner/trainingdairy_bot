#!/usr/bin/env python3
"""Fix duplicate handlers in coach_competitions_handlers.py"""

# Read the file
with open('coach/coach_competitions_handlers.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and remove second duplicate (lines 4507-4577)
# We'll keep only lines up to 4507
output_lines = []
skip = False
skip_start = 4506  # 0-indexed, so line 4507
skip_end = 4577

for i, line in enumerate(lines):
    line_num = i + 1
    if line_num == skip_start:
        skip = True
    if line_num > skip_end:
        skip = False

    if not skip:
        output_lines.append(line)

# Write back
with open('coach/coach_competitions_handlers.py', 'w', encoding='utf-8') as f:
    f.writelines(output_lines)

print(f"✅ Removed duplicate lines {skip_start}-{skip_end}")
print(f"Original: {len(lines)} lines, New: {len(output_lines)} lines")
print(f"Removed: {len(lines) - len(output_lines)} lines")
