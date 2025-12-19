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

    # ВАЖНО: Проверяем лыжи РАНЬШЕ, чем бег, так как "skirun" содержит "run"
    # Маппинг типов событий HeroLeague на стандартные коды
    if any(keyword in event_type_lower for keyword in ["skirun", "snowrun", "ski", "лыж"]):
        return "ski"
    # "Гонка Героев", "Гонка Героев Зима" и тренировочные лагеря относятся к "другим видам спорта"
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
        # По умолчанию возвращаем "other" для неизвестных типов
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
    # Нормализуем код спорта
    normalized_code = normalize_sport_code(event_type_id)

    # Если фильтр "все" - показываем ВСЕ события (включая camp)
    if not sport or sport == "all":
        return True

    # Проверяем соответствие выбранному спорту
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

                # Извлекаем события из ответа
                events = data.get("values", [])
                logger.info(f"Received {len(events)} event types from HeroLeague")

                competitions = []

                # Обрабатываем каждый тип события
                for event in events:
                    event_type_id = event.get("event_type", {}).get("public_id", "")

                    # Фильтр по спорту
                    if not matches_sport_type(event_type_id, sport):
                        continue

                    # Обрабатываем каждый город в событии
                    for city_event in event.get("event_city", []):
                        comp = parse_competition(event, city_event)

                        if not comp:
                            continue

                        # Фильтр по городу
                        if city and city.lower() not in comp.get("city", "").lower():
                            continue

                        # Фильтр по периоду
                        if period_months:
                            begin_date_str = comp.get("begin_date")
                            if begin_date_str:
                                try:
                                    begin_date = datetime.fromisoformat(begin_date_str.replace('Z', '+00:00'))
                                    if begin_date.tzinfo is None:
                                        begin_date = begin_date.replace(tzinfo=timezone.utc)

                                    now = datetime.now(timezone.utc)
                                    year = now.year
                                    month = now.month

                                    # Вычисляем диапазон дат как в других парсерах
                                    if period_months == 1:
                                        # 1 месяц - с 1-го до последнего дня текущего месяца
                                        from datetime import timedelta
                                        start_date = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
                                        if month == 12:
                                            end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
                                        else:
                                            next_month_first = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=timezone.utc)
                                            end_date = next_month_first - timedelta(seconds=1)

                                    elif period_months == 12:
                                        # 1 год - с 01.01 до 31.12 текущего года
                                        start_date = datetime(year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
                                        end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

                                    else:
                                        # 6 месяцев - от текущей даты + 180 дней
                                        from datetime import timedelta
                                        start_date = now
                                        end_date = now + timedelta(days=180)

                                    # Событие должно быть в диапазоне start_date <= begin_date <= end_date
                                    if begin_date < start_date or begin_date > end_date:
                                        continue

                                    # Дополнительная проверка: событие должно быть в будущем (>= сегодня)
                                    from datetime import timezone as tz
                                    now_utc = datetime.now(tz.utc)
                                    # Делаем begin_date timezone-aware если он naive
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

        # Форматируем дату
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            formatted_date = start_dt.strftime("%d.%m.%Y")
        except:
            formatted_date = start_time[:10] if len(start_time) >= 10 else start_time

        # Получаем оригинальный sport_code и нормализуем его
        original_sport_code = event.get("event_type", {}).get("public_id", "run")
        normalized_sport_code = normalize_sport_code(original_sport_code)

        # Для уникальной идентификации используем city_event ID в URL
        city_event_id = city_event.get("public_id", "")

        comp = {
            "id": city_event_id,
            "title": event.get("title", ""),
            "code": event.get("public_id", ""),
            "city": city_name,
            "place": city_event.get("address", city_name),
            "sport_code": normalized_sport_code,  # Используем нормализованный код
            "organizer": "Лига Героев",
            "service": "HeroLeague",
            "begin_date": start_time,
            "end_date": start_time,  # Для HeroLeague используем start_time как end_date
            "formatted_date": formatted_date,
            "description": event.get("description", ""),
            "event_type": event.get("event_type", {}).get("title", ""),
            "registration_open": city_event.get("registration_open"),
            "registration_close": city_event.get("registration_close"),
            # ВАЖНО: используем city_event ID для уникальности URL
            "url": f"{BASE_URL}/city_event/{city_event_id}",
            "distances": [],  # Пустой список дистанций (они не структурированы в API)
        }

        # Добавляем информацию о дистанциях из описания
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
    # TODO: Реализовать получение детальной информации о дистанциях
    # Возможно, потребуется дополнительный API запрос или парсинг страницы события
    logger.warning(f"get_competition_details not yet implemented for HeroLeague")
    return None
