"""
Модуль для получения данных о соревнованиях с API reg.russiarunning.com
"""

import aiohttp
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

BASE_URL = "https://reg.russiarunning.com"
API_ENDPOINT = "/api/events/list"

def check_sport_match(sport_code: str, sport_name: str, target_sport: str) -> bool:
    """
    Проверяет, соответствует ли одна дисциплина указанному виду спорта

    Args:
        sport_code: Код дисциплины
        sport_name: Название дисциплины
        target_sport: Целевой вид спорта (run, swim, bike, all)

    Returns:
        True если дисциплина соответствует виду спорта
    """
    if target_sport == "all":
        return True

    sport_code_lower = (sport_code or "").lower()
    sport_name_lower = (sport_name or "").lower()

    if target_sport == "run":
        return any(keyword in sport_code_lower or keyword in sport_name_lower
                   for keyword in ["run", "бег", "trail", "трейл", "трал", "running"])

    elif target_sport == "swim":
        return any(keyword in sport_code_lower or keyword in sport_name_lower
                   for keyword in ["swim", "плав", "swimming", "заплыв", "open-water"])

    elif target_sport == "bike":
        return any(keyword in sport_code_lower or keyword in sport_name_lower
                   for keyword in ["bike", "cycle", "cycling", "велосипед", "велоспорт", "велогонка"])

    return False


def matches_sport_type(event: Dict, target_sport: str) -> bool:
    """
    Проверяет, относится ли событие к указанному виду спорта
    Анализирует основную дисциплину И дисциплины всех дистанций (raceItems)
    А также названия события и дистанций для более точного определения

    Args:
        event: Событие из API (полный объект)
        target_sport: Целевой вид спорта (run, swim, bike, all)

    Returns:
        True если событие содержит указанный вид спорта
    """
    if target_sport == "all":
        return True

    event_sport_code = event.get('disciplineCode', '')
    event_sport_name = event.get('disciplineName', '')

    if check_sport_match(event_sport_code, event_sport_name, target_sport):
        return True

    event_title = event.get('title', '').lower()
    if target_sport == "swim" and any(keyword in event_title for keyword in ["плав", "swim", "заплыв"]):
        return True
    elif target_sport == "bike" and any(keyword in event_title for keyword in ["bike", "cycle", "cycling", "велосипед", "велоспорт", "велогонка"]):
        return True
    elif target_sport == "run" and any(keyword in event_title for keyword in ["бег", "run", "trail", "трейл"]):
        return True

    race_items = event.get('raceItems', [])
    for race in race_items:
        race_code = race.get('disciplineCode', '')
        race_name = race.get('disciplineName', '')

        if check_sport_match(race_code, race_name, target_sport):
            return True

        race_title = race.get('name', '').lower()
        if target_sport == "swim" and any(keyword in race_title for keyword in ["плав", "swim", "заплыв"]):
            return True
        elif target_sport == "bike" and any(keyword in race_title for keyword in ["bike", "cycle", "cycling", "велосипед", "велоспорт", "велогонка"]):
            return True
        elif target_sport == "run" and any(keyword in race_title for keyword in ["бег", "run", "trail", "трейл"]):
            return True

    return False


class RussiaRunningParser:
    """Парсер для получения данных о соревнованиях с API reg.russiarunning.com"""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Создание сессии при входе в контекстный менеджер"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие сессии при выходе из контекстного менеджера"""
        if self.session:
            await self.session.close()

    async def get_events(
        self,
        skip: int = 0,
        take: int = 50,
        city: Optional[str] = None,
        sport: Optional[str] = None,
        language: str = "ru"
    ) -> Dict:
        """
        Получить список соревнований

        Args:
            skip: Количество пропускаемых записей (пагинация)
            take: Количество записей для получения (макс 50-100)
            city: Фильтр по городу (название города)
            sport: Фильтр по виду спорта (код дисциплины, например "run")
            language: Язык ответа ("ru" или "en")

        Returns:
            Словарь с ключами:
            - list: список событий
            - totalCount: общее количество
            - pageSize: размер страницы
            - currentPage: текущая страница
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = BASE_URL + API_ENDPOINT

        payload = {
            "Page": {
                "Skip": skip,
                "Take": min(take, 100)  
            },
            "Filter": {
                "EventsLoaderType": 0  
            },
            "Language": language
        }

        if city:
            payload["Filter"]["CityName"] = city
        if sport:
            payload["Filter"]["DisciplineCode"] = sport

        try:
            async with self.session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"API returned status {response.status}")
                    error_text = await response.text()
                    logger.error(f"Response: {error_text[:500]}")
                    return {"list": [], "totalCount": 0}

        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            return {"list": [], "totalCount": 0}

    async def get_competitions(
        self,
        city: Optional[str] = None,
        sport: Optional[str] = None,
        limit: int = 50,
        period_months: Optional[int] = None
    ) -> List[Dict]:
        """
        Получить список соревнований с упрощенной структурой

        Args:
            city: Название города для фильтрации (фильтруется на стороне бота)
            sport: Код вида спорта ("run", "bike", и т.д.)
            limit: Максимальное количество результатов
            period_months: Период в месяцах (фильтровать соревнования в пределах периода)

        Returns:
            Список словарей с информацией о соревнованиях:
            [
                {
                    "id": "uuid",
                    "title": "Название соревнования",
                    "date": "2025-12-15T10:00:00Z",
                    "city": "Москва",
                    "place": "Парк Горького",
                    "sport": "Бег",
                    "sport_code": "run",
                    "distances": [
                        {"name": "5 км", "distance": 5.0},
                        {"name": "10 км", "distance": 10.0}
                    ],
                    "image_url": "https://...",
                    "participants_count": 150,
                    "url": "https://reg.russiarunning.com/event/..."
                }
            ]
        """

        start_date = None
        end_date = None
        if period_months:
            from datetime import timezone
            now = datetime.now(timezone.utc)

            if period_months == 1:
                year = now.year
                month = now.month

                start_date = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)

                if month == 12:
                    last_day = 31
                else:
                    next_month = datetime(year, month + 1, 1, tzinfo=timezone.utc)
                    last_day_date = next_month - timedelta(days=1)
                    last_day = last_day_date.day

                end_date = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)

            elif period_months == 12:
                year = now.year
                start_date = datetime(year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
                end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

            else:
                start_date = now
                end_date = now + timedelta(days=180)

        all_events = []
        skip = 0
        batch_size = 100
        max_requests = 20  

        for request_num in range(max_requests):
            data = await self.get_events(
                skip=skip,
                take=batch_size,
                city=None,  
                sport=None  
            )

            events_batch = data.get("list", [])
            if not events_batch:
                break

            all_events.extend(events_batch)

            if len(events_batch) < batch_size:
                break

            skip += batch_size

        logger.info(f"Fetched {len(all_events)} events from API in {request_num + 1} requests")

        if period_months:
            start_str = start_date.strftime('%Y-%m-%d') if start_date else 'None'
            end_str = end_date.strftime('%Y-%m-%d') if end_date else 'None'
            logger.info(f"Filtering by period: {period_months} months, from {start_str} to {end_str}")

        competitions = []
        events_list = all_events
        filtered_count = 0  
        filtered_by_period = 0
        filtered_by_city = 0
        filtered_by_sport = 0

        for event in events_list:
            try:
                comp = {
                    "id": event.get("id", ""),
                    "title": event.get("title", ""),
                    "code": event.get("code", ""),
                    "city": event.get("cityName") or event.get("place", ""),
                    "place": event.get("place", ""),
                    "address": event.get("address", ""),
                    "sport_code": event.get("disciplineCode", "run"),
                    "image_url": event.get("imageUrl", ""),
                    "participants_count": event.get("participantsCount", 0),
                    "organizer": event.get("organizerName", ""),
                    "service": "RussiaRunning",  
                }

                comp["begin_date"] = event.get("beginDate")
                comp["end_date"] = event.get("endDate")

                code = event.get("code", "")
                if code:
                    comp["url"] = f"https://reg.russiarunning.com/event/{code}"
                else:
                    comp["url"] = ""

                distances = []
                race_items = event.get("raceItems", [])
                for race in race_items:
                    distances.append({
                        "id": race.get("id", ""),
                        "name": race.get("name", ""),
                        "distance": race.get("distance", 0),
                        "sport": race.get("disciplineName", ""),
                        "sport_code": race.get("disciplineCode", ""),
                        "participants_count": race.get("participantsCount", 0),
                        "race_date": race.get("raceDate")
                    })

                comp["distances"] = distances

                if (start_date or end_date) and comp["begin_date"]:
                    try:
                        begin_date_obj = datetime.fromisoformat(comp["begin_date"].replace('Z', '+00:00'))
                        if start_date and begin_date_obj < start_date:
                            filtered_count += 1
                            filtered_by_period += 1
                            continue
                        if end_date and begin_date_obj > end_date:
                            filtered_count += 1
                            filtered_by_period += 1
                            continue

                        from datetime import timezone as tz
                        now_utc = datetime.now(tz.utc)
                        if begin_date_obj.tzinfo is None:
                            begin_date_obj = begin_date_obj.replace(tzinfo=tz.utc)
                        if begin_date_obj < now_utc:
                            filtered_count += 1
                            filtered_by_period += 1
                            logger.debug(f"Skipping past event: '{comp['title']}' on {begin_date_obj.strftime('%Y-%m-%d')}")
                            continue
                    except Exception as e:
                        logger.error(f"Error parsing date for event {comp['id']}: {e}")

                if city:
                    event_city = event.get('cityName') or ''
                    event_place = event.get('place') or ''
                    event_address = event.get('address') or ''
                    event_title = event.get('title') or ''

                    city_lower = city.lower()
                    event_city_lower = event_city.lower()
                    event_place_lower = event_place.lower()
                    event_address_lower = event_address.lower()
                    event_title_lower = event_title.lower()

                    city_found = (
                        city_lower in event_address_lower or
                        city_lower in event_place_lower or
                        city_lower in event_title_lower or
                        city_lower in event_city_lower
                    )

                    if not city_found:
                        filtered_by_city += 1
                        continue  

                if sport:
                    sport_matches = matches_sport_type(event, sport)

                    if sport == "swim" and ('плав' in event.get('title', '').lower() or 'swim' in event.get('title', '').lower()):
                        logger.info(f"Swimming event check: '{event.get('title', '')}' - disciplineCode: {event.get('disciplineCode')}, disciplineName: {event.get('disciplineName')}, matches: {sport_matches}")

                    if not sport_matches:
                        filtered_by_sport += 1
                        continue  

                competitions.append(comp)

                if len(competitions) >= limit:
                    break

            except Exception as e:
                logger.error(f"Error parsing event {event.get('id', 'unknown')}: {e}")
                continue

        logger.info(f"Filtering results: kept {len(competitions)} events, filtered out {filtered_count} total")
        if filtered_by_period > 0:
            logger.info(f"  - Filtered by period: {filtered_by_period} events")
        if filtered_by_city > 0:
            logger.info(f"  - Filtered by city: {filtered_by_city} events")
        if filtered_by_sport > 0:
            logger.info(f"  - Filtered by sport: {filtered_by_sport} events")

        return competitions



async def fetch_competitions(
    city: Optional[str] = None,
    sport: Optional[str] = None,
    limit: int = 50,
    period_months: Optional[int] = None
) -> List[Dict]:
    """
    Получить список соревнований

    Args:
        city: Название города
        sport: Код вида спорта ("run", "bike", и т.д.)
        limit: Максимальное количество результатов
        period_months: Период в месяцах для фильтрации

    Returns:
        Список соревнований
    """
    async with RussiaRunningParser() as parser:
        return await parser.get_competitions(city, sport, limit, period_months)


async def fetch_competition_by_id(competition_id: str) -> Optional[Dict]:
    """
    Получить информацию о конкретном соревновании по ID

    Args:
        competition_id: ID соревнования

    Returns:
        Словарь с информацией о соревновании или None
    """
    async with RussiaRunningParser() as parser:
        data = await parser.get_events(take=100)
        events_list = data.get("list", [])

        for event in events_list:
            if event.get("id") == competition_id:
                comps = await parser.get_competitions(limit=100)
                for comp in comps:
                    if comp["id"] == competition_id:
                        return comp

    return None


SPORT_CODES = {
    "Бег": "run",
    "Плавание": "swim",
    "Велоспорт": "bike",
    "Лыжи": "ski",
    "Триатлон": "triathlon",
    "Все виды спорта": "all",
}

SPORT_NAMES = {v: k for k, v in SPORT_CODES.items()}

SPORT_NAMES["camp"] = "Лига Путешествий"
SPORT_NAMES["other"] = "Другое"
