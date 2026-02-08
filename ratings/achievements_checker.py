"""
Модуль для проверки и присвоения достижений пользователям
"""

import aiosqlite
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Set
from database.queries import DB_PATH
from ratings.achievements_data import ACHIEVEMENTS

logger = logging.getLogger(__name__)


async def check_and_award_achievements(user_id: int, bot=None) -> List[str]:
    """
    Проверить и присвоить новые достижения пользователю

    Args:
        user_id: ID пользователя
        bot: Экземпляр бота для отправки уведомлений (опционально)

    Returns:
        Список ID новых достижений
    """
    # Получаем уже полученные достижения, чтобы не выдавать дубли
    current_achievements = await get_user_achievements(user_id)
    current_ids = {ach['name'] for ach in current_achievements}

    # Собираем актуальную статистику пользователя
    stats = await get_user_stats(user_id)

    new_achievements = []

    # Проверяем все возможные достижения
    for ach_id, ach_data in ACHIEVEMENTS.items():
        if ach_id in current_ids:
            continue  # Уже получено

        # Проверяем условие получения достижения
        if await check_achievement_condition(user_id, ach_id, stats):
            await award_achievement(user_id, ach_id)
            new_achievements.append(ach_id)
            logger.info(f"User {user_id} earned achievement: {ach_id}")

            # Отправляем уведомление если передан бот
            if bot:
                await send_achievement_notification(bot, user_id, ach_id)

    return new_achievements


async def check_achievement_condition(user_id: int, achievement_id: str, stats: dict) -> bool:
    """
    Проверить условие получения достижения

    Args:
        user_id: ID пользователя
        achievement_id: ID достижения
        stats: Статистика пользователя

    Returns:
        True если условие выполнено
    """
    if achievement_id == 'first_competition':
        return stats['total_competitions'] >= 1

    elif achievement_id == 'ten_k_first':
        return stats['has_10k']

    elif achievement_id == 'half_marathon_first':
        return stats['has_half_marathon']

    elif achievement_id == 'marathon_first':
        return stats['has_marathon']

    elif achievement_id == 'ultra_marathon':
        return stats['has_ultra']

    elif achievement_id == 'triathlon_first':
        return stats['triathlon_count'] >= 1

    elif achievement_id == 'swimmer':
        return stats['swimming_competitions'] >= 5

    elif achievement_id == 'cyclist':
        return stats['cycling_competitions'] >= 5

    elif achievement_id == 'mid_distance':
        return stats['mid_distance_races'] >= 10  

    elif achievement_id == 'versatile':
        return stats['different_sports'] >= 3

    elif achievement_id == 'distance_collector':
        return stats['has_all_distances']  

    elif achievement_id == 'enthusiast':
        return stats['total_competitions'] >= 5

    elif achievement_id == 'active_runner':
        return stats['total_competitions'] >= 10

    elif achievement_id == 'experienced_runner':
        return stats['total_competitions'] >= 25

    elif achievement_id == 'veteran':
        return stats['total_competitions'] >= 50

    elif achievement_id == 'legend':
        return stats['total_competitions'] >= 100

    elif achievement_id == 'annual_marathon':
        return stats['competitions_this_year'] >= 12

    elif achievement_id == 'streak_3_months':
        return stats['competition_streak_months'] >= 3

    elif achievement_id == 'streak_6_months':
        return stats['competition_streak_months'] >= 6

    elif achievement_id == 'streak_12_months':
        return stats['competition_streak_months'] >= 12

    elif achievement_id == 'first_podium':
        return stats['podium_count'] >= 1

    elif achievement_id == 'podium_5_times':
        return stats['podium_count'] >= 5

    elif achievement_id == 'pr_improvement':
        return stats['has_big_pr_improvement']  

    elif achievement_id == 'progress_streak':
        return stats['has_progress_streak']  

    elif achievement_id == 'record_holder':
        return stats['pr_distances_count'] >= 5

    elif achievement_id == 'goal_achiever':
        return stats['target_time_achieved'] >= 5

    elif achievement_id == 'first_result':
        return stats['total_results'] >= 1

    elif achievement_id == 'historian_10':
        return stats['total_results'] >= 10

    elif achievement_id == 'archivist':
        return stats['total_results'] >= 50

    elif achievement_id == 'first_training':
        return stats['total_trainings'] >= 1

    elif achievement_id == 'training_month':
        return stats['trainings_this_month'] >= 20

    elif achievement_id == 'regularity':
        return stats['training_streak_days'] >= 7

    elif achievement_id == 'mileage_100':
        return stats['monthly_km'] >= 100

    elif achievement_id == 'mileage_200':
        return stats['monthly_km'] >= 200

    elif achievement_id == 'first_registration':
        return stats['bot_registrations'] >= 1

    elif achievement_id == 'active_planner':
        return stats['bot_registrations'] >= 10

    elif achievement_id == 'calendar_full':
        return stats['upcoming_registrations'] >= 5

    elif achievement_id == 'detailer':
        return stats['detailed_results'] >= 10

    elif achievement_id == 'traveler':
        return stats['different_cities'] >= 5

    elif achievement_id == 'russia_geography':
        return stats['different_cities'] >= 10

    elif achievement_id == 'explorer':
        return stats['different_cities'] >= 20

    elif achievement_id == 'regions_5':
        return stats['different_regions'] >= 5

    elif achievement_id == 'regions_10':
        return stats['different_regions'] >= 10

    elif achievement_id == 'moscow_spb':
        return stats['moscow_spb_count'] >= 10

    elif achievement_id == 'bot_1_year':
        return stats['bot_usage_days'] >= 365

    elif achievement_id == 'bot_2_years':
        return stats['bot_usage_days'] >= 730

    elif achievement_id == 'russia_running_fan':
        return stats['russia_running_count'] >= 10

    elif achievement_id == 'hero_league':
        return stats['hero_league_count'] >= 5

    elif achievement_id == 'parkrun_regular':
        return stats['parkrun_count'] >= 10

    elif achievement_id == 'trail_runner':
        return stats['trail_count'] >= 5

    elif achievement_id == 'night_runner':
        return stats['night_races'] >= 3

    elif achievement_id == 'relay_team':
        return stats['relay_count'] >= 3

    elif achievement_id == 'virtual_runner':
        return stats['virtual_races'] >= 5

    elif achievement_id == 'charity_runner':
        return stats['charity_races'] >= 3

    elif achievement_id == 'early_bird':
        return stats['early_trainings'] >= 10  

    return False


async def get_user_stats(user_id: int) -> dict:
    """
    Получить статистику пользователя для проверки достижений

    Returns:
        Словарь со статистикой
    """
    stats = {
        'total_competitions': 0,
        'has_10k': False,
        'has_half_marathon': False,
        'has_marathon': False,
        'has_ultra': False,
        'triathlon_count': 0,
        'swimming_competitions': 0,
        'cycling_competitions': 0,
        'mid_distance_races': 0,
        'different_sports': 0,
        'has_all_distances': False,
        'competitions_this_year': 0,
        'competition_streak_months': 0,

        'podium_count': 0,
        'has_big_pr_improvement': False,
        'has_progress_streak': False,
        'pr_distances_count': 0,
        'target_time_achieved': 0,

        'total_results': 0,
        'total_trainings': 0,
        'trainings_this_month': 0,
        'training_streak_days': 0,
        'monthly_km': 0,
        'bot_registrations': 0,
        'upcoming_registrations': 0,
        'detailed_results': 0,

        'different_cities': 0,
        'different_regions': 0,
        'moscow_spb_count': 0,

        'bot_usage_days': 0,
        'russia_running_count': 0,
        'hero_league_count': 0,
        'parkrun_count': 0,
        'trail_count': 0,
        'night_races': 0,
        'relay_count': 0,
        'virtual_races': 0,
        'charity_races': 0,
        'early_trainings': 0,
    }

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            "SELECT COUNT(*) as cnt FROM competition_participants WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            stats['total_competitions'] = row['cnt'] if row else 0

        async with db.execute(
            """
            SELECT DISTINCT cp.distance, c.sport_type, c.organizer, c.type, cp.place_overall, c.city
            FROM competition_participants cp
            JOIN competitions c ON cp.competition_id = c.id
            WHERE cp.user_id = ?
            """,
            (user_id,)
        ) as cursor:
            distances = set()
            sports = set()
            cities = set()
            swimming_count = 0
            cycling_count = 0
            triathlon_count = 0
            mid_distance = 0
            russia_running = 0
            hero_league = 0
            parkrun = 0
            trail = 0
            podium = 0
            moscow_spb = 0

            async for row in cursor:
                distance = row['distance']
                sport = row['sport_type']
                organizer = row['organizer'] or ''
                comp_type = row['type'] or ''
                place = row['place_overall']
                city = row['city'] or ''

                if distance:
                    distances.add(distance)

                    if distance == 10.0:
                        stats['has_10k'] = True
                    elif distance == 21.1:
                        stats['has_half_marathon'] = True
                    elif distance == 42.195:
                        stats['has_marathon'] = True
                    elif distance > 42.195:
                        stats['has_ultra'] = True

                    if 5.0 <= distance <= 10.0:
                        mid_distance += 1

                if sport:
                    sports.add(sport)
                    if sport == 'плавание':
                        swimming_count += 1
                    elif sport == 'велоспорт':
                        cycling_count += 1
                    elif sport == 'триатлон':
                        triathlon_count += 1

                if 'russia running' in organizer.lower():
                    russia_running += 1
                elif 'hero' in organizer.lower() or 'лига героев' in organizer.lower():
                    hero_league += 1
                elif 'parkrun' in organizer.lower() or 'паркран' in organizer.lower():
                    parkrun += 1

                if 'трейл' in comp_type.lower():
                    trail += 1

                if place and place <= 3:
                    podium += 1

                if city:
                    cities.add(city)
                    if city.lower() in ['москва', 'санкт-петербург']:
                        moscow_spb += 1

            stats['mid_distance_races'] = mid_distance
            stats['different_sports'] = len(sports)
            stats['swimming_competitions'] = swimming_count
            stats['cycling_competitions'] = cycling_count
            stats['triathlon_count'] = triathlon_count
            stats['russia_running_count'] = russia_running
            stats['hero_league_count'] = hero_league
            stats['parkrun_count'] = parkrun
            stats['trail_count'] = trail
            stats['podium_count'] = podium
            stats['different_cities'] = len(cities)
            stats['moscow_spb_count'] = moscow_spb

            stats['has_all_distances'] = all([
                5.0 in distances,
                10.0 in distances,
                21.1 in distances,
                42.195 in distances
            ])

        current_year = datetime.now().year
        async with db.execute(
            """
            SELECT COUNT(*) as cnt
            FROM competition_participants cp
            JOIN competitions c ON cp.competition_id = c.id
            WHERE cp.user_id = ? AND strftime('%Y', c.date) = ?
            """,
            (user_id, str(current_year))
        ) as cursor:
            row = await cursor.fetchone()
            stats['competitions_this_year'] = row['cnt'] if row else 0

        stats['competition_streak_months'] = await calculate_competition_streak(user_id, db)

        async with db.execute(
            "SELECT COUNT(*) as cnt FROM competition_participants WHERE user_id = ? AND finish_time IS NOT NULL",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            stats['total_results'] = row['cnt'] if row else 0

        async with db.execute(
            """
            SELECT COUNT(*) as cnt
            FROM competition_participants
            WHERE user_id = ? AND finish_time IS NOT NULL AND place_overall IS NOT NULL AND age_category IS NOT NULL
            """,
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            stats['detailed_results'] = row['cnt'] if row else 0

        async with db.execute(
            "SELECT COUNT(DISTINCT distance) as cnt FROM personal_records WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            stats['pr_distances_count'] = row['cnt'] if row else 0

        async with db.execute(
            """
            SELECT COUNT(*) as cnt
            FROM competition_participants
            WHERE user_id = ? AND target_time IS NOT NULL AND finish_time IS NOT NULL
              AND finish_time <= target_time
            """,
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            stats['target_time_achieved'] = row['cnt'] if row else 0

        async with db.execute(
            "SELECT COUNT(*) as cnt FROM trainings WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            stats['total_trainings'] = row['cnt'] if row else 0

        month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        async with db.execute(
            "SELECT COUNT(*) as cnt FROM trainings WHERE user_id = ? AND date >= ?",
            (user_id, month_ago)
        ) as cursor:
            row = await cursor.fetchone()
            stats['trainings_this_month'] = row['cnt'] if row else 0

        async with db.execute(
            "SELECT SUM(distance) as total FROM trainings WHERE user_id = ? AND date >= ?",
            (user_id, month_ago)
        ) as cursor:
            row = await cursor.fetchone()
            stats['monthly_km'] = row['total'] if row and row['total'] else 0

        stats['training_streak_days'] = await calculate_training_streak(user_id, db)

        async with db.execute(
            """
            SELECT COUNT(*) as cnt
            FROM trainings
            WHERE user_id = ? AND time < '07:00'
            """,
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            stats['early_trainings'] = row['cnt'] if row else 0

        async with db.execute(
            "SELECT COUNT(*) as cnt FROM competition_participants WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            stats['bot_registrations'] = row['cnt'] if row else 0

        stats['night_races'] = 0  
        stats['relay_count'] = 0  
        stats['virtual_races'] = 0  
        stats['charity_races'] = 0  

        stats['different_regions'] = min(stats['different_cities'] // 2, stats['different_cities'])

        today = datetime.now().strftime('%Y-%m-%d')
        async with db.execute(
            """
            SELECT COUNT(*) as cnt
            FROM competition_participants cp
            JOIN competitions c ON cp.competition_id = c.id
            WHERE cp.user_id = ? AND c.date >= ?
            """,
            (user_id, today)
        ) as cursor:
            row = await cursor.fetchone()
            stats['upcoming_registrations'] = row['cnt'] if row else 0

        async with db.execute(
            "SELECT created_at FROM users WHERE id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row and row['created_at']:
                created = datetime.fromisoformat(row['created_at'])
                stats['bot_usage_days'] = (datetime.now() - created).days

    stats['has_big_pr_improvement'] = await check_big_pr_improvement(user_id)

    stats['has_progress_streak'] = await check_progress_streak(user_id)

    return stats


async def calculate_competition_streak(user_id: int, db) -> int:
    """Вычислить количество месяцев подряд с соревнованиями"""
    # Получаем все месяцы, в которых были соревнования
    async with db.execute(
        """
        SELECT DISTINCT strftime('%Y-%m', c.date) as month
        FROM competition_participants cp
        JOIN competitions c ON cp.competition_id = c.id
        WHERE cp.user_id = ?
        ORDER BY month DESC
        """,
        (user_id,)
    ) as cursor:
        months = [row['month'] async for row in cursor]

    if not months:
        return 0

    # Считаем серию последовательных месяцев с конца (самые свежие)
    streak = 1
    for i in range(len(months) - 1):
        current = datetime.strptime(months[i], '%Y-%m')
        next_month = datetime.strptime(months[i + 1], '%Y-%m')

        # Проверяем что месяцы идут подряд (учитывая переход года)
        if (current.year == next_month.year and current.month == next_month.month + 1) or \
           (current.year == next_month.year + 1 and current.month == 1 and next_month.month == 12):
            streak += 1
        else:
            break  # Серия прервана

    return streak


async def calculate_training_streak(user_id: int, db) -> int:
    """Вычислить количество дней подряд с тренировками"""
    async with db.execute(
        """
        SELECT DISTINCT date
        FROM trainings
        WHERE user_id = ?
        ORDER BY date DESC
        LIMIT 30
        """,
        (user_id,)
    ) as cursor:
        dates = [datetime.strptime(row['date'], '%Y-%m-%d').date() async for row in cursor]

    if not dates:
        return 0

    streak = 1
    for i in range(len(dates) - 1):
        if (dates[i] - dates[i + 1]).days == 1:
            streak += 1
        else:
            break

    return streak


async def check_big_pr_improvement(user_id: int) -> bool:
    """Проверить наличие улучшения ЛР на 5+ минут"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Получаем все результаты по дистанциям в хронологическом порядке
        async with db.execute(
            """
            SELECT distance, finish_time
            FROM competition_participants cp
            JOIN competitions c ON cp.competition_id = c.id
            WHERE cp.user_id = ? AND cp.finish_time IS NOT NULL
            ORDER BY distance, c.date
            """,
            (user_id,)
        ) as cursor:
            # Группируем результаты по дистанциям
            times_by_distance = {}
            async for row in cursor:
                distance = row['distance']
                time_str = row['finish_time']

                if distance not in times_by_distance:
                    times_by_distance[distance] = []

                times_by_distance[distance].append(time_str)

            # Ищем улучшение на 5+ минут (300 секунд)
            for distance, times in times_by_distance.items():
                for i in range(len(times) - 1):
                    old_time = parse_time(times[i])
                    new_time = parse_time(times[i + 1])

                    if old_time and new_time:
                        improvement = old_time - new_time
                        if improvement >= 300:  # 5 минут = 300 секунд
                            return True

    return False


async def check_progress_streak(user_id: int) -> bool:
    """Проверить наличие серии улучшений ЛР (3 раза подряд)"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Получаем результаты по дистанциям
        async with db.execute(
            """
            SELECT distance, finish_time
            FROM competition_participants cp
            JOIN competitions c ON cp.competition_id = c.id
            WHERE cp.user_id = ? AND cp.finish_time IS NOT NULL
            ORDER BY distance, c.date
            """,
            (user_id,)
        ) as cursor:
            times_by_distance = {}
            async for row in cursor:
                distance = row['distance']
                time_str = row['finish_time']

                if distance not in times_by_distance:
                    times_by_distance[distance] = []

                times_by_distance[distance].append(time_str)

            # Ищем серию из 3 последовательных улучшений
            for distance, times in times_by_distance.items():
                if len(times) < 3:
                    continue  # Нужно минимум 3 результата

                # Проверяем каждую тройку подряд идущих результатов
                for i in range(len(times) - 2):
                    time1 = parse_time(times[i])
                    time2 = parse_time(times[i + 1])
                    time3 = parse_time(times[i + 2])

                    # Каждый следующий результат должен быть лучше предыдущего
                    if time1 and time2 and time3:
                        if time2 < time1 and time3 < time2:
                            return True  # Нашли серию улучшений

    return False


def parse_time(time_str: str) -> int:
    """Преобразовать строку времени в секунды"""
    try:
        parts = time_str.split(':')
        if len(parts) == 3:
            h, m, s = map(int, parts)
            return h * 3600 + m * 60 + s
        elif len(parts) == 2:
            m, s = map(int, parts)
            return m * 60 + s
        else:
            return int(parts[0])
    except:
        return 0


async def get_user_achievements(user_id: int) -> List[dict]:
    """Получить все достижения пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM achievements WHERE user_id = ? ORDER BY date_awarded DESC",
            (user_id,)
        ) as cursor:
            return [dict(row) async for row in cursor]


async def award_achievement(user_id: int, achievement_id: str):
    """Присвоить достижение пользователю"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO achievements (user_id, name, date_awarded) VALUES (?, ?, CURRENT_DATE)",
            (user_id, achievement_id)
        )
        await db.commit()


async def send_achievement_notification(bot, user_id: int, achievement_id: str):
    """Отправить уведомление о новом достижении"""
    from ratings.achievements_data import get_achievement_by_id

    ach = get_achievement_by_id(achievement_id)
    if not ach:
        return

    message = (
        f"🎉 Поздравляем! Вы получили новое достижение!\n\n"
        f"{ach['emoji']} **{ach['name']}**\n"
        f"{ach['description']}\n\n"
        f"⭐ +{ach['points']} баллов к рейтингу!"
    )

    try:
        await bot.send_message(user_id, message, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Failed to send achievement notification to {user_id}: {e}")


async def get_achievement_leaderboard(limit: int = 10) -> List[dict]:
    """
    Получить список лидеров по достижениям

    Args:
        limit: Количество пользователей в списке

    Returns:
        Список пользователей с количеством достижений
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT
                u.id,
                u.username,
                COUNT(a.id) as achievement_count,
                SUM(CASE
                    WHEN a.name IN (SELECT id FROM json_each(?))
                    THEN json_extract(?, '$.' || a.name || '.points')
                    ELSE 0
                END) as total_points
            FROM users u
            LEFT JOIN achievements a ON u.id = a.user_id
            GROUP BY u.id
            HAVING achievement_count > 0
            ORDER BY achievement_count DESC, total_points DESC
            LIMIT ?
            """,
            (str(list(ACHIEVEMENTS.keys())), str({k: v for k, v in ACHIEVEMENTS.items()}), limit)
        ) as cursor:
            pass

        async with db.execute(
            """
            SELECT
                u.id,
                u.username,
                COUNT(a.id) as achievement_count
            FROM users u
            LEFT JOIN achievements a ON u.id = a.user_id
            GROUP BY u.id
            HAVING achievement_count > 0
            ORDER BY achievement_count DESC
            LIMIT ?
            """,
            (limit,)
        ) as cursor:
            leaders = []
            async for row in cursor:
                user_achievements = await get_user_achievements(row['id'])
                total_points = sum(
                    ACHIEVEMENTS.get(ach['name'], {}).get('points', 0)
                    for ach in user_achievements
                )

                leaders.append({
                    'id': row['id'],
                    'username': row['username'],
                    'achievement_count': row['achievement_count'],
                    'total_points': total_points
                })

            leaders.sort(key=lambda x: (x['achievement_count'], x['total_points']), reverse=True)

            return leaders
