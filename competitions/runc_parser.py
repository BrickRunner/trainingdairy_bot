"""
Парсер для получения соревнований с сайта RunC (runc.run)

Парсит HTML страницы results.runc.run для получения списка соревнований
"""

import aiohttp
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

BASE_URL = "https://results.runc.run"
EVENTS_LIST_URL = f"{BASE_URL}/"


def normalize_sport_code(event_name: str, distances: str) -> str:
    """
    Нормализует sport_code от RunC к стандартным кодам

    Args:
        event_name: Название события
        distances: Описание дистанций

    Returns:
        str: Стандартный код спорта ("run", "ski", "bike", "swim", "triathlon", "other")
    """
    combined_text = f"{event_name} {distances}".lower()

    # Проверяем ключевые слова для определения типа спорта
    if any(keyword in combined_text for keyword in ["лыж", "ski"]):
        return "ski"
    elif any(keyword in combined_text for keyword in ["велос", "bike", "вело"]):
        return "bike"
    elif any(keyword in combined_text for keyword in ["плав", "swim", "заплыв"]):
        return "swim"
    elif any(keyword in combined_text for keyword in ["триатлон", "triathlon", "акватлон"]):
        return "triathlon"
    elif any(keyword in combined_text for keyword in [
        "бег", "забег", "кросс", "марафон", "эстафет",
        "спринт", "run", "race", "км", " м", "метр"
    ]):
        return "run"
    else:
        # По умолчанию возвращаем "run" для беговых соревнований
        return "run"


def matches_sport_type(event_name: str, distances: str, sport: Optional[str]) -> bool:
    """
    Проверяет, соответствует ли событие выбранному спорту

    Args:
        event_name: Название события
        distances: Описание дистанций
        sport: Тип спорта для фильтрации ("run", "bike", "swim", "triathlon", "ski")

    Returns:
        bool: True если событие соответствует спорту, False иначе
    """
    # Нормализуем код спорта
    normalized_code = normalize_sport_code(event_name, distances)

    # Если фильтр "все" - показываем ВСЕ события
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
    Получает список соревнований с RunC

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
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        "Referer": BASE_URL,
    }

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            logger.info(f"Fetching from RunC: {EVENTS_LIST_URL}")

            async with session.get(
                EVENTS_LIST_URL,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:

                if response.status != 200:
                    logger.error(f"RunC returned status {response.status}")
                    return []

                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')

                # Парсим список соревнований
                # Ищем все ссылки на события вида /event/{id}/overview/
                event_links = soup.find_all('a', href=re.compile(r'/event/\d+/overview/'))
                logger.info(f"Found {len(event_links)} event links on RunC")

                competitions = []
                processed_ids = set()  # Чтобы избежать дубликатов

                for link in event_links:
                    # Извлекаем ID события из URL
                    match = re.search(r'/event/(\d+)/overview/', link.get('href', ''))
                    if not match:
                        continue

                    event_id = match.group(1)

                    # Пропускаем дубликаты
                    if event_id in processed_ids:
                        continue

                    processed_ids.add(event_id)

                    # Парсим информацию о соревновании
                    comp = parse_competition_from_link(link, event_id)

                    if not comp:
                        continue

                    # Фильтр по городу
                    if city and city.lower() not in comp.get("city", "").lower():
                        continue

                    # Фильтр по спорту
                    event_name = comp.get("title", "")
                    distances = comp.get("distances_text", "")
                    if not matches_sport_type(event_name, distances, sport):
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
                                now_utc = datetime.now(timezone.utc)
                                if begin_date.tzinfo is None:
                                    begin_date = begin_date.replace(tzinfo=timezone.utc)
                                if begin_date < now_utc:
                                    logger.debug(f"Skipping past event: '{comp.get('title')}' on {begin_date.strftime('%Y-%m-%d')}")
                                    continue
                            except ValueError as e:
                                logger.warning(f"Date parsing error: {e}")
                                continue

                    competitions.append(comp)

                    if len(competitions) >= limit:
                        break

                logger.info(f"Processed {len(competitions)} competitions from RunC")
                return competitions[:limit]

    except aiohttp.ClientError as e:
        logger.error(f"HTTP error while fetching RunC competitions: {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching RunC competitions: {e}", exc_info=True)
        return []


def parse_competition_from_link(link, event_id: str) -> Optional[Dict]:
    """
    Парсит информацию о соревновании из ссылки на главной странице

    Args:
        link: BeautifulSoup элемент ссылки
        event_id: ID события

    Returns:
        Optional[Dict]: Информация о соревновании или None
    """
    try:
        # Получаем весь текст из ссылки
        text_content = link.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text_content.split("\n") if line.strip()]

        if len(lines) < 3:
            logger.debug(f"Not enough data in link for event {event_id}")
            return None

        # Предполагаемая структура:
        # [0] - Город или тип
        # [1] - Дистанции (от X до Y)
        # [2] - Название соревнования
        # [3] - Город (повторно)
        # [4] - Дата

        title = ""
        city = "Москва"  # По умолчанию
        distances_text = ""
        date_str = ""

        # Ищем название (обычно самая длинная строка или содержит кавычки)
        for line in lines:
            if '"' in line or "«" in line or "»" in line:
                title = line
                break
            # Если строка содержит слова, характерные для названий
            if any(word in line.lower() for word in ["соревнован", "кросс", "марафон", "забег", "эстафет"]):
                title = line
                break

        # Если не нашли название, берем первую подходящую строку
        if not title and lines:
            title = lines[0]

        # Ищем дистанции (содержит "км" или "м")
        for line in lines:
            if any(unit in line.lower() for unit in [" км", " м", "метр", "от ", "до "]):
                if not any(skip in line.lower() for skip in ["соревнован", "кросс", "марафон"]):
                    distances_text = line
                    break

        # Ищем город (обычно "Москва", "Санкт-Петербург" и т.д.)
        for line in lines:
            if any(city_name in line for city_name in ["Москва", "Санкт-Петербург", "Казань", "Екатеринбург", "Новосибирск"]):
                city = line
                break

        # Ищем дату (содержит цифры и месяцы)
        months_ru = ["января", "февраля", "марта", "апреля", "мая", "июня",
                     "июля", "августа", "сентября", "октября", "ноября", "декабря"]
        for line in lines:
            if any(month in line.lower() for month in months_ru):
                date_str = line
                break

        # Парсим дату в ISO формат
        begin_date = parse_russian_date(date_str) if date_str else datetime.now(timezone.utc).isoformat()
        formatted_date = date_str if date_str else "Дата уточняется"

        # Определяем тип спорта
        normalized_sport_code = normalize_sport_code(title, distances_text)

        comp = {
            "id": event_id,
            "title": title,
            "code": event_id,
            "city": city,
            "place": city,
            "sport_code": normalized_sport_code,
            "organizer": "RunC",
            "service": "RunC",
            "begin_date": begin_date,
            "end_date": begin_date,
            "formatted_date": formatted_date,
            "description": distances_text,
            "distances_text": distances_text,
            "url": f"{BASE_URL}/event/{event_id}/overview/",
            "distances": [],  # Пустой список дистанций (не структурированы на главной)
        }

        return comp

    except Exception as e:
        logger.error(f"Error parsing competition {event_id}: {e}", exc_info=True)
        return None


def parse_russian_date(date_str: str) -> str:
    """
    Парсит русскую дату в ISO формат

    Args:
        date_str: Строка с датой (например, "22 ноября 2025")

    Returns:
        str: Дата в ISO формате
    """
    try:
        # Словарь соответствия русских месяцев
        months_map = {
            "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
            "мая": 5, "июня": 6, "июля": 7, "августа": 8,
            "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12
        }

        # Ищем паттерн "DD месяца YYYY" или "DD-DD месяца YYYY"
        pattern = r'(\d{1,2})(?:-\d{1,2})?\s+(\w+)\s+(\d{4})'
        match = re.search(pattern, date_str)

        if match:
            day = int(match.group(1))
            month_name = match.group(2).lower()
            year = int(match.group(3))

            month = months_map.get(month_name)
            if month:
                date_obj = datetime(year, month, day, 0, 0, 0, tzinfo=timezone.utc)
                return date_obj.isoformat()

        # Если не получилось распарсить, возвращаем текущую дату
        return datetime.now(timezone.utc).isoformat()

    except Exception as e:
        logger.warning(f"Error parsing date '{date_str}': {e}")
        return datetime.now(timezone.utc).isoformat()


async def get_competition_details(competition_id: str) -> Optional[Dict]:
    """
    Получает детальную информацию о соревновании по его ID

    Args:
        competition_id: ID соревнования

    Returns:
        Optional[Dict]: Детальная информация о соревновании или None
    """
    # TODO: Реализовать получение детальной информации о дистанциях
    # Можно парсить страницу /event/{id}/overview/ для более подробной информации
    logger.warning(f"get_competition_details not yet implemented for RunC")
    return None
