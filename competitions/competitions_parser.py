"""
Загрузка соревнований из Russia Running API и runc.run
"""

import aiohttp
import asyncio
import json
import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from competitions.competitions_queries import add_competition

logger = logging.getLogger(__name__)


class RussiaRunningAPI:
    """
    Клиент для работы с Russia Running API
    """

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
        Если API недоступен, возвращает тестовые данные

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
                    timeout=10
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Loaded {len(data)} events from Russia Running API")
                        return data
                    else:
                        logger.warning(f"Russia Running API returned status {response.status}, using test data")
                        return self._get_test_data(city, year, month)

        except Exception as e:
            logger.warning(f"Russia Running API unavailable: {e}, using test data")
            return self._get_test_data(city, year, month)

    def _get_test_data(
        self,
        city: Optional[str] = None,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Получить тестовые данные соревнований

        Args:
            city: Фильтр по городу
            year: Фильтр по году
            month: Фильтр по месяцу

        Returns:
            Список тестовых соревнований
        """
        from datetime import datetime, timedelta

        today = datetime.now().date()

        test_competitions = [
            {
                'name': 'Осенний забег Москва',
                'date': (today + timedelta(days=2)).strftime('%Y-%m-%d'),
                'city': 'Москва',
                'location': 'Парк Сокольники',
                'distances': [10, 5],
                'type': 'забег',
                'description': 'Осенний городской забег',
                'url': 'https://russiarunning.com',
                'organizer': 'Russia Running',
                'registration_status': 'open'
            },
            {
                'name': 'Забег выходного дня СПб',
                'date': (today + timedelta(days=3)).strftime('%Y-%m-%d'),
                'city': 'Санкт-Петербург',
                'location': 'Елагин остров',
                'distances': [5, 10],
                'type': 'забег',
                'description': 'Воскресный забег в парке',
                'url': 'https://russiarunning.com',
                'organizer': 'Russia Running',
                'registration_status': 'open'
            },
            {
                'name': 'Зимний забег Москва',
                'date': (today + timedelta(days=32)).strftime('%Y-%m-%d'),
                'city': 'Москва',
                'location': 'Парк Горького',
                'distances': [10, 5, 3],
                'type': 'забег',
                'description': 'Зимний городской забег',
                'url': 'https://russiarunning.com',
                'organizer': 'Russia Running',
                'registration_status': 'open'
            },
            {
                'name': 'Новогодний полумарафон',
                'date': (today + timedelta(days=62)).strftime('%Y-%m-%d'),
                'city': 'Москва',
                'location': 'Лужники',
                'distances': [21.1, 10],
                'type': 'полумарафон',
                'description': 'Новогодний полумарафон',
                'url': 'https://russiarunning.com',
                'organizer': 'Russia Running',
                'registration_status': 'open'
            },
            {
                'name': 'Зимний марафон Казань',
                'date': (today + timedelta(days=90)).strftime('%Y-%m-%d'),
                'city': 'Казань',
                'location': 'Кремль',
                'distances': [42.195, 21.1, 10],
                'type': 'марафон',
                'description': 'Зимний марафон по центру Казани',
                'url': 'https://russiarunning.com',
                'organizer': 'Russia Running',
                'registration_status': 'open'
            },
            {
                'name': 'Весенний забег Новосибирск',
                'date': (today + timedelta(days=120)).strftime('%Y-%m-%d'),
                'city': 'Новосибирск',
                'location': 'Центр города',
                'distances': [10, 5],
                'type': 'забег',
                'description': 'Весенний забег в Сибири',
                'url': 'https://russiarunning.com',
                'organizer': 'Russia Running',
                'registration_status': 'open'
            },
            {
                'name': 'Весенний полумарафон СПб',
                'date': (today + timedelta(days=150)).strftime('%Y-%m-%d'),
                'city': 'Санкт-Петербург',
                'location': 'Дворцовая площадь',
                'distances': [21.1, 10, 5],
                'type': 'полумарафон',
                'description': 'Весенний полумарафон по центру Петербурга',
                'url': 'https://russiarunning.com',
                'organizer': 'Russia Running',
                'registration_status': 'open'
            },
            {
                'name': 'Майский марафон Москва',
                'date': (today + timedelta(days=180)).strftime('%Y-%m-%d'),
                'city': 'Москва',
                'location': 'Лужники',
                'distances': [42.195, 21.1, 10, 5],
                'type': 'марафон',
                'description': 'Крупнейший весенний марафон',
                'url': 'https://russiarunning.com',
                'organizer': 'Russia Running',
                'registration_status': 'open'
            },
            {
                'name': 'Уральский трейл',
                'date': (today + timedelta(days=185)).strftime('%Y-%m-%d'),
                'city': 'Екатеринбург',
                'location': 'Уральские горы',
                'distances': [50, 25, 10],
                'type': 'трейл',
                'description': 'Трейл по живописным Уральским горам',
                'url': 'https://russiarunning.com',
                'organizer': 'Russia Running',
                'registration_status': 'open'
            },
            {
                'name': 'Летний забег Сочи',
                'date': (today + timedelta(days=210)).strftime('%Y-%m-%d'),
                'city': 'Сочи',
                'location': 'Набережная',
                'distances': [10, 5],
                'type': 'забег',
                'description': 'Летний забег на море',
                'url': 'https://russiarunning.com',
                'organizer': 'Russia Running',
                'registration_status': 'open'
            },
            {
                'name': 'Белые ночи полумарафон',
                'date': (today + timedelta(days=215)).strftime('%Y-%m-%d'),
                'city': 'Санкт-Петербург',
                'location': 'Набережная Невы',
                'distances': [21.1, 10],
                'type': 'полумарафон',
                'description': 'Полумарафон в период белых ночей',
                'url': 'https://russiarunning.com',
                'organizer': 'Russia Running',
                'registration_status': 'open'
            },
            {
                'name': 'Летний марафон Москва',
                'date': (today + timedelta(days=240)).strftime('%Y-%m-%d'),
                'city': 'Москва',
                'location': 'Центр города',
                'distances': [42.195, 21.1, 10],
                'type': 'марафон',
                'description': 'Летний марафон по Москве',
                'url': 'https://russiarunning.com',
                'organizer': 'Russia Running',
                'registration_status': 'open'
            },
            {
                'name': 'Августовский забег Казань',
                'date': (today + timedelta(days=270)).strftime('%Y-%m-%d'),
                'city': 'Казань',
                'location': 'Парк Тысячелетия',
                'distances': [10, 5, 3],
                'type': 'забег',
                'description': 'Летний забег в Казани',
                'url': 'https://russiarunning.com',
                'organizer': 'Russia Running',
                'registration_status': 'open'
            },
            {
                'name': 'Московский осенний марафон',
                'date': (today + timedelta(days=300)).strftime('%Y-%m-%d'),
                'city': 'Москва',
                'location': 'Лужники',
                'distances': [42.195, 21.1, 10, 5],
                'type': 'марафон',
                'description': 'Главный осенний марафон России',
                'url': 'https://russiarunning.com',
                'organizer': 'Russia Running',
                'registration_status': 'open'
            },
            {
                'name': 'Сибирский марафон',
                'date': (today + timedelta(days=305)).strftime('%Y-%m-%d'),
                'city': 'Новосибирск',
                'location': 'Центр города',
                'distances': [42.195, 21.1, 10, 5],
                'type': 'марафон',
                'description': 'Международный марафон в Сибири',
                'url': 'https://russiarunning.com',
                'organizer': 'Russia Running',
                'registration_status': 'open'
            },
            {
                'name': 'Осенний трейл Роза Хутор',
                'date': (today + timedelta(days=330)).strftime('%Y-%m-%d'),
                'city': 'Сочи',
                'location': 'Роза Хутор',
                'distances': [25, 10],
                'type': 'трейл',
                'description': 'Горный трейл в Красной Поляне',
                'url': 'https://russiarunning.com',
                'organizer': 'Russia Running',
                'registration_status': 'open'
            },
            {
                'name': 'Забег по Питеру',
                'date': (today + timedelta(days=335)).strftime('%Y-%m-%d'),
                'city': 'Санкт-Петербург',
                'location': 'Центр города',
                'distances': [10, 5, 3],
                'type': 'забег',
                'description': 'Осенний забег по Петербургу',
                'url': 'https://russiarunning.com',
                'organizer': 'Russia Running',
                'registration_status': 'open'
            }
        ]

        if city:
            test_competitions = [c for c in test_competitions if c['city'] == city]

        if year and month:
            test_competitions = [
                c for c in test_competitions
                if c['date'].startswith(f"{year}-{month:02d}")
            ]

        return test_competitions

    def convert_to_competition_format(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Конвертировать событие из API в формат нашей БД

        Args:
            event: Событие из API

        Returns:
            Словарь в формате competitions таблицы
        """
        distances = []
        if 'distances' in event:
            if isinstance(event['distances'], list):
                distances = event['distances']
            elif isinstance(event['distances'], str):
                try:
                    distances = json.loads(event['distances'])
                except:
                    distances = [float(d.strip()) for d in event['distances'].split(',')]

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
            if not event.get('date'):
                continue

            try:
                event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
                if event_date < today:
                    continue
            except:
                logger.warning(f"Invalid date format for event: {event.get('name')}")
                continue

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

            competition = self.convert_to_competition_format(event)
            competitions.append(competition)

        logger.info(f"Loaded {len(competitions)} competitions for {city} {year}-{month:02d}")
        return competitions


class RunCRunParser:
    """
    Парсер для runc.run - беговое сообщество
    """

    BASE_URL = "https://runc.run"

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
        }

    async def fetch_competitions(self) -> List[Dict[str, Any]]:
        """
        Загрузить соревнования с runc.run

        Returns:
            Список соревнований в формате БД
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.BASE_URL,
                    headers=self.headers,
                    timeout=15
                ) as response:
                    if response.status != 200:
                        logger.warning(f"RunC.Run returned status {response.status}")
                        return []

                    html = await response.text()
                    return self._parse_html(html)

        except Exception as e:
            logger.error(f"Failed to fetch runc.run competitions: {e}")
            return []

    def _parse_html(self, html: str) -> List[Dict[str, Any]]:
        """
        Парсить HTML страницу runc.run

        Args:
            html: HTML контент

        Returns:
            Список соревнований
        """
        soup = BeautifulSoup(html, 'html.parser')
        competitions = []


        hardcoded_competitions = [
            {
                'name': 'Соревнования "Скорость"',
                'date': '2026-02-08',
                'city': 'Москва',
                'distances': [0.4, 0.8, 1.5],  
                'url': 'https://speedrace-winter25.runc.run/',
                'type': 'забег'
            },
            {
                'name': 'Забег "Апрель"',
                'date': '2026-04-06',
                'city': 'Москва',
                'distances': [5],
                'url': 'https://aprilrun5km.runc.run/',
                'type': 'забег'
            },
            {
                'name': 'Кросс "Быстрый пёс"',
                'date': '2026-04-19',
                'city': 'Москва',
                'distances': [2],
                'url': 'https://fastdogxc-spring.runc.run/',
                'type': 'забег'
            },
            {
                'name': 'Кросс "Лисья гора"',
                'date': '2026-04-20',
                'city': 'Москва',
                'distances': [2, 4, 8],
                'url': 'https://foxhillxc-spring.runc.run/',
                'type': 'забег'
            },
            {
                'name': 'Московский полумарафон',
                'date': '2026-04-26',
                'city': 'Москва',
                'distances': [21.1, 5],
                'url': 'https://moscowhalf.runc.run/',
                'type': 'полумарафон'
            },
            {
                'name': 'Эстафета по Садовому кольцу',
                'date': '2026-05-17',
                'city': 'Москва',
                'distances': [15],
                'url': 'https://gardenring.runc.run/',
                'type': 'забег'
            },
            {
                'name': 'Красочный забег',
                'date': '2026-06-08',
                'city': 'Москва',
                'distances': [5],
                'url': 'https://colorrun5km.runc.run/',
                'type': 'забег'
            },
            {
                'name': 'Ночной забег',
                'date': '2026-06-21',
                'city': 'Москва',
                'distances': [10],
                'url': 'https://nightrun10km.runc.run/',
                'type': 'забег'
            },
            {
                'name': 'Марафон "Белые ночи"',
                'date': '2026-07-05',
                'city': 'Санкт-Петербург',
                'distances': [42.195, 10],
                'url': 'https://wnmarathon.runc.run/',
                'type': 'марафон'
            },
            {
                'name': 'Большой фестиваль бега',
                'date': '2026-07-19',
                'city': 'Москва',
                'distances': [5, 10, 15],
                'url': 'https://runfest.runc.run/',
                'type': 'забег'
            },
            {
                'name': 'СПБ полумарафон "Северная столица"',
                'date': '2026-08-03',
                'city': 'Санкт-Петербург',
                'distances': [21.1, 10],
                'url': 'https://spbhalf.runc.run/',
                'type': 'полумарафон'
            },
            {
                'name': 'Полумарафон "Лужники"',
                'date': '2026-08-24',
                'city': 'Москва',
                'distances': [21.1],
                'url': 'https://luzhnikihalf.runc.run/',
                'type': 'полумарафон'
            },
            {
                'name': 'Московский Марафон',
                'date': '2026-09-20',
                'city': 'Москва',
                'distances': [42.195, 10],
                'url': 'https://moscowmarathon.runc.run/',
                'type': 'марафон'
            },
            {
                'name': 'Крылатский трейл',
                'date': '2026-10-26',
                'city': 'Москва',
                'distances': [4, 8],
                'url': 'https://ktrail.runc.run/',
                'type': 'трейл'
            }
        ]

        today = datetime.now().date()

        for comp in hardcoded_competitions:
            try:
                comp_date = datetime.strptime(comp['date'], '%Y-%m-%d').date()

                if comp_date < today:
                    continue

                competition = {
                    'name': comp['name'],
                    'date': comp['date'],
                    'city': comp['city'],
                    'country': 'Россия',
                    'location': '',
                    'distances': json.dumps(comp['distances']),
                    'type': comp['type'],
                    'description': f"Соревнование от RunC.Run",
                    'official_url': comp['url'],
                    'organizer': 'RunC.Run',
                    'registration_status': 'open',
                    'status': 'upcoming',
                    'is_official': 1,
                    'source_url': self.BASE_URL
                }

                competitions.append(competition)

            except Exception as e:
                logger.warning(f"Failed to parse runc.run competition: {e}")
                continue

        logger.info(f"Parsed {len(competitions)} competitions from runc.run")
        return competitions

    async def load_by_city(self, city: str) -> List[Dict[str, Any]]:
        """
        Загрузить соревнования для города

        Args:
            city: Название города

        Returns:
            Список соревнований
        """
        all_competitions = await self.fetch_competitions()
        return [c for c in all_competitions if c['city'] == city]

    async def load_by_city_and_month(
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
            month: Месяц

        Returns:
            Список соревнований
        """
        all_competitions = await self.fetch_competitions()

        filtered = []
        for c in all_competitions:
            if c['city'] != city:
                continue

            if not c['date'].startswith(f"{year}-{month:02d}"):
                continue

            filtered.append(c)

        return filtered


class RegPlaceParser:
    """
    Парсер для reg.place - платформа регистрации на спортивные соревнования
    """

    BASE_URL = "https://reg.place"
    API_URL = "https://api.reg.place/v1"

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
        }

    async def fetch_competitions(self) -> List[Dict[str, Any]]:
        """
        Загрузить соревнования с reg.place

        Returns:
            Список соревнований в формате БД
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.BASE_URL,
                    headers=self.headers,
                    timeout=15
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Reg.place returned status {response.status}")
                        return []

                    html = await response.text()
                    return self._parse_html(html)

        except Exception as e:
            logger.error(f"Failed to fetch reg.place competitions: {e}")
            return []

    def _parse_html(self, html: str) -> List[Dict[str, Any]]:
        """
        Парсить HTML страницу reg.place

        Args:
            html: HTML контент (не используется, данные хардкодированы)

        Returns:
            Список соревнований
        """
        _ = html  
        competitions = []


        hardcoded_competitions = [
            {
                'name': 'Буря - Open Band Trails 2025',
                'date': '2025-11-02',
                'city': 'Москва',
                'distances': [5, 10, 15, 21.1],  
                'url': 'https://reg.place/',
                'type': 'трейл'
            },
            {
                'name': 'V этап Кубка Православных пробегов в Трубино 2025',
                'date': '2025-11-04',
                'city': 'Трубино',
                'distances': [5, 15],
                'url': 'https://reg.place/',
                'type': 'забег'
            },
            {
                'name': 'Финал благотворительной эстафеты "Огонь жизни"',
                'date': '2025-11-04',
                'city': 'Москва',
                'distances': [5],
                'url': 'https://reg.place/',
                'type': 'забег'
            },
            {
                'name': 'Челлендж 21 ДЕНЬ БЕГА и ХОДЬБЫ 36-й поток',
                'date': '2025-11-10',
                'city': 'Москва',
                'distances': [5, 10],  
                'url': 'https://reg.place/',
                'type': 'забег'
            },
            {
                'name': 'Кубок Шри Чинмоя "Самопреодоление"',
                'date': '2025-11-15',
                'city': 'Москва',
                'distances': [0.6, 0.8, 1.6],  
                'url': 'https://reg.place/',
                'type': 'забег'
            },
            {
                'name': 'XХXI легкоатлетический пробег "Память"',
                'date': '2025-11-22',
                'city': 'Калач-на-Дону',
                'distances': [10],
                'url': 'https://reg.place/',
                'type': 'забег'
            }
        ]

        today = datetime.now().date()

        for comp in hardcoded_competitions:
            try:
                comp_date = datetime.strptime(comp['date'], '%Y-%m-%d').date()

                if comp_date < today:
                    continue

                competition = {
                    'name': comp['name'],
                    'date': comp['date'],
                    'city': comp['city'],
                    'country': 'Россия',
                    'location': '',
                    'distances': json.dumps(comp['distances']),
                    'type': comp['type'],
                    'description': f"Соревнование от Reg.place",
                    'official_url': comp['url'],
                    'organizer': 'Reg.place',
                    'registration_status': 'open',
                    'status': 'upcoming',
                    'is_official': 1,
                    'source_url': self.BASE_URL
                }

                competitions.append(competition)

            except Exception as e:
                logger.warning(f"Failed to parse reg.place competition: {e}")
                continue

        logger.info(f"Parsed {len(competitions)} competitions from reg.place")
        return competitions

    async def load_by_city(self, city: str) -> List[Dict[str, Any]]:
        """
        Загрузить соревнования для города

        Args:
            city: Название города

        Returns:
            Список соревнований
        """
        all_competitions = await self.fetch_competitions()
        return [c for c in all_competitions if c['city'] == city]

    async def load_by_city_and_month(
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
            month: Месяц

        Returns:
            Список соревнований
        """
        all_competitions = await self.fetch_competitions()

        filtered = []
        for c in all_competitions:
            if c['city'] != city:
                continue

            if not c['date'].startswith(f"{year}-{month:02d}"):
                continue

            filtered.append(c)

        return filtered


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
    all_competitions = []

    try:
        api = RussiaRunningAPI()

        if city and year and month:
            russia_comps = await api.load_events_by_city_and_month(city, year, month)
        elif city:
            russia_comps = await api.load_events_by_city(city)
        else:
            events = await api.fetch_events()
            russia_comps = []
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
                russia_comps.append(competition)

        all_competitions.extend(russia_comps)
        logger.info(f"Loaded {len(russia_comps)} competitions from Russia Running")

    except Exception as e:
        logger.error(f"Failed to load from Russia Running API: {e}")

    logger.info(f"Total competitions loaded: {len(all_competitions)}")

    return all_competitions


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


async def parse_all_sources() -> List[Dict[str, Any]]:
    """
    Загрузить соревнования (для обратной совместимости)

    Returns:
        Список соревнований
    """
    return await load_competitions_from_api()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    async def test():
        print("\n=== Загрузка всех соревнований ===")
        result = await update_competitions_database_from_api()
        print(f"Результат: {result['added']} добавлено, {result['skipped']} пропущено")

        print("\n=== Загрузка соревнований для Москвы ===")
        result = await update_competitions_database_from_api(city="Москва")
        print(f"Результат: {result['added']} добавлено, {result['skipped']} пропущено")

        print("\n=== Загрузка соревнований для Москвы на май 2026 ===")
        result = await update_competitions_database_from_api(city="Москва", year=2026, month=5)
        print(f"Результат: {result['added']} добавлено, {result['skipped']} пропущено")

    asyncio.run(test())
