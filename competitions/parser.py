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

        # Формируем payload согласно требованиям API
        payload = {
            "Page": {
                "Skip": skip,
                "Take": min(take, 100)  # Ограничение API
            },
            "Filter": {
                "EventsLoaderType": 0  # 0 = только будущие события
            },
            "Language": language
        }

        # Добавляем фильтры если указаны
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
        # API игнорирует фильтр по городу, поэтому получаем больше данных
        # и фильтруем на стороне бота
        # Увеличиваем лимит для фильтрации по городу
        fetch_limit = limit * 5 if city else limit

        # ПРИМЕЧАНИЕ: Фильтр по периоду (period_months) не используется
        # API возвращает максимум 100 записей, отсортированных по дате
        # Поэтому показываем все доступные соревнования из API

        # Получаем данные из API (только фильтр по спорту работает)
        data = await self.get_events(
            skip=0,
            take=100,  # Максимум что позволяет API
            city=None,  # API игнорирует этот параметр
            sport=sport
        )

        competitions = []
        events_list = data.get("list", [])

        for event in events_list:
            try:
                # Извлекаем базовую информацию
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
                }

                # Даты
                comp["begin_date"] = event.get("beginDate")
                comp["end_date"] = event.get("endDate")

                # URL события
                code = event.get("code", "")
                if code:
                    comp["url"] = f"https://reg.russiarunning.com/event/{code}"
                else:
                    comp["url"] = ""

                # Дистанции из raceItems
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

                # Фильтрация по городу на стороне бота
                if city:
                    # Проверяем различные поля с названием города
                    event_city = event.get('cityName') or ''
                    event_place = event.get('place') or ''
                    event_address = event.get('address') or ''
                    event_title = event.get('title') or ''

                    # Приводим к нижнему регистру для сравнения
                    city_lower = city.lower()
                    event_city_lower = event_city.lower()
                    event_place_lower = event_place.lower()
                    event_address_lower = event_address.lower()
                    event_title_lower = event_title.lower()

                    # Проверяем вхождение города в различных полях
                    # Приоритет: адрес > место > название события > cityName (т.к. cityName может быть неточным)
                    city_found = (
                        city_lower in event_address_lower or
                        city_lower in event_place_lower or
                        city_lower in event_title_lower or
                        city_lower in event_city_lower
                    )

                    if not city_found:
                        continue  # Пропускаем событие, если город не найден

                competitions.append(comp)

                # Ограничиваем количество результатов
                if len(competitions) >= limit:
                    break

            except Exception as e:
                logger.error(f"Error parsing event {event.get('id', 'unknown')}: {e}")
                continue

        return competitions


# Вспомогательные функции для использования в handlers

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
    # Получаем все соревнования и ищем нужное
    # TODO: Можно оптимизировать если есть отдельный endpoint для получения по ID
    async with RussiaRunningParser() as parser:
        data = await parser.get_events(take=100)
        events_list = data.get("list", [])

        for event in events_list:
            if event.get("id") == competition_id:
                # Преобразуем в упрощенную структуру
                comps = await parser.get_competitions(limit=100)
                for comp in comps:
                    if comp["id"] == competition_id:
                        return comp

    return None


# Константы для видов спорта (можно расширить)
SPORT_CODES = {
    "Бег": "run",
    "Велоспорт": "bike",
    "Триатлон": "triathlon",
    "Лыжи": "ski",
    "Плавание": "swim",
}

# Обратный словарь
SPORT_NAMES = {v: k for k, v in SPORT_CODES.items()}
