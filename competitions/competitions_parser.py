"""
Загрузка соревнований из Russia Running API
"""

import aiohttp
import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from competitions.competitions_queries import add_competition

logger = logging.getLogger(__name__)


class RussiaRunningAPI:
    """
    Клиент для работы с Russia Running API
    """

    # API endpoints
    BASE_URL = "https://russiarunning.com/api"
    EVENTS_URL = f"{BASE_URL}/events"

    def __init__(self):
        self.headers = {
            'User-Agent': 'TrainingDiaryBot/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    async def fetch_events(
        self,
        city: Optional[str] = None,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Загрузить соревнования из Russia Running API

        Args:
            city: Название города для фильтрации
            year: Год для фильтрации
            month: Месяц для фильтрации (1-12)

        Returns:
            Список соревнований
        """
        try:
            params = {}

            if city:
                params['city'] = city

            if year:
                params['year'] = year

            if month:
                params['month'] = month

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.EVENTS_URL,
                    headers=self.headers,
                    params=params,
                    timeout=30
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Loaded {len(data)} events from Russia Running API")
                        return data
                    else:
                        logger.error(f"Russia Running API error: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"Error fetching Russia Running API: {e}")
            return []

    def convert_to_competition_format(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Конвертировать событие из API в формат нашей БД

        Args:
            event: Событие из API

        Returns:
            Словарь в формате competitions таблицы
        """
        # Парсим дистанции
        distances = []
        if 'distances' in event:
            if isinstance(event['distances'], list):
                distances = event['distances']
            elif isinstance(event['distances'], str):
                try:
                    distances = json.loads(event['distances'])
                except:
                    # Если строка с числами через запятую
                    distances = [float(d.strip()) for d in event['distances'].split(',')]

        # Определяем тип соревнования по дистанции
        competition_type = 'забег'
        if distances:
            max_distance = max(distances)
            if max_distance >= 42:
                competition_type = 'марафон'
            elif max_distance >= 21:
                competition_type = 'полумарафон'
            elif max_distance >= 10:
                competition_type = 'забег'

        return {
            'name': event.get('name', 'Без названия'),
            'date': event.get('date'),
            'city': event.get('city', ''),
            'country': event.get('country', 'Россия'),
            'location': event.get('location', ''),
            'distances': json.dumps(distances) if distances else json.dumps([]),
            'type': event.get('type', competition_type),
            'description': event.get('description', ''),
            'official_url': event.get('url', event.get('official_url', '')),
            'organizer': event.get('organizer', 'Russia Running'),
            'registration_status': event.get('registration_status', 'open'),
            'status': 'upcoming',
            'is_official': 1,
            'source_url': 'https://russiarunning.com'
        }

    async def load_events_by_city(self, city: str) -> List[Dict[str, Any]]:
        """
        Загрузить соревнования для конкретного города

        Args:
            city: Название города

        Returns:
            Список соревнований в формате БД
        """
        events = await self.fetch_events(city=city)

        competitions = []
        today = datetime.now().date()

        for event in events:
            # Проверяем что есть дата
            if not event.get('date'):
                continue

            # Проверяем что дата в будущем
            try:
                event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
                if event_date < today:
                    continue
            except:
                logger.warning(f"Invalid date format for event: {event.get('name')}")
                continue

            # Конвертируем в формат БД
            competition = self.convert_to_competition_format(event)
            competitions.append(competition)

        logger.info(f"Loaded {len(competitions)} competitions for {city}")
        return competitions

    async def load_events_by_city_and_month(
        self,
        city: str,
        year: int,
        month: int
    ) -> List[Dict[str, Any]]:
        """
        Загрузить соревнования для города и месяца

        Args:
            city: Название города
            year: Год
            month: Месяц (1-12)

        Returns:
            Список соревнований в формате БД
        """
        events = await self.fetch_events(city=city, year=year, month=month)

        competitions = []

        for event in events:
            if not event.get('date'):
                continue

            # Конвертируем в формат БД
            competition = self.convert_to_competition_format(event)
            competitions.append(competition)

        logger.info(f"Loaded {len(competitions)} competitions for {city} {year}-{month:02d}")
        return competitions


async def load_competitions_from_api(
    city: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Загрузить соревнования из Russia Running API

    Args:
        city: Название города (опционально)
        year: Год (опционально)
        month: Месяц (опционально)

    Returns:
        Список соревнований в формате БД
    """
    api = RussiaRunningAPI()

    if city and year and month:
        return await api.load_events_by_city_and_month(city, year, month)
    elif city:
        return await api.load_events_by_city(city)
    else:
        # Загружаем все события
        events = await api.fetch_events()
        competitions = []
        today = datetime.now().date()

        for event in events:
            if not event.get('date'):
                continue

            try:
                event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
                if event_date < today:
                    continue
            except:
                continue

            competition = api.convert_to_competition_format(event)
            competitions.append(competition)

        return competitions


async def update_competitions_database_from_api(
    city: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None
) -> Dict[str, int]:
    """
    Обновить базу данных соревнований из Russia Running API

    Args:
        city: Город для фильтрации (опционально)
        year: Год для фильтрации (опционально)
        month: Месяц для фильтрации (опционально)

    Returns:
        Словарь с результатами: {'added': int, 'skipped': int, 'total': int}
    """
    logger.info("Updating competitions database from Russia Running API...")

    competitions = await load_competitions_from_api(city, year, month)

    added_count = 0
    skipped_count = 0

    for comp_data in competitions:
        try:
            # Проверяем есть ли уже такое соревнование
            # TODO: Добавить проверку дубликатов по названию и дате

            comp_id = await add_competition(comp_data)
            added_count += 1
            logger.info(f"Added: {comp_data['name']} (ID: {comp_id})")

        except Exception as e:
            skipped_count += 1
            logger.warning(f"Skipped {comp_data['name']}: {e}")

    logger.info(f"Update complete: {added_count} added, {skipped_count} skipped")
    return {
        'added': added_count,
        'skipped': skipped_count,
        'total': len(competitions)
    }


# Для обратной совместимости со старым кодом
async def parse_all_sources() -> List[Dict[str, Any]]:
    """
    Загрузить соревнования (для обратной совместимости)

    Returns:
        Список соревнований
    """
    return await load_competitions_from_api()


if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Пример использования
    async def test():
        # Тест 1: Загрузка всех соревнований
        print("\n=== Загрузка всех соревнований ===")
        result = await update_competitions_database_from_api()
        print(f"Результат: {result['added']} добавлено, {result['skipped']} пропущено")

        # Тест 2: Загрузка соревнований для Москвы
        print("\n=== Загрузка соревнований для Москвы ===")
        result = await update_competitions_database_from_api(city="Москва")
        print(f"Результат: {result['added']} добавлено, {result['skipped']} пропущено")

        # Тест 3: Загрузка соревнований для Москвы на май 2026
        print("\n=== Загрузка соревнований для Москвы на май 2026 ===")
        result = await update_competitions_database_from_api(city="Москва", year=2026, month=5)
        print(f"Результат: {result['added']} добавлено, {result['skipped']} пропущено")

    asyncio.run(test())
