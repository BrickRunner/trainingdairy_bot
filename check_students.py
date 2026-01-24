#!/usr/bin/env python3
"""Проверка учеников в базе данных"""

import asyncio
import aiosqlite
import os

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

async def check_students():
    """Проверить учеников в БД"""

    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем таблицу coach_links
        print("=" * 80)
        print("COACH_LINKS TABLE")
        print("=" * 80)

        async with db.execute(
            "SELECT coach_id, student_id, status, created_at, coach_nickname FROM coach_links"
        ) as cursor:
            rows = await cursor.fetchall()
            print(f"Total links: {len(rows)}\n")
            for row in rows:
                print(f"Coach ID: {row[0]}, Student ID: {row[1]}, Status: {row[2]}")
                print(f"  Created: {row[3]}, Nickname: {row[4]}")
                print()

        # Проверяем учеников для каждого тренера
        print("=" * 80)
        print("STUDENTS PER COACH")
        print("=" * 80)

        async with db.execute(
            "SELECT DISTINCT coach_id FROM coach_links WHERE status = 'active'"
        ) as cursor:
            coaches = await cursor.fetchall()

            for coach_row in coaches:
                coach_id = coach_row[0]
                print(f"\nCoach ID: {coach_id}")

                # Запрос из get_coach_students
                async with db.execute(
                    """
                    SELECT
                        u.id,
                        u.username,
                        s.name,
                        cl.created_at,
                        cl.coach_nickname
                    FROM coach_links cl
                    JOIN users u ON u.id = cl.student_id
                    LEFT JOIN user_settings s ON s.user_id = cl.student_id
                    WHERE cl.coach_id = ? AND cl.status = 'active'
                    ORDER BY cl.created_at DESC
                    """,
                    (coach_id,)
                ) as cursor2:
                    students = await cursor2.fetchall()
                    print(f"  Students count: {len(students)}")

                    for student in students:
                        print(f"    - Student ID: {student[0]}")
                        print(f"      Username: {student[1]}")
                        print(f"      Name (user_settings): {student[2]}")
                        print(f"      Created at: {student[3]}")
                        print(f"      Coach nickname: {student[4]}")

                        # Вычисляем отображаемое имя как в коде
                        display_name = student[4] or student[2] or student[1]
                        print(f"      Display name: {display_name}")
                        print()

if __name__ == "__main__":
    asyncio.run(check_students())
