"""
Модуль для получения данных о соревнованиях с API timerman.org
"""

import aiohttp
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

BASE_URL = "https://timerman.org"
API_ENDPOINT = "/api/events/list/ru"  # Реальный endpoint для получения списка событий

# Функции для проверки соответствия виду спорта (аналогично parser.py)
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
        # Бег: все что содержит run, бег, trail, трейл
        return any(keyword in sport_code_lower or keyword in sport_name_lower
                   for keyword in ["run", "бег", "trail", "трейл", "трал", "running", "забег"])

    elif target_sport == "swim":
        # Плавание: все что содержит swim или плав
        return any(keyword in sport_code_lower or keyword in sport_name_lower
                   for keyword in ["swim", "плав", "swimming", "заплыв", "open-water"])

    elif target_sport == "bike":
        # Велоспорт: все что содержит bike, cycle, велос
        return any(keyword in sport_code_lower or keyword in sport_name_lower
                   for keyword in ["bike", "cycle", "cycling", "велосипед", "велоспорт", "велогонка"])

    return False


def matches_sport_type(event: Dict, target_sport: str) -> bool:
    """
    Проверяет, относится ли событие к указанному виду спорта

    Args:
        event: Событие из API (полный объект с сокращенными полями: dc, dn, t, ri)
        target_sport: Целевой вид спорта (run, swim, bike, all)

    Returns:
        True если событие содержит указанный вид спорта
    """
    if target_sport == "all":
        return True

    # Проверяем основную дисциплину события (dc = disciplineCode, dn = disciplineName)
    event_sport_code = event.get('dc', '') or event.get('disciplineCode', '')
    event_sport_name = event.get('dn', '') or event.get('disciplineName', '')

    if check_sport_match(event_sport_code, event_sport_name, target_sport):
        return True

    # Проверяем название события (t = title)
    event_title = event.get('t', '') or event.get('title', '')
    event_title_lower = event_title.lower()
    if target_sport == "swim" and any(keyword in event_title_lower for keyword in ["плав", "swim", "заплыв"]):
        return True
    elif target_sport == "bike" and any(keyword in event_title_lower for keyword in ["bike", "cycle", "cycling", "велосипед", "велоспорт", "велогонка"]):
        return True
    elif target_sport == "run" and any(keyword in event_title_lower for keyword in ["бег", "run", "trail", "трейл", "забег"]):
        return True

    # Проверяем дисциплины в дистанциях (ri = raceItems)
    race_items = event.get('ri', []) or event.get('raceItems', []) or event.get('distances', [])
    for race in race_items:
        race_code = race.get('dc', '') or race.get('disciplineCode', '')
        race_name = race.get('dn', '') or race.get('disciplineName', '') or race.get('n', '') or race.get('name', '')

        if check_sport_match(race_code, race_name, target_sport):
            return True

        # Проверяем название дистанции (n = name)
        race_title = race.get('n', '') or race.get('name', '')
        race_title_lower = race_title.lower()
        if target_sport == "swim" and any(keyword in race_title_lower for keyword in ["плав", "swim", "заплыв"]):
            return True
        elif target_sport == "bike" and any(keyword in race_title_lower for keyword in ["bike", "cycle", "cycling", "велосипед", "велоспорт", "велогонка"]):
            return True
        elif target_sport == "run" and any(keyword in race_title_lower for keyword in ["бег", "run", "trail", "трейл", "забег"]):
            return True

    return False


class TimmermanParser:
    """Парсер для получения данных о соревнованиях с API timerman.org"""

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
            take: Количество записей для получения
            city: Фильтр по городу
            sport: Фильтр по виду спорта
            language: Язык ответа

        Returns:
            Словарь с ключами:
            - list: список событий
            - totalCount: общее количество
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = BASE_URL + API_ENDPOINT

        # Структура payload согласно реальному API Timerman
        payload = {
            "EventsLoaderType": 0,  # 0 = предстоящие события
            "UseTenantBeneficiaryCode": True,
            "Skip": skip,
            "Take": min(take, 100),
            "DisciplinesCodes": None,
            "DateFrom": None,
            "DateTo": None,
            "FromAge": 11,
            "HidePastEvents": False,
            "InSportmasterChampionship": False,
            "IntoRayRussiaRunnung": False,
            "NationalMovementOnly": False,
            "OnlyWithAdmissions": False,
            "OnlyWithOpenRegistration": False,
            "ResultsCalculated": False,
            "RrRecomended": False,
            "SortRule": {"Type": 0, "Direction": 1},
            "SportSeriesCode": None,
            "StarRaitings": [],
            "ToAge": None,
            "ApprovedStarRaitingOnly": False,
        }

        try:
            async with self.session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    # API возвращает массив событий напрямую
                    if isinstance(data, list):
                        return {"list": data, "totalCount": len(data)}
                    # Или объект с полем Items/TotalCount (с заглавными буквами!)
                    elif isinstance(data, dict):
                        events = data.get("Items") or data.get("events") or data.get("items") or data.get("list") or []
                        total = data.get("TotalCount") or data.get("totalCount") or data.get("total") or len(events)
                        return {"list": events, "totalCount": total}
                    else:
                        logger.error(f"Unexpected data type from Timerman API: {type(data)}")
                        return {"list": [], "totalCount": 0}
                else:
                    logger.error(f"Timerman API returned status {response.status}")
                    error_text = await response.text()
                    logger.error(f"Response: {error_text[:500]}")
                    return {"list": [], "totalCount": 0}

        except Exception as e:
            logger.error(f"Error fetching events from Timerman: {e}")
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
            city: Название города для фильтрации
            sport: Код вида спорта ("run", "bike", "swim", "all")
            limit: Максимальное количество результатов
            period_months: Период в месяцах

        Returns:
            Список словарей с информацией о соревнованиях
        """
        # Вычисляем период если указан
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

        # Получаем события
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

        logger.info(f"Fetched {len(all_events)} events from Timerman API in {request_num + 1} requests")

        competitions = []
        filtered_count = 0
        filtered_by_period = 0
        filtered_by_city = 0
        filtered_by_sport = 0

        for event in all_events:
            try:
                # Извлекаем базовую информацию (структура API Timerman)
                comp = {
                    "id": event.get("c", ""),  # c = code
                    "title": event.get("t", ""),  # t = title
                    "code": event.get("c", ""),
                    "city": event.get("p", ""),  # p = place
                    "place": event.get("p", ""),
                    "address": event.get("address", ""),
                    "sport_code": event.get("dc", "run"),  # dc = disciplineCode
                    "image_url": event.get("ImageUrl", ""),
                    "participants_count": event.get("pc", 0),  # pc = participantsCount
                    "organizer": event.get("on", "Timerman"),  # on = organizerName
                    "service": "Timerman",  # Сервис регистрации
                }

                # Даты
                comp["begin_date"] = event.get("d")  # d = date
                comp["end_date"] = event.get("ed") or event.get("d")  # ed = endDate

                # URL события
                code = event.get("c", "")
                if code:
                    comp["url"] = f"https://timerman.org/event/{code}"
                else:
                    comp["url"] = ""

                # Дистанции (ri = raceItems)
                distances = []
                race_items = event.get("ri", [])
                for race in race_items:
                    distances.append({
                        "id": race.get("id", ""),
                        "name": race.get("n", ""),  # n = name
                        "distance": race.get("d", 0),  # d = distance
                        "sport": race.get("dn", ""),  # dn = disciplineName
                        "sport_code": race.get("dc", ""),  # dc = disciplineCode
                        "participants_count": race.get("pc", 0),  # pc = participantsCount
                        "race_date": race.get("sd")  # sd = startDate
                    })

                comp["distances"] = distances

                # Фильтрация по периоду
                if (start_date or end_date) and comp["begin_date"]:
                    try:
                        from datetime import timezone
                        begin_date_str = comp["begin_date"].replace('Z', '+00:00')
                        begin_date_obj = datetime.fromisoformat(begin_date_str)

                        # Если дата не имеет timezone, добавляем UTC
                        if begin_date_obj.tzinfo is None:
                            begin_date_obj = begin_date_obj.replace(tzinfo=timezone.utc)

                        if start_date and begin_date_obj < start_date:
                            filtered_count += 1
                            filtered_by_period += 1
                            continue
                        if end_date and begin_date_obj > end_date:
                            filtered_count += 1
                            filtered_by_period += 1
                            continue
                    except Exception as e:
                        logger.error(f"Error parsing date for event {comp['id']}: {e}")

                # Фильтрация по городу
                if city:
                    event_city = event.get('cityName') or event.get('city') or ''
                    event_place = event.get('place') or ''
                    event_address = event.get('address') or ''
                    event_title = event.get('title') or event.get('name') or ''

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

                # Фильтрация по виду спорта
                if sport:
                    sport_matches = matches_sport_type(event, sport)

                    if not sport_matches:
                        filtered_by_sport += 1
                        continue

                competitions.append(comp)

                if len(competitions) >= limit:
                    break

            except Exception as e:
                logger.error(f"Error parsing Timerman event {event.get('id', 'unknown')}: {e}")
                continue

        logger.info(f"Timerman filtering results: kept {len(competitions)} events, filtered out {filtered_count} total")
        if filtered_by_period > 0:
            logger.info(f"  - Filtered by period: {filtered_by_period} events")
        if filtered_by_city > 0:
            logger.info(f"  - Filtered by city: {filtered_by_city} events")
        if filtered_by_sport > 0:
            logger.info(f"  - Filtered by sport: {filtered_by_sport} events")

        return competitions


# Вспомогательные функции для использования в handlers

async def fetch_competitions(
    city: Optional[str] = None,
    sport: Optional[str] = None,
    limit: int = 50,
    period_months: Optional[int] = None
) -> List[Dict]:
    """
    Получить список соревнований с Timerman

    Args:
        city: Название города
        sport: Код вида спорта ("run", "bike", "swim", "all")
        limit: Максимальное количество результатов
        period_months: Период в месяцах для фильтрации

    Returns:
        Список соревнований
    """
    async with TimmermanParser() as parser:
        return await parser.get_competitions(city, sport, limit, period_months)
