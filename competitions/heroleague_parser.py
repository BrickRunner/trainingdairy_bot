"""
Парсер для получения соревнований с сайта Лига Героев (heroleague.ru)

API Endpoint: GET https://heroleague.ru/api/event/list
"""

import aiohttp
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

BASE_URL = "https://heroleague.ru"
API_ENDPOINT = f"{BASE_URL}/api/event/list"


def normalize_sport_code(event_type_id: str) -> str:
    """
    Нормализует sport_code от HeroLeague к стандартным кодам

    Args:
        event_type_id: ID типа события (например, "gonka", "zabeg", "skirun")

    Returns:
        str: Стандартный код спорта ("run", "ski", "bike", "swim", "triathlon", "other")
    """
    event_type_lower = event_type_id.lower()

    if any(keyword in event_type_lower for keyword in ["skirun", "snowrun", "ski", "лыж"]):
        return "ski"
    elif any(keyword in event_type_lower for keyword in ["gonka", "gonka_zima", "camp"]):
        return "other"
    elif any(keyword in event_type_lower for keyword in ["zabeg", "race", "run", "marathon", "doroga", "arctic", "trail"]):
        return "run"
    elif any(keyword in event_type_lower for keyword in ["bike", "велос", "lastrada"]):
        return "bike"
    elif any(keyword in event_type_lower for keyword in ["swim", "плав"]):
        return "swim"
    elif any(keyword in event_type_lower for keyword in ["triathlon", "триатлон"]):
        return "triathlon"
    else:
        return "other"


def matches_sport_type(event_type_id: str, sport: Optional[str]) -> bool:
    """
    Проверяет, соответствует ли тип события выбранному спорту

    Args:
        event_type_id: ID типа события (например, "gonka", "zabeg", "skirun")
        sport: Тип спорта для фильтрации ("run", "bike", "swim", "triathlon", "ski")

    Returns:
        bool: True если событие соответствует спорту, False иначе
    """
    normalized_code = normalize_sport_code(event_type_id)

    if not sport or sport == "all":
        return True

    return normalized_code == sport


async def fetch_competitions(
    city: Optional[str] = None,
    sport: Optional[str] = None,
    limit: int = 50,
    period_months: Optional[int] = None
) -> List[Dict]:
    """
    Получает список соревнований с Лиги Героев

    Args:
        city: Город для фильтрации (например, "Москва")
        sport: Тип спорта для фильтрации ("run", "bike", "swim", "triathlon", "ski")
        limit: Максимальное количество соревнований
        period_months: Период в месяцах от текущей даты

    Returns:
        List[Dict]: Список соревнований
    """

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": f"{BASE_URL}/calendar",
    }

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            logger.info(f"Fetching from HeroLeague API: {API_ENDPOINT}")

            async with session.get(
                API_ENDPOINT,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:

                if response.status != 200:
                    logger.error(f"HeroLeague API returned status {response.status}")
                    return []

                data = await response.json()

                events = data.get("values", [])
                logger.info(f"Received {len(events)} event types from HeroLeague")

                competitions = []

                # Обрабатываем каждое событие (тип соревнования) из API
                for event in events:
                    event_type_id = event.get("event_type", {}).get("public_id", "")

                    # Фильтруем по виду спорта (бег, велосипед и т.д.)
                    if not matches_sport_type(event_type_id, sport):
                        continue

                    # Каждое событие может проходить в нескольких городах
                    for city_event in event.get("event_city", []):
                        comp = parse_competition(event, city_event)

                        if not comp:
                            continue

                        # Фильтруем по городу если указан
                        if city and city.lower() not in comp.get("city", "").lower():
                            continue

                        # Фильтруем по периоду времени если указан
                        if period_months:
                            begin_date_str = comp.get("begin_date")
                            if begin_date_str:
                                try:
                                    # Парсим дату начала соревнования и добавляем UTC если нет timezone
                                    begin_date = datetime.fromisoformat(begin_date_str.replace('Z', '+00:00'))
                                    if begin_date.tzinfo is None:
                                        begin_date = begin_date.replace(tzinfo=timezone.utc)

                                    now = datetime.now(timezone.utc)
                                    year = now.year
                                    month = now.month

                                    # Вычисляем диапазон дат в зависимости от периода
                                    if period_months == 1:
                                        # Текущий месяц: с 1-го числа до конца месяца
                                        from datetime import timedelta
                                        start_date = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
                                        if month == 12:
                                            end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
                                        else:
                                            next_month_first = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=timezone.utc)
                                            end_date = next_month_first - timedelta(seconds=1)

                                    elif period_months == 12:
                                        # Текущий год: с 1 января до 31 декабря
                                        start_date = datetime(year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
                                        end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

                                    else:
                                        # По умолчанию: полгода вперед от текущей даты
                                        from datetime import timedelta
                                        start_date = now
                                        end_date = now + timedelta(days=180)

                                    # Пропускаем соревнования вне указанного диапазона
                                    if begin_date < start_date or begin_date > end_date:
                                        continue

                                    # Дополнительная проверка: пропускаем прошедшие события
                                    from datetime import timezone as tz
                                    now_utc = datetime.now(tz.utc)
                                    if begin_date.tzinfo is None:
                                        begin_date = begin_date.replace(tzinfo=tz.utc)
                                    if begin_date < now_utc:
                                        logger.debug(f"Skipping past event: '{comp.get('title')}' on {begin_date.strftime('%Y-%m-%d')}")
                                        continue
                                except ValueError as e:
                                    logger.warning(f"Date parsing error: {e}")
                                    continue

                        competitions.append(comp)

                        if len(competitions) >= limit:
                            break

                    if len(competitions) >= limit:
                        break

                logger.info(f"Processed {len(competitions)} competitions from HeroLeague")
                return competitions[:limit]

    except aiohttp.ClientError as e:
        logger.error(f"HTTP error while fetching HeroLeague competitions: {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching HeroLeague competitions: {e}", exc_info=True)
        return []


def parse_competition(event: Dict, city_event: Dict) -> Optional[Dict]:
    """
    Парсит информацию о соревновании из данных API

    Args:
        event: Данные о типе события
        city_event: Данные о конкретном событии в городе

    Returns:
        Optional[Dict]: Информация о соревновании или None
    """
    try:
        city_name = city_event.get("city", {}).get("name_ru", "")
        start_time = city_event.get("start_time", "")

        if not city_name or not start_time:
            return None

        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            formatted_date = start_dt.strftime("%d.%m.%Y")
        except:
            formatted_date = start_time[:10] if len(start_time) >= 10 else start_time

        original_sport_code = event.get("event_type", {}).get("public_id", "run")
        normalized_sport_code = normalize_sport_code(original_sport_code)

        city_event_id = city_event.get("public_id", "")

        comp = {
            "id": city_event_id,
            "title": event.get("title", ""),
            "code": event.get("public_id", ""),
            "city": city_name,
            "place": city_event.get("address", city_name),
            "sport_code": normalized_sport_code,  
            "organizer": "Лига Героев",
            "service": "HeroLeague",
            "begin_date": start_time,
            "end_date": start_time,  
            "formatted_date": formatted_date,
            "description": event.get("description", ""),
            "event_type": event.get("event_type", {}).get("title", ""),
            "registration_open": city_event.get("registration_open"),
            "registration_close": city_event.get("registration_close"),
            "url": f"{BASE_URL}/city_event/{city_event_id}",
            "distances": [],  
        }

        description = event.get("description", "")
        if description:
            comp["distances_text"] = description

        return comp

    except Exception as e:
        logger.error(f"Error parsing competition: {e}")
        return None


async def get_competition_details(competition_code: str) -> Optional[Dict]:
    """
    Получает детальную информацию о соревновании по его коду

    Args:
        competition_code: Код соревнования (public_id)

    Returns:
        Optional[Dict]: Детальная информация о соревновании или None
    """
    logger.warning(f"get_competition_details not yet implemented for HeroLeague")
    return None
