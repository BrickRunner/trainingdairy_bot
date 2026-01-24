"""
Объединенный модуль для получения соревнований из разных сервисов
"""

from typing import List, Dict, Optional
import logging

from competitions.parser import fetch_competitions as fetch_russiarunning
from competitions.timerman_parser import fetch_competitions as fetch_timerman
from competitions.heroleague_parser import fetch_competitions as fetch_heroleague
from competitions.regplace_parser import fetch_competitions as fetch_regplace
from competitions.runc_parser import fetch_competitions as fetch_runc

logger = logging.getLogger(__name__)


async def fetch_all_competitions(
    city: Optional[str] = None,
    sport: Optional[str] = None,
    limit: int = 50,
    period_months: Optional[int] = None,
    service: Optional[str] = None  # "RussiaRunning", "Timerman", "HeroLeague", "reg.place", "RunC", "all"
) -> List[Dict]:
    """
    Получить список соревнований из всех или выбранного сервиса

    Args:
        city: Название города
        sport: Код вида спорта ("run", "bike", "swim", "all")
        limit: Максимальное количество результатов
        period_months: Период в месяцах для фильтрации
        service: Сервис для регистрации ("RussiaRunning", "Timerman", "HeroLeague", "reg.place", "RunC", "all" или None)

    Returns:
        Объединенный список соревнований из всех источников
    """
    all_competitions = []

    # Определяем какие сервисы использовать
    use_russiarunning = service is None or service == "all" or service == "RussiaRunning"
    use_timerman = service is None or service == "all" or service == "Timerman"
    use_heroleague = service is None or service == "all" or service == "HeroLeague"
    use_regplace = service is None or service == "all" or service == "reg.place"
    use_runc = service is None or service == "all" or service == "RunC"

    # Получаем соревнования из RussiaRunning
    if use_russiarunning:
        try:
            logger.info("Fetching competitions from RussiaRunning...")
            russiarunning_comps = await fetch_russiarunning(
                city=city,
                sport=sport,
                limit=limit if service == "RussiaRunning" else 1000,  # Если выбран конкретный сервис - ограничиваем, иначе берем все
                period_months=period_months
            )
            logger.info(f"Received {len(russiarunning_comps)} competitions from RussiaRunning")
            all_competitions.extend(russiarunning_comps)
        except Exception as e:
            logger.error(f"Error fetching from RussiaRunning: {e}")

    # Получаем соревнования из Timerman
    if use_timerman:
        try:
            logger.info("Fetching competitions from Timerman...")
            timerman_comps = await fetch_timerman(
                city=city,
                sport=sport,
                limit=limit if service == "Timerman" else 1000,
                period_months=period_months
            )
            logger.info(f"Received {len(timerman_comps)} competitions from Timerman")
            all_competitions.extend(timerman_comps)
        except Exception as e:
            logger.error(f"Error fetching from Timerman: {e}")

    # Получаем соревнования из HeroLeague
    if use_heroleague:
        try:
            logger.info("Fetching competitions from HeroLeague...")
            heroleague_comps = await fetch_heroleague(
                city=city,
                sport=sport,
                limit=limit if service == "HeroLeague" else 1000,
                period_months=period_months
            )
            logger.info(f"Received {len(heroleague_comps)} competitions from HeroLeague")
            all_competitions.extend(heroleague_comps)
        except Exception as e:
            logger.error(f"Error fetching from HeroLeague: {e}")

    # Получаем соревнования из reg.place
    if use_regplace:
        try:
            logger.info("Fetching competitions from reg.place...")
            regplace_comps = await fetch_regplace(
                city=city,
                sport=sport,
                limit=limit if service == "reg.place" else 1000,
                period_months=period_months
            )
            logger.info(f"Received {len(regplace_comps)} competitions from reg.place")
            all_competitions.extend(regplace_comps)
        except Exception as e:
            logger.error(f"Error fetching from reg.place: {e}")

    # Получаем соревнования из RunC
    if use_runc:
        try:
            logger.info("Fetching competitions from RunC...")
            runc_comps = await fetch_runc(
                city=city,
                sport=sport,
                limit=limit if service == "RunC" else 1000,
                period_months=period_months
            )
            logger.info(f"Received {len(runc_comps)} competitions from RunC")
            all_competitions.extend(runc_comps)
        except Exception as e:
            logger.error(f"Error fetching from RunC: {e}")

    # Сортируем по дате (самые близкие сначала)
    all_competitions.sort(key=lambda x: x.get('begin_date', '9999-12-31'))

    # Ограничиваем количество если нужно
    if len(all_competitions) > limit:
        all_competitions = all_competitions[:limit]

    logger.info(f"Total competitions after merging: {len(all_competitions)}")

    return all_competitions


# Константы для сервисов
SERVICE_CODES = {
    "RussiaRunning": "RussiaRunning",
    "Timerman": "Timerman",
    "Лига Героев": "HeroLeague",
    "Reg.place": "reg.place",
    "RunC": "RunC",
    "Все сервисы": "all",
}

# Обратный словарь
SERVICE_NAMES = {v: k for k, v in SERVICE_CODES.items()}
