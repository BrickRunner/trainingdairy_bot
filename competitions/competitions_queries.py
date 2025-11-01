"""
Функции для работы с соревнованиями в базе данных
"""

import aiosqlite
import os
import json
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from utils.time_formatter import normalize_time

# Путь к базе данных
DB_PATH = os.getenv('DB_PATH', 'bot_data.db')


# ========== CRUD ДЛЯ СОРЕВНОВАНИЙ ==========

async def add_competition(data: Dict[str, Any]) -> int:
    """
    Добавить соревнование в базу данных

    Args:
        data: Словарь с данными соревнования
              Обязательные поля: name, date
              Опциональные: city, country, location, distances, type, description,
                          official_url, organizer, registration_status, status,
                          created_by, is_official, source_url

    Returns:
        ID созданного соревнования
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO competitions
            (name, date, city, country, location, distances, type, description,
             official_url, organizer, registration_status, status, created_by,
             is_official, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data['name'],
                data['date'],
                data.get('city'),
                data.get('country', 'Россия'),
                data.get('location'),
                json.dumps(data.get('distances', [])) if isinstance(data.get('distances'), list) else data.get('distances'),
                data.get('type'),
                data.get('description'),
                data.get('official_url'),
                data.get('organizer'),
                data.get('registration_status', 'unknown'),
                data.get('status', 'upcoming'),
                data.get('created_by'),
                data.get('is_official', 1),
                data.get('source_url')
            )
        )
        await db.commit()
        return cursor.lastrowid


async def get_competition(competition_id: int) -> Optional[Dict[str, Any]]:
    """
    Получить соревнование по ID

    Args:
        competition_id: ID соревнования

    Returns:
        Словарь с данными соревнования или None
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM competitions WHERE id = ?",
            (competition_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                competition = dict(row)
                # Парсим JSON поля
                if competition.get('distances'):
                    try:
                        competition['distances'] = json.loads(competition['distances'])
                    except:
                        pass
                return competition
            return None


async def get_upcoming_competitions(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Получить список предстоящих соревнований

    Args:
        limit: Максимальное количество соревнований
        offset: Смещение для пагинации

    Returns:
        Список словарей с соревнованиями
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        today = date.today().strftime('%Y-%m-%d')

        # Только официальные соревнования (is_official = 1)
        async with db.execute(
            """
            SELECT * FROM competitions
            WHERE date >= ? AND status IN ('upcoming', 'ongoing') AND is_official = 1
            ORDER BY date ASC
            LIMIT ? OFFSET ?
            """,
            (today, limit, offset)
        ) as cursor:
            rows = await cursor.fetchall()
            competitions = []
            for row in rows:
                comp = dict(row)
                # Парсим JSON поля
                if comp.get('distances'):
                    try:
                        comp['distances'] = json.loads(comp['distances'])
                    except:
                        pass
                competitions.append(comp)
            return competitions


async def search_competitions(
    query: str = None,
    city: str = None,
    month: int = None,
    year: int = None,
    competition_type: str = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Поиск соревнований по различным критериям

    Args:
        query: Поисковый запрос (по названию)
        city: Город
        month: Месяц (1-12)
        year: Год
        competition_type: Тип соревнования
        limit: Максимальное количество результатов

    Returns:
        Список найденных соревнований
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Строим динамический запрос
        # Только официальные соревнования (is_official = 1)
        conditions = ["date >= date('now')", "is_official = 1"]
        params = []

        if query:
            conditions.append("(name LIKE ? OR city LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])

        if city:
            conditions.append("city = ?")
            params.append(city)

        if month and year:
            conditions.append("strftime('%Y-%m', date) = ?")
            params.append(f"{year:04d}-{month:02d}")
        elif year:
            conditions.append("strftime('%Y', date) = ?")
            params.append(str(year))

        if competition_type:
            conditions.append("type = ?")
            params.append(competition_type)

        where_clause = " AND ".join(conditions)
        params.append(limit)

        async with db.execute(
            f"""
            SELECT * FROM competitions
            WHERE {where_clause}
            ORDER BY date ASC
            LIMIT ?
            """,
            params
        ) as cursor:
            rows = await cursor.fetchall()
            competitions = []
            for row in rows:
                comp = dict(row)
                if comp.get('distances'):
                    try:
                        comp['distances'] = json.loads(comp['distances'])
                    except:
                        pass
                competitions.append(comp)
            return competitions


async def update_competition(competition_id: int, data: Dict[str, Any]) -> bool:
    """
    Обновить данные соревнования

    Args:
        competition_id: ID соревнования
        data: Словарь с полями для обновления

    Returns:
        True если обновление прошло успешно
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Формируем SET часть запроса
        set_parts = []
        params = []

        for key, value in data.items():
            if key == 'distances' and isinstance(value, list):
                value = json.dumps(value)
            set_parts.append(f"{key} = ?")
            params.append(value)

        set_parts.append("updated_at = CURRENT_TIMESTAMP")
        params.append(competition_id)

        cursor = await db.execute(
            f"""
            UPDATE competitions
            SET {', '.join(set_parts)}
            WHERE id = ?
            """,
            params
        )
        await db.commit()
        return cursor.rowcount > 0


# ========== УЧАСТИЕ В СОРЕВНОВАНИЯХ ==========

async def register_for_competition(
    user_id: int,
    competition_id: int,
    distance: float,
    target_time: str = None
) -> int:
    """
    Зарегистрировать пользователя на соревнование

    Args:
        user_id: ID пользователя
        competition_id: ID соревнования
        distance: Выбранная дистанция
        target_time: Целевое время (опционально)

    Returns:
        ID записи участия
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO competition_participants
            (user_id, competition_id, distance, target_time, status)
            VALUES (?, ?, ?, ?, 'registered')
            """,
            (user_id, competition_id, distance, target_time)
        )
        await db.commit()
        return cursor.lastrowid


async def unregister_from_competition(
    user_id: int,
    competition_id: int,
    distance: float = None
) -> bool:
    """
    Отменить регистрацию на соревнование

    Args:
        user_id: ID пользователя
        competition_id: ID соревнования
        distance: Дистанция (если None, удаляются все регистрации)

    Returns:
        True если удаление прошло успешно
    """
    async with aiosqlite.connect(DB_PATH) as db:
        if distance is not None:
            cursor = await db.execute(
                """
                DELETE FROM competition_participants
                WHERE user_id = ? AND competition_id = ? AND distance = ?
                """,
                (user_id, competition_id, distance)
            )
        else:
            cursor = await db.execute(
                """
                DELETE FROM competition_participants
                WHERE user_id = ? AND competition_id = ?
                """,
                (user_id, competition_id)
            )
        await db.commit()
        return cursor.rowcount > 0


async def get_user_competitions(
    user_id: int,
    status_filter: str = None
) -> List[Dict[str, Any]]:
    """
    Получить соревнования пользователя

    Args:
        user_id: ID пользователя
        status_filter: Фильтр по статусу ('upcoming', 'finished')

    Returns:
        Список соревнований с данными участия
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if status_filter == 'upcoming':
            date_condition = "c.date >= date('now')"
        elif status_filter == 'finished':
            date_condition = "c.date < date('now')"
        else:
            date_condition = "1=1"

        async with db.execute(
            f"""
            SELECT c.*, cp.distance, cp.target_time, cp.finish_time,
                   cp.place_overall, cp.place_age_category, cp.age_category,
                   cp.result_comment, cp.result_photo, cp.status as participant_status,
                   cp.registered_at, cp.result_added_at
            FROM competitions c
            JOIN competition_participants cp ON c.id = cp.competition_id
            WHERE cp.user_id = ? AND {date_condition}
            ORDER BY c.date DESC
            """,
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            competitions = []
            for row in rows:
                comp = dict(row)
                if comp.get('distances'):
                    try:
                        comp['distances'] = json.loads(comp['distances'])
                    except:
                        pass
                competitions.append(comp)
            return competitions


async def is_user_registered(user_id: int, competition_id: int, distance: float = None) -> bool:
    """
    Проверить зарегистрирован ли пользователь на соревнование

    Args:
        user_id: ID пользователя
        competition_id: ID соревнования
        distance: Конкретная дистанция (опционально)

    Returns:
        True если зарегистрирован
    """
    async with aiosqlite.connect(DB_PATH) as db:
        if distance is not None:
            async with db.execute(
                """
                SELECT COUNT(*) FROM competition_participants
                WHERE user_id = ? AND competition_id = ? AND distance = ?
                """,
                (user_id, competition_id, distance)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] > 0
        else:
            async with db.execute(
                """
                SELECT COUNT(*) FROM competition_participants
                WHERE user_id = ? AND competition_id = ?
                """,
                (user_id, competition_id)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] > 0


async def add_competition_result(
    user_id: int,
    competition_id: int,
    distance: float,
    finish_time: str,
    place_overall: int = None,
    place_age_category: int = None,
    age_category: str = None,
    result_comment: str = None,
    result_photo: str = None
) -> bool:
    """
    Добавить результат соревнования

    Args:
        user_id: ID пользователя
        competition_id: ID соревнования
        distance: Дистанция
        finish_time: Финишное время
        place_overall: Место в общем зачёте
        place_age_category: Место в возрастной категории
        age_category: Возрастная категория
        result_comment: Комментарий
        result_photo: Путь к фото

    Returns:
        True если добавление прошло успешно
    """
    # Нормализуем время перед сохранением
    normalized_time = normalize_time(finish_time)

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            UPDATE competition_participants
            SET finish_time = ?,
                place_overall = ?,
                place_age_category = ?,
                age_category = ?,
                result_comment = ?,
                result_photo = ?,
                status = 'finished',
                result_added_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND competition_id = ? AND distance = ?
            """,
            (
                normalized_time, place_overall, place_age_category, age_category,
                result_comment, result_photo, user_id, competition_id, distance
            )
        )
        await db.commit()

        # Проверяем и обновляем личный рекорд
        if cursor.rowcount > 0:
            await update_personal_record(user_id, distance, normalized_time, competition_id)

        return cursor.rowcount > 0


async def get_competition_participants_count(competition_id: int) -> int:
    """
    Получить количество участников соревнования из бота

    Args:
        competition_id: ID соревнования

    Returns:
        Количество участников
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(DISTINCT user_id) FROM competition_participants WHERE competition_id = ?",
            (competition_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def get_user_competition_registration(user_id: int, competition_id: int) -> Optional[Dict[str, Any]]:
    """
    Получить регистрацию пользователя на соревнование

    Args:
        user_id: ID пользователя
        competition_id: ID соревнования

    Returns:
        Словарь с данными регистрации или None
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT * FROM competition_participants
            WHERE user_id = ? AND competition_id = ?
            """,
            (user_id, competition_id)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


# ========== ЛИЧНЫЕ РЕКОРДЫ ==========

async def update_personal_record(
    user_id: int,
    distance: float,
    time: str,
    competition_id: int = None
) -> bool:
    """
    Обновить личный рекорд пользователя если новое время лучше

    Args:
        user_id: ID пользователя
        distance: Дистанция
        time: Время (HH:MM:SS)
        competition_id: ID соревнования

    Returns:
        True если рекорд был обновлён
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Получаем текущий рекорд
        async with db.execute(
            "SELECT best_time FROM personal_records WHERE user_id = ? AND distance = ?",
            (user_id, distance)
        ) as cursor:
            row = await cursor.fetchone()

        # Сравниваем времена
        if row:
            current_best = row[0]
            # Простое сравнение строк времени работает для формата HH:MM:SS
            if time < current_best:
                # Обновляем рекорд
                await db.execute(
                    """
                    UPDATE personal_records
                    SET best_time = ?, competition_id = ?, date = date('now'), updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND distance = ?
                    """,
                    (time, competition_id, user_id, distance)
                )
                await db.commit()
                return True
        else:
            # Создаём новый рекорд
            await db.execute(
                """
                INSERT INTO personal_records (user_id, distance, best_time, competition_id, date)
                VALUES (?, ?, ?, ?, date('now'))
                """,
                (user_id, distance, time, competition_id)
            )
            await db.commit()
            return True

        return False


async def get_user_personal_records(user_id: int) -> Dict[float, Dict[str, Any]]:
    """
    Получить все личные рекорды пользователя

    Args:
        user_id: ID пользователя

    Returns:
        Словарь {дистанция: {best_time, date, competition_id}}
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT pr.*, c.name as competition_name
            FROM personal_records pr
            LEFT JOIN competitions c ON pr.competition_id = c.id
            WHERE pr.user_id = ?
            ORDER BY pr.distance ASC
            """,
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            records = {}
            for row in rows:
                record = dict(row)
                records[record['distance']] = {
                    'best_time': record['best_time'],
                    'date': record['date'],
                    'competition_id': record['competition_id'],
                    'competition_name': record['competition_name']
                }
            return records


async def get_competition_statistics(competition_id: int) -> Dict[str, Any]:
    """
    Получить статистику по соревнованию

    Args:
        competition_id: ID соревнования

    Returns:
        Словарь со статистикой
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Общее количество участников
        async with db.execute(
            "SELECT COUNT(DISTINCT user_id) as total FROM competition_participants WHERE competition_id = ?",
            (competition_id,)
        ) as cursor:
            total_row = await cursor.fetchone()
            total_participants = total_row[0] if total_row else 0

        # Количество с результатами
        async with db.execute(
            "SELECT COUNT(*) as finished FROM competition_participants WHERE competition_id = ? AND status = 'finished'",
            (competition_id,)
        ) as cursor:
            finished_row = await cursor.fetchone()
            finished_participants = finished_row[0] if finished_row else 0

        # Статистика по дистанциям
        async with db.execute(
            """
            SELECT distance, COUNT(*) as count
            FROM competition_participants
            WHERE competition_id = ?
            GROUP BY distance
            """,
            (competition_id,)
        ) as cursor:
            distance_rows = await cursor.fetchall()
            distances_stats = {row['distance']: row['count'] for row in distance_rows}

        return {
            'total_participants': total_participants,
            'finished_participants': finished_participants,
            'distances_stats': distances_stats
        }
