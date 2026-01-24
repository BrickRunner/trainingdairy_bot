"""
Проверка данных в БД для раздела "Мои соревнования"
"""

import asyncio
import aiosqlite
import os
from datetime import date
import json

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

async def check_competitions():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        print("=" * 80)
        print("ПРОВЕРКА ДАННЫХ В ТАБЛИЦЕ competition_participants")
        print("=" * 80)

        # Получаем всех пользователей с соревнованиями
        async with db.execute(
            "SELECT DISTINCT user_id FROM competition_participants"
        ) as cursor:
            users = await cursor.fetchall()

        print(f"\n✓ Найдено пользователей с соревнованиями: {len(users)}\n")

        for user_row in users:
            user_id = user_row[0]
            print(f"\n{'='*80}")
            print(f"ПОЛЬЗОВАТЕЛЬ ID: {user_id}")
            print(f"{'='*80}\n")

            # Получаем все записи из competition_participants для этого пользователя
            async with db.execute(
                """
                SELECT cp.*, c.name, c.date, c.status as comp_status
                FROM competition_participants cp
                JOIN competitions c ON c.id = cp.competition_id
                WHERE cp.user_id = ?
                ORDER BY c.date
                """,
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()

            print(f"Всего записей в competition_participants: {len(rows)}\n")

            for i, row in enumerate(rows, 1):
                comp_dict = dict(row)
                print(f"{i}. {comp_dict['name']}")
                print(f"   ID соревнования: {comp_dict['competition_id']}")
                print(f"   Дата: {comp_dict['date']}")
                print(f"   Дистанция: {comp_dict['distance']}")
                print(f"   Название дистанции: {comp_dict['distance_name']}")
                print(f"   Статус участника: {comp_dict['status']}")
                print(f"   Статус предложения: {comp_dict['proposal_status']}")
                print(f"   Предложено тренером: {comp_dict['proposed_by_coach']}")
                print(f"   Целевое время: {comp_dict['target_time']}")
                print(f"   Финишное время: {comp_dict['finish_time']}")
                print(f"   Статус соревнования в БД: {comp_dict['comp_status']}")
                print()

            # Проверяем, какие соревнования должны показываться в "Мои соревнования"
            today = date.today().strftime('%Y-%m-%d')

            print(f"\n--- ФИЛЬТРАЦИЯ ДЛЯ 'МОИ СОРЕВНОВАНИЯ' (upcoming) ---")
            print(f"Текущая дата: {today}\n")

            # Тестируем запрос get_user_competitions с фильтром upcoming
            async with db.execute(
                """
                SELECT c.*, cp.distance, cp.distance_name, cp.target_time, cp.finish_time,
                       cp.place_overall, cp.place_age_category, cp.age_category,
                       cp.result_comment, cp.result_photo, cp.heart_rate, cp.qualification, cp.status as participant_status,
                       cp.registered_at, cp.result_added_at, cp.proposal_status
                FROM competitions c
                JOIN competition_participants cp ON c.id = cp.competition_id
                WHERE cp.user_id = ? AND c.date >= date('now')
                  AND (cp.proposal_status IS NULL
                       OR cp.proposal_status NOT IN ('pending', 'rejected'))
                ORDER BY c.date ASC
                """,
                (user_id,)
            ) as cursor:
                upcoming_rows = await cursor.fetchall()

            print(f"✓ Соревнования, которые ДОЛЖНЫ ПОКАЗЫВАТЬСЯ (get_user_competitions):")
            print(f"  Количество: {len(upcoming_rows)}\n")

            for i, row in enumerate(upcoming_rows, 1):
                comp_dict = dict(row)
                print(f"  {i}. {comp_dict['name']}")
                print(f"     Дата: {comp_dict['date']}")
                print(f"     Дистанция: {comp_dict['distance']} / {comp_dict['distance_name']}")
                print(f"     Статус: {comp_dict['participant_status']}")
                print(f"     Proposal status: {comp_dict['proposal_status']}")
                print()

            # Тестируем запрос get_student_competitions_for_coach (который сейчас используется)
            async with db.execute(
                """
                SELECT c.*, cp.distance, cp.distance_name, cp.target_time, cp.finish_time,
                       cp.place_overall, cp.place_age_category, cp.age_category,
                       cp.result_comment, cp.result_photo, cp.heart_rate, cp.qualification, cp.status as participant_status,
                       cp.registered_at, cp.result_added_at, cp.proposal_status,
                       cp.proposed_by_coach, cp.proposed_by_coach_id
                FROM competitions c
                JOIN competition_participants cp ON c.id = cp.competition_id
                WHERE cp.user_id = ? AND c.date >= date('now')
                ORDER BY c.date ASC
                """,
                (user_id,)
            ) as cursor:
                coach_rows = await cursor.fetchall()

            print(f"\n✗ Соревнования, которые ПОКАЗЫВАЮТСЯ СЕЙЧАС (get_student_competitions_for_coach):")
            print(f"  Количество: {len(coach_rows)}\n")

            for i, row in enumerate(coach_rows, 1):
                comp_dict = dict(row)
                print(f"  {i}. {comp_dict['name']}")
                print(f"     Дата: {comp_dict['date']}")
                print(f"     Дистанция: {comp_dict['distance']} / {comp_dict['distance_name']}")
                print(f"     Статус: {comp_dict['participant_status']}")
                print(f"     Proposal status: {comp_dict['proposal_status']}")
                print()

            # Показываем разницу
            if len(upcoming_rows) != len(coach_rows):
                print(f"\n⚠️  ПРОБЛЕМА НАЙДЕНА!")
                print(f"   Правильный запрос возвращает: {len(upcoming_rows)} соревнований")
                print(f"   Текущий запрос возвращает: {len(coach_rows)} соревнований")
                print(f"   Разница: {len(coach_rows) - len(upcoming_rows)}")

                # Показываем лишние записи
                upcoming_ids = {(r['id'], r['distance']) for r in [dict(r) for r in upcoming_rows]}
                coach_ids = {(r['id'], r['distance']) for r in [dict(r) for r in coach_rows]}
                extra_ids = coach_ids - upcoming_ids

                if extra_ids:
                    print(f"\n   Лишние соревнования (не должны показываться):")
                    for comp_id, distance in extra_ids:
                        for row in coach_rows:
                            row_dict = dict(row)
                            if row_dict['id'] == comp_id and row_dict['distance'] == distance:
                                print(f"   - {row_dict['name']} (proposal_status={row_dict['proposal_status']})")

if __name__ == "__main__":
    asyncio.run(check_competitions())
