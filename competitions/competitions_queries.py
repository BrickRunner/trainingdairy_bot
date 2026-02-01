"""
Функции для работы с соревнованиями в базе данных
"""

import aiosqlite
import os
import json
import logging
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from utils.time_formatter import normalize_time

# Логгер
logger = logging.getLogger(__name__)

# Путь к базе данных
DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


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
            (name, date, city, country, location, distances, type, sport_type, description,
             official_url, organizer, registration_status, status, created_by,
             is_official, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data['name'],
                data['date'],
                data.get('city'),
                data.get('country', 'Россия'),
                data.get('location'),
                json.dumps(data.get('distances', [])) if isinstance(data.get('distances'), list) else data.get('distances'),
                data.get('type'),
                data.get('sport_type', 'бег'),
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


async def get_or_create_competition_from_api(api_comp: Dict[str, Any]) -> int:
    """
    Получить БД ID соревнования из API данных или создать новую запись если не существует

    Args:
        api_comp: Словарь с данными соревнования из API
                  Обязательные поля: id, title, date, url

    Returns:
        Integer ID соревнования в БД
    """
    source_url = api_comp.get('url', '')

    # Проверяем существование соревнования по source_url
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, name FROM competitions WHERE source_url = ? AND source_url != ''",
            (source_url,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                # Соревнование уже существует - обновляем название если изменилось
                existing_id = row['id']
                existing_name = row['name']
                new_name = api_comp.get('title', api_comp.get('name', existing_name))

                # Обновляем название если оно изменилось
                if new_name and new_name != existing_name:
                    await db.execute(
                        "UPDATE competitions SET name = ? WHERE id = ?",
                        (new_name, existing_id)
                    )
                    await db.commit()
                    logger.info(f"Updated competition name: '{existing_name}' -> '{new_name}' (ID: {existing_id})")

                return existing_id

    # Соревнование не найдено - создаем новое
    # Преобразуем данные API в формат для add_competition

    # Парсим дату (может быть в формате ISO с временем)
    comp_date = api_comp.get('date', '')
    if 'T' in comp_date:
        comp_date = comp_date.split('T')[0]

    # Преобразуем distances в нужный формат
    distances_data = api_comp.get('distances', [])
    if isinstance(distances_data, list) and distances_data:
        # API может возвращать [{"name": "5 км", "distance": 5.0}, ...]
        # Извлекаем только числовые значения дистанций
        distances = []
        for d in distances_data:
            if isinstance(d, dict):
                dist_val = d.get('distance')
                if dist_val:
                    distances.append(dist_val)
            elif isinstance(d, (int, float)):
                distances.append(d)
    else:
        distances = []

    # Определяем organizer по URL
    organizer = ''
    if 'russiarunning' in source_url.lower():
        organizer = 'Russia Running'
    elif 'timerman' in source_url.lower():
        organizer = 'Timerman'
    elif 'heroleague' in source_url.lower():
        organizer = 'HeroLeague'
    elif 'reg.place' in source_url.lower() or 'regplace' in source_url.lower():
        organizer = 'reg.place'

    comp_data = {
        'name': api_comp.get('title', api_comp.get('name', 'Без названия')),
        'date': comp_date,
        'city': api_comp.get('city', ''),
        'country': 'Россия',
        'location': api_comp.get('place', ''),
        'distances': distances,
        'type': api_comp.get('type', ''),
        'description': api_comp.get('description', ''),
        'official_url': source_url,
        'organizer': organizer,
        'registration_status': 'unknown',
        'status': 'upcoming',
        'created_by': None,
        'is_official': 1,
        'source_url': source_url,
        'sport_type': api_comp.get('sport_code', 'бег')
    }

    db_id = await add_competition(comp_data)
    logger.info(f"Created competition in DB: {comp_data['name']} with DB ID: {db_id} (API ID: {api_comp.get('id')})")
    return db_id


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


async def get_student_competitions_for_coach(
    student_id: int,
    status_filter: str = None
) -> List[Dict[str, Any]]:
    """
    Получить соревнования ученика для отображения тренеру
    В отличие от get_user_competitions, показывает ВСЕ соревнования,
    включая pending proposals

    Args:
        student_id: ID ученика
        status_filter: Фильтр по статусу ('upcoming', 'finished')

    Returns:
        Список соревнований с данными участия
    """
    import logging
    logger = logging.getLogger(__name__)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if status_filter == 'upcoming':
            date_condition = "c.date >= date('now')"
        elif status_filter == 'finished':
            date_condition = "c.date < date('now')"
        else:
            date_condition = "1=1"

        logger.info(f"get_student_competitions_for_coach: student_id={student_id}, status_filter={status_filter}")

        # Получаем ВСЕ соревнования ученика, включая pending и rejected proposals
        async with db.execute(
            f"""
            SELECT c.*, cp.distance, cp.distance_name, cp.target_time, cp.finish_time,
                   cp.place_overall, cp.place_age_category, cp.age_category,
                   cp.result_comment, cp.result_photo, cp.heart_rate, cp.qualification, cp.status as participant_status,
                   cp.registered_at, cp.result_added_at, cp.proposal_status,
                   cp.proposed_by_coach, cp.proposed_by_coach_id
            FROM competitions c
            JOIN competition_participants cp ON c.id = cp.competition_id
            WHERE cp.user_id = ? AND {date_condition}
            ORDER BY c.date ASC
            """,
            (student_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            logger.info(f"Found {len(rows)} competitions for student {student_id}")
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


async def get_student_competitions_for_coach(
    student_id: int,
    status_filter: str = None
) -> List[Dict[str, Any]]:
    """
    Получить соревнования ученика для отображения тренеру
    В отличие от get_user_competitions, показывает ВСЕ соревнования,
    включая pending proposals

    Args:
        student_id: ID ученика
        status_filter: Фильтр по статусу ('upcoming', 'finished')

    Returns:
        Список соревнований с данными участия
    """
    import logging
    logger = logging.getLogger(__name__)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if status_filter == 'upcoming':
            date_condition = "c.date >= date('now')"
        elif status_filter == 'finished':
            date_condition = "c.date < date('now')"
        else:
            date_condition = "1=1"

        logger.info(f"get_student_competitions_for_coach: student_id={student_id}, status_filter={status_filter}")

        # Получаем ВСЕ соревнования ученика, включая pending и rejected proposals
        async with db.execute(
            f"""
            SELECT c.*, cp.distance, cp.distance_name, cp.target_time, cp.finish_time,
                   cp.place_overall, cp.place_age_category, cp.age_category,
                   cp.result_comment, cp.result_photo, cp.heart_rate, cp.qualification, cp.status as participant_status,
                   cp.registered_at, cp.result_added_at, cp.proposal_status,
                   cp.proposed_by_coach, cp.proposed_by_coach_id
            FROM competitions c
            JOIN competition_participants cp ON c.id = cp.competition_id
            WHERE cp.user_id = ? AND {date_condition}
            ORDER BY c.date ASC
            """,
            (student_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            logger.info(f"Found {len(rows)} competitions for student {student_id}")
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
    target_time: str = None,
    distance_name: str = None
) -> int:
    """
    Зарегистрировать пользователя на соревнование

    Args:
        user_id: ID пользователя
        competition_id: ID соревнования
        distance: Выбранная дистанция (в км)
        target_time: Целевое время (опционально)
        distance_name: Название дистанции (опционально, например "5 км", "Полумарафон")

    Returns:
        ID записи участия
    """
    import logging
    logger = logging.getLogger(__name__)

    async with aiosqlite.connect(DB_PATH) as db:
        # Если distance_name не указано, используем distance как строку
        if distance_name is None:
            distance_name = str(distance)

        # Проверяем существование записи с такими параметрами
        async with db.execute(
            """
            SELECT id FROM competition_participants
            WHERE user_id = ? AND competition_id = ? AND distance = ? AND distance_name = ?
            """,
            (user_id, competition_id, distance, distance_name)
        ) as cursor:
            existing = await cursor.fetchone()

        if existing:
            # Запись уже существует - обновляем только если нужно
            logger.info(f"Registration already exists: user={user_id}, comp={competition_id}, dist={distance}, updating if needed")
            if target_time:
                await db.execute(
                    """
                    UPDATE competition_participants
                    SET target_time = ?, status = 'registered',
                        proposal_status = NULL, reminders_enabled = 1
                    WHERE id = ?
                    """,
                    (target_time, existing[0])
                )
                await db.commit()
            return existing[0]
        else:
            # Создаем новую запись
            logger.info(f"Creating new registration: user={user_id}, comp={competition_id}, dist={distance}, dist_name={distance_name}")
            cursor = await db.execute(
                """
                INSERT INTO competition_participants
                (user_id, competition_id, distance, distance_name, target_time, status, reminders_enabled)
                VALUES (?, ?, ?, ?, ?, 'registered', 1)
                """,
                (user_id, competition_id, distance, distance_name, target_time)
            )
            await db.commit()
            logger.info(f"Registration created with id={cursor.lastrowid}")
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
            # Для reg.place/HeroLeague distance может быть 0 или NULL
            # Поэтому используем гибкий поиск
            if distance in (0, 0.0):
                # Для distance=0, ищем записи где distance=0, NULL или не указана
                cursor = await db.execute(
                    """
                    DELETE FROM competition_participants
                    WHERE user_id = ? AND competition_id = ?
                    AND (distance = 0 OR distance IS NULL)
                    """,
                    (user_id, competition_id)
                )
            else:
                # Для обычных дистанций используем точное совпадение
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


# Alias for clearer API
async def unregister_from_competition_with_distance(
    user_id: int,
    competition_id: int,
    distance: float
) -> bool:
    """
    Отменить регистрацию на соревнование с указанной дистанцией

    Args:
        user_id: ID пользователя
        competition_id: ID соревнования
        distance: Дистанция

    Returns:
        True если удаление прошло успешно
    """
    return await unregister_from_competition(user_id, competition_id, distance)


async def update_target_time(
    user_id: int,
    competition_id: int,
    distance: float,
    target_time: str
) -> bool:
    """
    Обновить целевое время для регистрации на соревнование

    Args:
        user_id: ID пользователя
        competition_id: ID соревнования
        distance: Дистанция
        target_time: Новое целевое время

    Returns:
        True если обновление прошло успешно
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Для reg.place/HeroLeague distance может быть 0 или NULL
        # Поэтому используем гибкий поиск
        if distance in (0, 0.0, None):
            # Для distance=0/None, ищем записи где distance=0, NULL или не указана
            cursor = await db.execute(
                """
                UPDATE competition_participants
                SET target_time = ?
                WHERE user_id = ? AND competition_id = ?
                AND (distance = 0 OR distance IS NULL)
                """,
                (target_time, user_id, competition_id)
            )
        else:
            # Для обычных дистанций используем точное совпадение
            cursor = await db.execute(
                """
                UPDATE competition_participants
                SET target_time = ?
                WHERE user_id = ? AND competition_id = ? AND distance = ?
                """,
                (target_time, user_id, competition_id, distance)
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
    import logging
    logger = logging.getLogger(__name__)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if status_filter == 'upcoming':
            date_condition = "c.date >= date('now')"
        elif status_filter == 'finished':
            date_condition = "c.date < date('now')"
        else:
            date_condition = "1=1"

        # Добавим логирование для диагностики
        logger.info(f"get_user_competitions: user_id={user_id}, status_filter={status_filter}, date_condition={date_condition}")

        # Сначала проверим, есть ли вообще записи в competition_participants для этого пользователя
        async with db.execute(
            "SELECT COUNT(*) FROM competition_participants WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            count_row = await cursor.fetchone()
            logger.info(f"Total competition_participants records for user {user_id}: {count_row[0]}")

        # Проверим записи без фильтра по дате
        async with db.execute(
            """
            SELECT c.id, c.name, c.date, cp.distance, cp.distance_name
            FROM competitions c
            JOIN competition_participants cp ON c.id = cp.competition_id
            WHERE cp.user_id = ?
            """,
            (user_id,)
        ) as cursor:
            all_rows = await cursor.fetchall()
            logger.info(f"All competitions for user (no date filter): {len(all_rows)}")
            for row in all_rows:
                logger.info(f"  - comp_id={row[0]}, name={row[1]}, date={row[2]}, distance={row[3]}, distance_name={row[4]}")

        # Проверим текущую дату в SQLite
        async with db.execute("SELECT date('now')") as cursor:
            now_row = await cursor.fetchone()
            logger.info(f"SQLite current date: {now_row[0]}")

        # НОВАЯ УПРОЩЕННАЯ ЛОГИКА: показываем все зарегистрированные соревнования
        # Исключаем только pending (ожидают решения) и rejected (отклонены)
        async with db.execute(
            f"""
            SELECT c.*, cp.distance, cp.distance_name, cp.target_time, cp.finish_time,
                   cp.place_overall, cp.place_age_category, cp.age_category,
                   cp.result_comment, cp.result_photo, cp.heart_rate, cp.qualification, cp.status as participant_status,
                   cp.registered_at, cp.result_added_at, cp.proposal_status
            FROM competitions c
            JOIN competition_participants cp ON c.id = cp.competition_id
            WHERE cp.user_id = ? AND {date_condition}
              AND (cp.proposal_status IS NULL
                   OR cp.proposal_status NOT IN ('pending', 'rejected'))
            ORDER BY c.date ASC
            """,
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            logger.info(f"Competitions after applying filter: {len(rows)}")
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


async def get_student_competitions_for_coach(
    student_id: int,
    status_filter: str = None
) -> List[Dict[str, Any]]:
    """
    Получить соревнования ученика для отображения тренеру
    В отличие от get_user_competitions, показывает ВСЕ соревнования,
    включая pending proposals

    Args:
        student_id: ID ученика
        status_filter: Фильтр по статусу ('upcoming', 'finished')

    Returns:
        Список соревнований с данными участия
    """
    import logging
    logger = logging.getLogger(__name__)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if status_filter == 'upcoming':
            date_condition = "c.date >= date('now')"
        elif status_filter == 'finished':
            date_condition = "c.date < date('now')"
        else:
            date_condition = "1=1"

        logger.info(f"get_student_competitions_for_coach: student_id={student_id}, status_filter={status_filter}")

        # Получаем ВСЕ соревнования ученика, включая pending и rejected proposals
        async with db.execute(
            f"""
            SELECT c.*, cp.distance, cp.distance_name, cp.target_time, cp.finish_time,
                   cp.place_overall, cp.place_age_category, cp.age_category,
                   cp.result_comment, cp.result_photo, cp.heart_rate, cp.qualification, cp.status as participant_status,
                   cp.registered_at, cp.result_added_at, cp.proposal_status,
                   cp.proposed_by_coach, cp.proposed_by_coach_id
            FROM competitions c
            JOIN competition_participants cp ON c.id = cp.competition_id
            WHERE cp.user_id = ? AND {date_condition}
            ORDER BY c.date ASC
            """,
            (student_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            logger.info(f"Found {len(rows)} competitions for student {student_id}")
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


async def get_user_competitions_by_period(
    user_id: int,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Получить завершенные соревнования пользователя за период

    Args:
        user_id: ID пользователя
        date_from: Начало периода (опционально)
        date_to: Конец периода (опционально, по умолчанию сейчас)

    Returns:
        Список соревнований с данными участия
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        conditions = ["cp.user_id = ?", "c.date < date('now')", "(cp.proposal_status IS NULL OR cp.proposal_status != 'pending')"]
        params = [user_id]

        if date_from:
            conditions.append("c.date >= ?")
            params.append(date_from.strftime('%Y-%m-%d'))

        if date_to:
            conditions.append("c.date <= ?")
            params.append(date_to.strftime('%Y-%m-%d'))

        where_clause = " AND ".join(conditions)

        async with db.execute(
            f"""
            SELECT c.*, cp.distance, cp.distance_name, cp.target_time, cp.finish_time,
                   cp.place_overall, cp.place_age_category, cp.age_category,
                   cp.result_comment, cp.result_photo, cp.heart_rate, cp.qualification, cp.status as participant_status,
                   cp.registered_at, cp.result_added_at
            FROM competitions c
            JOIN competition_participants cp ON c.id = cp.competition_id
            WHERE {where_clause}
            ORDER BY c.date ASC
            """,
            tuple(params)
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


async def get_student_competitions_for_coach(
    student_id: int,
    status_filter: str = None
) -> List[Dict[str, Any]]:
    """
    Получить соревнования ученика для отображения тренеру
    В отличие от get_user_competitions, показывает ВСЕ соревнования,
    включая pending proposals

    Args:
        student_id: ID ученика
        status_filter: Фильтр по статусу ('upcoming', 'finished')

    Returns:
        Список соревнований с данными участия
    """
    import logging
    logger = logging.getLogger(__name__)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if status_filter == 'upcoming':
            date_condition = "c.date >= date('now')"
        elif status_filter == 'finished':
            date_condition = "c.date < date('now')"
        else:
            date_condition = "1=1"

        logger.info(f"get_student_competitions_for_coach: student_id={student_id}, status_filter={status_filter}")

        # Получаем ВСЕ соревнования ученика, включая pending и rejected proposals
        async with db.execute(
            f"""
            SELECT c.*, cp.distance, cp.distance_name, cp.target_time, cp.finish_time,
                   cp.place_overall, cp.place_age_category, cp.age_category,
                   cp.result_comment, cp.result_photo, cp.heart_rate, cp.qualification, cp.status as participant_status,
                   cp.registered_at, cp.result_added_at, cp.proposal_status,
                   cp.proposed_by_coach, cp.proposed_by_coach_id
            FROM competitions c
            JOIN competition_participants cp ON c.id = cp.competition_id
            WHERE cp.user_id = ? AND {date_condition}
            ORDER BY c.date ASC
            """,
            (student_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            logger.info(f"Found {len(rows)} competitions for student {student_id}")
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

    ВАЖНО: Не считаются зарегистрированными:
    - Отклоненные предложения (proposal_status='rejected')
    - Ожидающие решения (proposal_status='pending')

    Args:
        user_id: ID пользователя
        competition_id: ID соревнования
        distance: Конкретная дистанция (опционально)

    Returns:
        True если зарегистрирован (исключая rejected и pending)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        if distance is not None:
            async with db.execute(
                """
                SELECT COUNT(*) FROM competition_participants
                WHERE user_id = ? AND competition_id = ? AND distance = ?
                  AND (proposal_status IS NULL OR proposal_status NOT IN ('pending', 'rejected'))
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
                  AND (proposal_status IS NULL OR proposal_status NOT IN ('pending', 'rejected'))
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
    heart_rate: int = None,
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
        heart_rate: Средний пульс
        result_comment: Комментарий
        result_photo: Путь к фото

    Returns:
        True если добавление прошло успешно
    """
    # Нормализуем время перед сохранением
    normalized_time = normalize_time(finish_time)

    async with aiosqlite.connect(DB_PATH) as db:
        # Получаем тип спорта соревнования и пол пользователя для расчета разряда
        cursor = await db.execute(
            """
            SELECT c.sport_type, us.gender
            FROM competitions c
            LEFT JOIN user_settings us ON us.user_id = ?
            WHERE c.id = ?
            """,
            (user_id, competition_id)
        )
        row = await cursor.fetchone()
        sport_type = row[0] if row else 'бег'
        gender = row[1] if row and row[1] else 'male'

        # Рассчитываем разряд
        qualification = None
        try:
            from utils.qualifications import get_qualification_async, time_to_seconds
            time_seconds = time_to_seconds(normalized_time)
            # Для плавания всегда используем бассейн 50м
            # Для велоспорта используем индивидуальную гонку
            kwargs = {}
            if sport_type and sport_type.lower().startswith('пла'):
                kwargs['pool_length'] = 50
            elif sport_type and (sport_type.lower().startswith('вело') or 'bike' in sport_type.lower()):
                kwargs['discipline'] = 'индивидуальная гонка'

            qualification = await get_qualification_async(sport_type, distance, time_seconds, gender, **kwargs)
        except Exception as e:
            # Если не удалось рассчитать разряд, продолжаем без него
            logger.error(f"Ошибка расчета разряда: {e}")

        cursor = await db.execute(
            """
            UPDATE competition_participants
            SET finish_time = ?,
                place_overall = ?,
                place_age_category = ?,
                age_category = ?,
                heart_rate = ?,
                result_comment = ?,
                result_photo = ?,
                qualification = ?,
                status = 'finished',
                result_added_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND competition_id = ? AND distance = ?
            """,
            (
                normalized_time, place_overall, place_age_category, age_category,
                heart_rate, result_comment, result_photo, qualification,
                user_id, competition_id, distance
            )
        )
        await db.commit()

        # Проверяем и обновляем личный рекорд
        if cursor.rowcount > 0:
            await update_personal_record(user_id, distance, normalized_time, competition_id, qualification)

            # Обновляем рейтинг пользователя после добавления результата
            try:
                from ratings.rating_updater import update_single_user_rating
                await update_single_user_rating(user_id)
            except Exception as e:
                logger.error(f"Error updating user rating after competition result: {e}")

        return cursor.rowcount > 0


async def update_competition_result(
    user_id: int,
    competition_id: int,
    finish_time: str
) -> bool:
    """
    Обновить результат соревнования (изменить только финишное время)

    Args:
        user_id: ID пользователя
        competition_id: ID соревнования
        finish_time: Новое финишное время

    Returns:
        True если обновление прошло успешно
    """
    # Нормализуем время перед сохранением
    normalized_time = normalize_time(finish_time)

    async with aiosqlite.connect(DB_PATH) as db:
        # Получаем дистанцию, тип спорта соревнования и пол пользователя
        cursor = await db.execute(
            """
            SELECT cp.distance, c.sport_type, us.gender
            FROM competition_participants cp
            JOIN competitions c ON c.id = cp.competition_id
            LEFT JOIN user_settings us ON us.user_id = ?
            WHERE cp.user_id = ? AND cp.competition_id = ?
            """,
            (user_id, user_id, competition_id)
        )
        row = await cursor.fetchone()
        if not row:
            return False

        distance = row[0]
        sport_type = row[1] if row[1] else 'бег'
        gender = row[2] if row[2] else 'male'

        # Рассчитываем разряд
        qualification = None
        try:
            from utils.qualifications import get_qualification_async, time_to_seconds
            time_seconds = time_to_seconds(normalized_time)
            # Для плавания всегда используем бассейн 50м
            # Для велоспорта используем индивидуальную гонку
            kwargs = {}
            if sport_type and sport_type.lower().startswith('пла'):
                kwargs['pool_length'] = 50
            elif sport_type and (sport_type.lower().startswith('вело') or 'bike' in sport_type.lower()):
                kwargs['discipline'] = 'индивидуальная гонка'

            qualification = await get_qualification_async(sport_type, distance, time_seconds, gender, **kwargs)
        except Exception as e:
            # Если не удалось рассчитать разряд, продолжаем без него
            logger.error(f"Ошибка расчета разряда: {e}")

        # Обновляем только время и разряд
        cursor = await db.execute(
            """
            UPDATE competition_participants
            SET finish_time = ?,
                qualification = ?
            WHERE user_id = ? AND competition_id = ?
            """,
            (normalized_time, qualification, user_id, competition_id)
        )
        await db.commit()

        # Проверяем и обновляем личный рекорд
        if cursor.rowcount > 0:
            await update_personal_record(user_id, distance, normalized_time, competition_id, qualification)

            # Обновляем рейтинг пользователя после обновления результата
            try:
                from ratings.rating_updater import update_single_user_rating
                await update_single_user_rating(user_id)
            except Exception as e:
                logger.error(f"Error updating user rating after competition result update: {e}")

        return cursor.rowcount > 0


async def delete_competition_result(user_id: int, competition_id: int) -> bool:
    """
    Удалить результат соревнования (очистить поля результата)

    Args:
        user_id: ID пользователя
        competition_id: ID соревнования

    Returns:
        True если удаление успешно
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            UPDATE competition_participants
            SET finish_time = NULL,
                place_overall = NULL,
                place_age_category = NULL,
                age_category = NULL,
                heart_rate = NULL,
                result_comment = NULL,
                result_photo = NULL,
                status = 'registered',
                result_added_at = NULL
            WHERE user_id = ? AND competition_id = ?
            """,
            (user_id, competition_id)
        )
        await db.commit()

        # Обновляем рейтинг пользователя после удаления результата
        if cursor.rowcount > 0:
            try:
                from ratings.rating_updater import update_single_user_rating
                await update_single_user_rating(user_id)
            except Exception as e:
                logger.error(f"Error updating user rating after competition result deletion: {e}")

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


async def get_user_competition_registration(
    user_id: int,
    competition_id: int,
    distance: float = None,
    distance_name: str = None
) -> Optional[Dict[str, Any]]:
    """
    Получить регистрацию пользователя на соревнование

    Args:
        user_id: ID пользователя
        competition_id: ID соревнования
        distance: Дистанция (опционально, для точного поиска при множественных регистрациях)
        distance_name: Название дистанции (опционально, для точного поиска при множественных регистрациях)

    Returns:
        Словарь с данными регистрации или None
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Если указаны distance или distance_name, используем их для точного поиска
        if distance is not None or distance_name:
            # Формируем условия поиска
            conditions = ["user_id = ?", "competition_id = ?"]
            params = [user_id, competition_id]

            # Для distance=0/None используем гибкий поиск (как в update_target_time)
            if distance is not None:
                if distance in (0, 0.0):
                    conditions.append("(distance = 0 OR distance IS NULL)")
                else:
                    conditions.append("distance = ?")
                    params.append(distance)

            if distance_name:
                conditions.append("distance_name = ?")
                params.append(distance_name)

            query = f"""
                SELECT * FROM competition_participants
                WHERE {' AND '.join(conditions)}
            """

            async with db.execute(query, tuple(params)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
        else:
            # Обратная совместимость: если параметры не указаны, возвращаем первую запись
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
    competition_id: int = None,
    qualification: str = None
) -> bool:
    """
    Обновить личный рекорд пользователя если новое время лучше

    Args:
        user_id: ID пользователя
        distance: Дистанция
        time: Время (HH:MM:SS)
        competition_id: ID соревнования
        qualification: Разряд (МСМК, МС, КМС и т.д.)

    Returns:
        True если рекорд был обновлён
    """
    from utils.time_formatter import parse_time_to_seconds

    async with aiosqlite.connect(DB_PATH) as db:
        # Получаем текущий рекорд
        async with db.execute(
            "SELECT best_time FROM personal_records WHERE user_id = ? AND distance = ?",
            (user_id, distance)
        ) as cursor:
            row = await cursor.fetchone()

        # Преобразуем новое время в секунды для корректного сравнения
        new_time_seconds = parse_time_to_seconds(time)
        if new_time_seconds is None:
            return False

        # Сравниваем времена
        if row:
            current_best = row[0]
            # Преобразуем текущий лучший результат в секунды
            current_best_seconds = parse_time_to_seconds(current_best)
            if current_best_seconds is None:
                # Если текущий рекорд поврежден, заменяем его
                current_best_seconds = float('inf')

            # Сравниваем по секундам - меньше секунд = лучше время
            if new_time_seconds < current_best_seconds:
                # Обновляем рекорд
                await db.execute(
                    """
                    UPDATE personal_records
                    SET best_time = ?, competition_id = ?, qualification = ?, date = date('now'), updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND distance = ?
                    """,
                    (time, competition_id, qualification, user_id, distance)
                )
                await db.commit()
                return True
        else:
            # Создаём новый рекорд
            await db.execute(
                """
                INSERT INTO personal_records (user_id, distance, best_time, competition_id, qualification, date)
                VALUES (?, ?, ?, ?, ?, date('now'))
                """,
                (user_id, distance, time, competition_id, qualification)
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
        Словарь {дистанция: {best_time, date, competition_id, qualification}}
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
                    'competition_name': record['competition_name'],
                    'qualification': record.get('qualification')
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


async def get_user_competitions_with_details(
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    """
    Получить соревнования пользователя с полной детальной информацией для экспорта

    Args:
        user_id: ID пользователя
        start_date: Начальная дата (опционально)
        end_date: Конечная дата (опционально)

    Returns:
        Список соревнований с данными участия
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        conditions = ["cp.user_id = ?", "(cp.proposal_status IS NULL OR cp.proposal_status != 'pending')"]
        params = [user_id]

        if start_date:
            conditions.append("c.date >= ?")
            params.append(start_date.strftime('%Y-%m-%d'))

        if end_date:
            conditions.append("c.date <= ?")
            params.append(end_date.strftime('%Y-%m-%d'))

        where_clause = " AND ".join(conditions)

        async with db.execute(
            f"""
            SELECT
                c.id, c.name, c.date, c.city, c.country, c.location,
                c.distances, c.type, c.sport_type, c.description, c.official_url,
                c.organizer, c.registration_status, c.status,
                cp.distance, cp.distance_name, cp.target_time, cp.finish_time,
                cp.place_overall, cp.place_age_category, cp.age_category,
                cp.qualification, cp.result_comment, cp.result_photo, cp.status as participant_status
            FROM competitions c
            JOIN competition_participants cp ON c.id = cp.competition_id
            WHERE {where_clause}
            ORDER BY c.date ASC
            """,
            tuple(params)
        ) as cursor:
            rows = await cursor.fetchall()
            competitions = []
            for row in rows:
                comp = dict(row)
                # Используем participant_status как основной status
                comp['status'] = comp.get('participant_status', 'registered')
                if comp.get('distances'):
                    try:
                        comp['distances'] = json.loads(comp['distances'])
                    except:
                        pass
                competitions.append(comp)
            return competitions


async def get_student_competitions_for_coach(
    student_id: int,
    status_filter: str = None
) -> List[Dict[str, Any]]:
    """
    Получить соревнования ученика для отображения тренеру
    В отличие от get_user_competitions, показывает ВСЕ соревнования,
    включая pending proposals

    Args:
        student_id: ID ученика
        status_filter: Фильтр по статусу ('upcoming', 'finished')

    Returns:
        Список соревнований с данными участия
    """
    import logging
    logger = logging.getLogger(__name__)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if status_filter == 'upcoming':
            date_condition = "c.date >= date('now')"
        elif status_filter == 'finished':
            date_condition = "c.date < date('now')"
        else:
            date_condition = "1=1"

        logger.info(f"get_student_competitions_for_coach: student_id={student_id}, status_filter={status_filter}")

        # Получаем ВСЕ соревнования ученика, включая pending и rejected proposals
        async with db.execute(
            f"""
            SELECT c.*, cp.distance, cp.distance_name, cp.target_time, cp.finish_time,
                   cp.place_overall, cp.place_age_category, cp.age_category,
                   cp.result_comment, cp.result_photo, cp.heart_rate, cp.qualification, cp.status as participant_status,
                   cp.registered_at, cp.result_added_at, cp.proposal_status,
                   cp.proposed_by_coach, cp.proposed_by_coach_id
            FROM competitions c
            JOIN competition_participants cp ON c.id = cp.competition_id
            WHERE cp.user_id = ? AND {date_condition}
            ORDER BY c.date ASC
            """,
            (student_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            logger.info(f"Found {len(rows)} competitions for student {student_id}")
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
