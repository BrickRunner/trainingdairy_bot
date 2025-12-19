"""
Парсер для получения соревнований с сайта reg.place

API Endpoint: GET https://api.reg.place/v1/events
"""

import aiohttp
import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

BASE_URL = "https://api.reg.place/v1"
# Пробуем различные возможные endpoint'ы для списка событий
POSSIBLE_ENDPOINTS = [
    f"{BASE_URL}/events",
    f"{BASE_URL}/event/list",
    f"{BASE_URL}/search",
    "https://reg.place/api/events",  # Возможно API без /v1
]


def normalize_sport_code(sport_type: str) -> str:
    """
    Нормализует sport_code от reg.place к стандартным кодам

    Args:
        sport_type: Тип спорта (slug или название, например: "swimming", "cycling", "skiing", "running")

    Returns:
        str: Стандартный код спорта ("run", "bike", "swim", "triathlon", "ski")
    """
    if not sport_type:
        logger.warning("Empty sport_type provided, defaulting to 'run'")
        return "run"

    sport_lower = sport_type.lower()

    # Маппинг slug-ов API reg.place на стандартные коды
    # Проверяем точное совпадение slug сначала
    slug_mapping = {
        "swimming": "swim",
        "cycling": "bike",
        "skiing": "ski",
        "running": "run",
        "triathlon": "triathlon",
        "duathlon": "triathlon",
        "other": "other",  # "Другой вид" - отдельный код
    }

    if sport_lower in slug_mapping:
        result = slug_mapping[sport_lower]
        logger.debug(f"Normalized sport via slug: '{sport_type}' -> '{result}'")
        return result

    # Маппинг типов спорта на стандартные коды (для совместимости)
    if any(keyword in sport_lower for keyword in ["run", "бег", "марафон", "забег", "trail", "трейл"]):
        result = "run"
    elif any(keyword in sport_lower for keyword in ["bike", "cycling", "велос", "вело", "cycle"]):
        result = "bike"
    elif any(keyword in sport_lower for keyword in ["swim", "плав", "заплыв"]):
        result = "swim"
    elif any(keyword in sport_lower for keyword in ["triathlon", "триатлон", "duathlon", "дуатлон"]):
        result = "triathlon"
    elif any(keyword in sport_lower for keyword in ["ski", "лыж", "лыжн"]):
        result = "ski"
    else:
        # Неизвестный тип спорта - логируем и возвращаем "run" по умолчанию
        logger.warning(f"Unknown sport type '{sport_type}', defaulting to 'run'")
        result = "run"

    logger.debug(f"Normalized sport: '{sport_type}' -> '{result}'")
    return result


async def fetch_competitions(
    city: Optional[str] = None,
    sport: Optional[str] = None,
    limit: int = 50,
    period_months: Optional[int] = None
) -> List[Dict]:
    """
    Получает список соревнований с reg.place

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
    }

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            # Пробуем различные endpoint'ы
            data = None
            successful_endpoint = None

            for endpoint in POSSIBLE_ENDPOINTS:
                try:
                    logger.info(f"Trying reg.place endpoint: {endpoint}")

                    async with session.get(
                        endpoint,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:

                        if response.status == 200:
                            data = await response.json()
                            successful_endpoint = endpoint
                            logger.info(f"SUCCESS! reg.place endpoint {endpoint} returned status 200")
                            logger.info(f"Response type: {type(data)}")
                            break
                        else:
                            logger.warning(f"reg.place endpoint {endpoint} returned status {response.status}")

                except asyncio.TimeoutError:
                    logger.warning(f"Timeout for endpoint {endpoint}")
                except Exception as e:
                    logger.warning(f"Error trying endpoint {endpoint}: {e}")

            if not data:
                logger.error("No working endpoint found for reg.place")
                return []

            logger.info(f"Using endpoint: {successful_endpoint}")

            # Проверяем формат ответа
            events = []
            if isinstance(data, list):
                events = data
            elif isinstance(data, dict):
                # Возможно данные в ключе events, items, data и т.д.
                for key in ['events', 'items', 'data', 'results']:
                    if key in data and isinstance(data[key], list):
                        events = data[key]
                        break

                if not events:
                    logger.warning(f"Could not find events list in response. Keys: {list(data.keys())}")
                    return []

            logger.info(f"Found {len(events)} events from reg.place")

            # Вычисляем диапазон дат для фильтра по периоду (как в RussiaRunning)
            start_date = None
            end_date = None
            if period_months:
                from datetime import timezone, timedelta
                now = datetime.now(timezone.utc)

                if period_months == 1:
                    # 1 месяц - с 1-го до последнего дня текущего месяца
                    year = now.year
                    month = now.month

                    # Начало месяца в 00:00:00
                    start_date = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)

                    # Находим последний день текущего месяца
                    if month == 12:
                        # Декабрь - последний день 31
                        end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
                    else:
                        # Первый день следующего месяца минус 1 секунда
                        next_month_first = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=timezone.utc)
                        end_date = next_month_first - timedelta(seconds=1)

                elif period_months == 12:
                    # 1 год - с 01.01 до 31.12 текущего года
                    year = now.year
                    start_date = datetime(year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
                    end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

                else:
                    # 6 месяцев - от текущей даты + 180 дней
                    start_date = now
                    end_date = now + timedelta(days=180)

                logger.info(f"Period filter: {period_months} months, from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

            # Парсим события
            competitions = []
            logger.info(f"Applying filters: city={city}, sport={sport}")
            for event in events:
                try:
                    comp = parse_event(event)
                    if comp:
                        # Логируем перед фильтрацией
                        logger.debug(f"Before filtering: '{comp.get('title')}' - sport_code='{comp.get('sport_code')}', city='{comp.get('city')}'")

                        # Применяем фильтры
                        if not matches_filters(comp, city, sport):
                            logger.debug(f"Event '{comp.get('title')}' was filtered out")
                            continue

                        logger.info(f"Event '{comp.get('title')}' passed all filters!")

                        # Фильтр по периоду (с начала до конца указанного периода)
                        if period_months and start_date and end_date:
                            comp_date = comp.get('start_time')
                            if comp_date:
                                # Делаем дату timezone-aware если она naive
                                if comp_date.tzinfo is None:
                                    from datetime import timezone as tz
                                    comp_date = comp_date.replace(tzinfo=tz.utc)

                                # Событие должно быть в диапазоне start_date <= comp_date <= end_date
                                if comp_date < start_date or comp_date > end_date:
                                    continue

                        # Дополнительная проверка: событие должно быть в будущем (>= сегодня)
                        comp_date = comp.get('start_time')
                        if comp_date:
                            if comp_date.tzinfo is None:
                                from datetime import timezone as tz
                                comp_date = comp_date.replace(tzinfo=tz.utc)

                            # Проверяем что событие не в прошлом
                            from datetime import timezone, timedelta
                            now_utc = datetime.now(timezone.utc)
                            if comp_date < now_utc:
                                logger.debug(f"Skipping past event: '{comp.get('title')}' on {comp_date.strftime('%Y-%m-%d')}")
                                continue

                        competitions.append(comp)

                        if len(competitions) >= limit:
                            break

                except Exception as e:
                    logger.error(f"Error parsing reg.place event: {e}")
                    continue

            logger.info(f"Parsed {len(competitions)} competitions from reg.place after filters")
            return competitions

    except Exception as e:
        logger.error(f"Error fetching from reg.place: {e}")
        return []


def parse_event(event: Dict) -> Optional[Dict]:
    """
    Парсит одно событие из API reg.place

    Args:
        event: Данные события из API

    Returns:
        Dict: Распарсенное соревнование или None
    """
    try:
        # Логируем структуру первого события для отладки
        if not hasattr(parse_event, '_logged_structure'):
            logger.info(f"reg.place event structure keys: {list(event.keys())}")
            parse_event._logged_structure = True

        # Получаем основные данные
        slug = event.get('slug', '')
        event_id = event.get('id', '') or event.get('event_id', '')
        name = event.get('name', '') or event.get('title', '')

        # Используем короткий event_id для callback_data (max 64 bytes)
        # slug используем только для URL
        short_id = str(event_id) if event_id else slug
        url_identifier = slug or event_id

        if not short_id or not name:
            logger.warning(f"Missing identifier or name in event: slug={slug}, id={event_id}, name={name}")
            return None

        # Дата события
        start_time_str = event.get('start_time') or event.get('date') or event.get('start_date')
        if not start_time_str:
            return None

        # Парсим дату
        try:
            if isinstance(start_time_str, str):
                # Пробуем различные форматы
                for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%SZ']:
                    try:
                        start_time = datetime.strptime(start_time_str, fmt)
                        break
                    except:
                        continue
                else:
                    # Не удалось распарсить
                    start_time = datetime.now()
            else:
                start_time = datetime.now()
        except:
            start_time = datetime.now()

        # Город
        city = event.get('city', {})
        if isinstance(city, dict):
            city_name = city.get('name', '') or city.get('title', '')
        else:
            city_name = str(city) if city else ''

        # Тип спорта - в API reg.place используется поле 'sports' (массив)
        sports = event.get('sports', [])
        if sports and isinstance(sports, list) and len(sports) > 0:
            # Берём первый вид спорта из массива
            sport_obj = sports[0]
            if isinstance(sport_obj, dict):
                # Используем slug (например: "swimming", "cycling", "skiing")
                sport_type = sport_obj.get('slug', '') or sport_obj.get('name', '')
            else:
                sport_type = ''
        else:
            # Fallback на старые поля (на случай изменения API)
            sport_type = event.get('sport_type', '') or event.get('sport', '') or event.get('type', '')

        sport_code = normalize_sport_code(sport_type) if sport_type else 'run'

        # Дистанции - пробуем разные возможные поля
        races = event.get('races', []) or event.get('distances', []) or event.get('items', [])
        distances = []

        logger.debug(f"Event '{name}': races field = {bool(event.get('races'))}, distances field = {bool(event.get('distances'))}, items field = {bool(event.get('items'))}")
        logger.debug(f"Event '{name}' has races data: {bool(races)}, type: {type(races)}, count: {len(races) if isinstance(races, list) else 'N/A'}")

        if races and isinstance(races, list):
            for i, race in enumerate(races):
                if isinstance(race, dict):
                    # Пробуем разные варианты названия поля дистанции
                    distance = race.get('distance') or race.get('length') or race.get('distance_km')
                    distance_name = race.get('name', '') or race.get('title', '') or race.get('distance_name', '')

                    logger.debug(f"  Race {i}: distance={distance}, name={distance_name}, keys={list(race.keys())}")

                    if distance:
                        try:
                            # Конвертируем в км
                            distance_km = float(distance) / 1000 if distance > 100 else float(distance)
                            distances.append({
                                'distance': distance_km,
                                'name': distance_name or f"{distance_km} км"
                            })
                            logger.debug(f"  ✓ Added distance: {distance_km} km, name: '{distance_name}'")
                        except Exception as e:
                            logger.warning(f"  ✗ Failed to parse distance: {distance}, error: {e}")
                    else:
                        logger.debug(f"  ✗ Skipping race without distance field: {list(race.keys())}")
                else:
                    logger.debug(f"  ✗ Race {i} is not a dict: {type(race)}")
        else:
            if races:
                logger.warning(f"Event '{name}': races is not a list, type: {type(races)}")
            else:
                logger.info(f"Event '{name}': no races data found in API response")

        logger.info(f"Event '{name}' parsed with {len(distances)} distances (races data: {bool(races)})")

        # URL события - пробуем получить из API или формируем сами
        event_url = event.get('url', '') or event.get('link', '')
        if not event_url:
            # Формируем URL из идентификатора (используем url_identifier для полного URL)
            event_url = f"https://reg.place/event/{url_identifier}"

        # Если URL относительный, делаем абсолютным
        if event_url and not event_url.startswith('http'):
            event_url = f"https://reg.place{event_url if event_url.startswith('/') else '/' + event_url}"

        logger.debug(f"Event URL: {event_url} (from API: {bool(event.get('url'))})")

        # Формируем результат в формате совместимом с другими парсерами
        comp = {
            'id': f"regplace_{short_id}",  # Короткий уникальный ID с префиксом
            'title': name,
            'name': name,  # Дублируем для совместимости
            'url': event_url,
            'city': city_name,
            'place': city_name,  # Для совместимости (используется в show_competition_detail)
            'date': start_time.strftime('%d.%m.%Y'),
            'begin_date': start_time.isoformat(),  # ISO формат для парсинга дат
            'end_date': start_time.isoformat(),    # ISO формат для парсинга дат
            'sport_code': sport_code,
            'service': 'reg.place',
            'distances': distances,
            'start_time': start_time
        }

        return comp

    except Exception as e:
        logger.error(f"Error parsing reg.place event: {e}")
        return None


def matches_filters(comp: Dict, city: Optional[str], sport: Optional[str]) -> bool:
    """
    Проверяет, соответствует ли соревнование фильтрам

    Args:
        comp: Соревнование
        city: Фильтр по городу
        sport: Фильтр по виду спорта

    Returns:
        bool: True если соответствует фильтрам
    """
    comp_title = comp.get('title', 'Unknown')

    # Фильтр по городу
    if city and city != "all":
        comp_city = comp.get('city', '').lower()
        if city.lower() not in comp_city:
            logger.debug(f"Filtering out '{comp_title}': city '{comp_city}' doesn't match '{city}'")
            return False

    # Фильтр по спорту
    if sport and sport != "all" and sport is not None:
        comp_sport = comp.get('sport_code', '')
        # Проверяем точное совпадение
        if comp_sport != sport:
            logger.debug(f"Filtering out '{comp_title}': sport '{comp_sport}' doesn't match '{sport}'")
            return False
        logger.debug(f"Event '{comp_title}' matched sport filter: '{comp_sport}' == '{sport}'")
    else:
        logger.debug(f"Event '{comp_title}' - no sport filter applied (sport={sport})")

    logger.debug(f"Event '{comp_title}' passed filters (city={city}, sport={sport})")
    return True
