"""
Парсер для получения соревнований с сайта "Беговое Сообщество" (runc.run)

Парсит HTML страницы runc.run для получения списка соревнований
"""

import aiohttp
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

BASE_URL = "https://runc.run"
EVENTS_LIST_URL = f"{BASE_URL}/"


def normalize_sport_code(event_name: str, distances: str) -> str:
    """
    Нормализует sport_code от Бегового Сообщества к стандартным кодам

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
    Получает список соревнований с сайта "Беговое Сообщество"

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

                # Парсим список соревнований из меню
                # Ищем элементы с классом header-menu-sub-menu-race-item
                event_items = soup.find_all('div', class_='header-menu-sub-menu-race-item')
                logger.info(f"Found {len(event_items)} event items on RunC")

                competitions = []
                processed_urls = set()  # Чтобы избежать дубликатов

                for item in event_items:
                    # Ищем ссылку на событие
                    link = item.find('a', class_='header-menu-sub-menu-race-item__race-name')

                    # Пропускаем если это ссылка на результаты или нет ссылки
                    if not link or 'results.runc.run' in link.get('href', ''):
                        continue

                    event_url = link.get('href', '')

                    # Пропускаем дубликаты
                    if event_url in processed_urls:
                        continue

                    processed_urls.add(event_url)

                    # Парсим информацию о соревновании
                    comp = parse_competition_from_menu_item(item)

                    if not comp:
                        continue

                    # Фильтр по городу
                    if city and city.lower() not in comp.get("city", "").lower():
                        continue

                    # Фильтр по спорту
                    event_name = comp.get("title", "")
                    distances_text = comp.get("distances_text", "")
                    if not matches_sport_type(event_name, distances_text, sport):
                        continue

                    # ВАЖНО: Получаем детальную информацию с дистанциями
                    # Это необходимо для корректного отображения в боте
                    try:
                        logger.info(f"Fetching details for: {comp.get('title')}")
                        detailed_comp = await get_competition_details(
                            comp.get('url'),
                            begin_date=comp.get('begin_date'),
                            end_date=comp.get('end_date')
                        )
                        if detailed_comp:
                            # Используем детальную информацию вместо базовой
                            comp = detailed_comp
                    except Exception as e:
                        logger.warning(f"Could not fetch details for {comp.get('title')}: {e}")
                        # Продолжаем с базовой информацией

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


def parse_competition_from_menu_item(item) -> Optional[Dict]:
    """
    Парсит информацию о соревновании из элемента меню на главной странице

    Args:
        item: BeautifulSoup элемент div с классом header-menu-sub-menu-race-item

    Returns:
        Optional[Dict]: Информация о соревновании или None
    """
    try:
        # Извлекаем дату
        date_elem = item.find('div', class_='header-menu-sub-menu-race-item__date')
        date_str = date_elem.get_text(strip=True) if date_elem else ""

        # Извлекаем название и ссылку
        link = item.find('a', class_='header-menu-sub-menu-race-item__race-name')
        if not link:
            return None

        title = link.get_text(strip=True)
        url = link.get('href', '')

        # Если URL относительный, делаем его абсолютным
        if url.startswith('/'):
            url = f"{BASE_URL}{url}"

        # Парсим дату в ISO формат (получаем кортеж begin_date, end_date)
        if date_str:
            begin_date, end_date = parse_russian_date_short(date_str)
        else:
            now_iso = datetime.now(timezone.utc).isoformat()
            begin_date, end_date = now_iso, now_iso

        # Проверка: событие должно быть в будущем
        if date_str:
            try:
                date_obj = datetime.fromisoformat(begin_date.replace('Z', '+00:00'))
                if date_obj.tzinfo is None:
                    date_obj = date_obj.replace(tzinfo=timezone.utc)

                now_utc = datetime.now(timezone.utc)
                if date_obj < now_utc:
                    logger.debug(f"Skipping past event: '{title}' on {date_obj.strftime('%Y-%m-%d')}")
                    return None
            except ValueError:
                pass

        # Генерируем ID из URL
        event_id = url.replace('https://', '').replace('http://', '').replace('/', '_').replace('.', '_')

        # Город по умолчанию (большинство событий в Москве)
        city = "Москва"

        # Определяем тип спорта
        normalized_sport_code = normalize_sport_code(title, title)

        comp = {
            "id": event_id,
            "title": title,
            "code": event_id,
            "city": city,
            "place": city,
            "sport_code": normalized_sport_code,
            "organizer": "Беговое Сообщество",
            "service": "Беговое Сообщество",
            "begin_date": begin_date,
            "end_date": end_date,  # Теперь используем правильную end_date
            "formatted_date": date_str if date_str else "Дата уточняется",
            "description": title,
            "distances_text": "Уточняется на сайте",  # Будет обновлено при вызове get_competition_details
            "url": url,
            "distances": [],  # Будет заполнено при вызове get_competition_details
        }

        logger.info(f"Parsed event: {title} ({date_str}) - {url}")
        return comp

    except Exception as e:
        logger.error(f"Error parsing competition from menu item: {e}", exc_info=True)
        return None


def parse_russian_date_short(date_str: str) -> tuple:
    """
    Парсит короткую русскую дату в ISO формат (например, "21-22 февраля")

    Args:
        date_str: Строка с датой (например, "21-22 февраля")

    Returns:
        tuple: (begin_date, end_date) в ISO формате
    """
    try:
        # Словарь соответствия русских месяцев
        months_map = {
            "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
            "мая": 5, "июня": 6, "июля": 7, "августа": 8,
            "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12
        }

        # Ищем паттерн "DD-DD месяца" (диапазон) или "DD месяца" (один день)
        pattern_range = r'(\d{1,2})-(\d{1,2})\s+(\w+)'
        pattern_single = r'(\d{1,2})\s+(\w+)'

        match_range = re.search(pattern_range, date_str)
        if match_range:
            # Диапазон дат
            start_day = int(match_range.group(1))
            end_day = int(match_range.group(2))
            month_name = match_range.group(3).lower()

            month = months_map.get(month_name)
            if month:
                # Определяем год - если месяц уже прошел в этом году, берем следующий год
                now = datetime.now(timezone.utc)
                year = now.year

                # Если месяц меньше текущего, событие в следующем году
                if month < now.month:
                    year += 1
                elif month == now.month and start_day < now.day:
                    year += 1

                begin_date = datetime(year, month, start_day, 0, 0, 0, tzinfo=timezone.utc)
                end_date = datetime(year, month, end_day, 0, 0, 0, tzinfo=timezone.utc)

                return (begin_date.isoformat(), end_date.isoformat())

        # Пробуем один день
        match_single = re.search(pattern_single, date_str)
        if match_single:
            day = int(match_single.group(1))
            month_name = match_single.group(2).lower()

            month = months_map.get(month_name)
            if month:
                # Определяем год - если месяц уже прошел в этом году, берем следующий год
                now = datetime.now(timezone.utc)
                year = now.year

                # Если месяц меньше текущего, событие в следующем году
                if month < now.month:
                    year += 1
                elif month == now.month and day < now.day:
                    year += 1

                date_obj = datetime(year, month, day, 0, 0, 0, tzinfo=timezone.utc)
                return (date_obj.isoformat(), date_obj.isoformat())

        # Если не получилось распарсить, возвращаем текущую дату
        now_iso = datetime.now(timezone.utc).isoformat()
        return (now_iso, now_iso)

    except Exception as e:
        logger.warning(f"Error parsing date '{date_str}': {e}")
        now_iso = datetime.now(timezone.utc).isoformat()
        return (now_iso, now_iso)


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
            "organizer": "Беговое Сообщество",
            "service": "Беговое Сообщество",
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


async def get_competition_details(
    competition_url: str,
    begin_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Optional[Dict]:
    """
    Получает детальную информацию о соревновании по его URL

    Args:
        competition_url: URL соревнования (например, https://speedrace.runc.run/)
        begin_date: Дата начала из меню (если уже известна)
        end_date: Дата окончания из меню (если уже известна)

    Returns:
        Optional[Dict]: Детальная информация о соревновании или None
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        "Referer": BASE_URL,
    }

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            event_url = competition_url
            logger.info(f"Fetching event details from: {event_url}")

            async with session.get(
                event_url,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:

                if response.status != 200:
                    logger.error(f"RunC event details returned status {response.status}")
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')

                # Извлекаем название события
                title_elem = soup.find('h1') or soup.find('h2', class_=re.compile('title|name|event'))
                title = title_elem.get_text(strip=True) if title_elem else "Без названия"

                # Извлекаем информацию о дистанциях
                distances, distances_text = parse_distances_from_detail_page(soup)

                # Извлекаем дату (используем переданные даты если есть)
                if not begin_date or not end_date:
                    date_elem = soup.find(text=re.compile(r'\d{1,2}\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{4}'))
                    date_str = date_elem.strip() if date_elem else ""
                    if date_str:
                        # parse_russian_date возвращает одну дату
                        begin_date = parse_russian_date(date_str)
                        end_date = begin_date  # Для детальных страниц обычно указана полная дата
                    else:
                        now_iso = datetime.now(timezone.utc).isoformat()
                        begin_date = now_iso
                        end_date = now_iso

                # Формируем formatted_date из переданных дат
                date_str = ""
                if begin_date and end_date:
                    try:
                        begin_dt = datetime.fromisoformat(begin_date.replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

                        # Русские названия месяцев
                        months_ru = ["", "января", "февраля", "марта", "апреля", "мая", "июня",
                                    "июля", "августа", "сентября", "октября", "ноября", "декабря"]

                        if begin_dt.date() == end_dt.date():
                            # Один день
                            date_str = f"{begin_dt.day} {months_ru[begin_dt.month]} {begin_dt.year}"
                        else:
                            # Диапазон дат
                            if begin_dt.month == end_dt.month:
                                date_str = f"{begin_dt.day}-{end_dt.day} {months_ru[begin_dt.month]} {begin_dt.year}"
                            else:
                                date_str = f"{begin_dt.day} {months_ru[begin_dt.month]} - {end_dt.day} {months_ru[end_dt.month]} {begin_dt.year}"
                    except:
                        date_str = "Дата уточняется"

                # Извлекаем город
                city = "Москва"  # По умолчанию
                city_elem = soup.find(text=re.compile(r'(Москва|Санкт-Петербург|Казань|Екатеринбург|Новосибирск)'))
                if city_elem:
                    city = city_elem.strip()

                # Определяем тип спорта
                sport_code = normalize_sport_code(title, distances_text)

                # Генерируем ID из URL
                competition_id = competition_url.replace('https://', '').replace('http://', '').replace('/', '_').replace('.', '_')

                event_details = {
                    "id": competition_id,
                    "title": title,
                    "code": competition_id,
                    "city": city,
                    "place": city,
                    "sport_code": sport_code,
                    "organizer": "Беговое Сообщество",
                    "service": "Беговое Сообщество",
                    "begin_date": begin_date,
                    "end_date": end_date,
                    "formatted_date": date_str if date_str else "Дата уточняется",
                    "description": distances_text,
                    "distances_text": distances_text,
                    "url": event_url,
                    "distances": distances,
                }

                logger.info(f"Successfully parsed event {competition_id}: {title} with {len(distances)} distances")
                return event_details

    except aiohttp.ClientError as e:
        logger.error(f"HTTP error while fetching event details: {e}")
        return None
    except Exception as e:
        logger.error(f"Error fetching event details for {competition_id}: {e}", exc_info=True)
        return None


def parse_distances_from_detail_page(soup: BeautifulSoup) -> tuple:
    """
    Парсит дистанции со страницы детального просмотра события

    Args:
        soup: BeautifulSoup объект страницы

    Returns:
        tuple: (distances_list, distances_text) где:
            - distances_list: List[Dict] - список дистанций [{"name": "60 м", "distance": 0.06}, ...]
            - distances_text: str - текстовое описание дистанций сгруппированных по дням
    """
    distances = []
    distances_by_day = []

    try:
        # Стратегия 1: Ищем специфичную структуру для speedrace.runc.run
        # Формат: <p><strong>21 февраля (суббота) </strong>— 60 м, 600 м, 1000 м, смешанная эстафета 4×200 м</p>

        # Ищем параграфы с датами и дистанциями
        paragraphs = soup.find_all('p')

        for p in paragraphs:
            strong = p.find('strong')
            if strong:
                strong_text = strong.get_text(strip=True)
                # Проверяем, содержит ли текст дату и день недели
                if any(day in strong_text.lower() for day in ['суббота', 'воскресенье', 'понедельник', 'вторник', 'среда', 'четверг', 'пятница']):
                    # Получаем полный текст параграфа
                    full_text = p.get_text(strip=True)

                    # Разделяем по тире (—) или дефису (-)
                    parts = re.split(r'[—\-]\s*', full_text, maxsplit=1)

                    if len(parts) == 2:
                        day_part = parts[0].strip()
                        distances_part = parts[1].strip()

                        # Сохраняем информацию о дне и дистанциях
                        distances_by_day.append(f"{day_part} — {distances_part}")

                        # Парсим отдельные дистанции для списка
                        # Ищем паттерны: "60 м", "1 миля", "эстафета 4×200 м"
                        distance_items = re.split(r',\s*', distances_part)

                        for item in distance_items:
                            item = item.strip()

                            # Парсим дистанцию с единицами измерения
                            # ВАЖНО: Более длинные единицы (миля/mile) должны проверяться ПЕРВЫМИ
                            match = re.search(r'(\d+(?:[.,]\d+)?)\s*(миля|mile|км|м)(?!\w)', item, re.IGNORECASE)
                            if match:
                                value_str = match.group(1).replace(',', '.')
                                unit = match.group(2).lower()

                                try:
                                    value = float(value_str)

                                    # Конвертируем в километры
                                    if unit in ['миля', 'mile']:
                                        distance_km = value * 1.60934
                                    elif unit in ['км']:
                                        distance_km = value
                                    elif unit in ['м', 'm']:
                                        distance_km = value / 1000
                                    else:
                                        distance_km = value

                                    distances.append({
                                        "name": item,  # Сохраняем полное название (включая "эстафета")
                                        "distance": distance_km
                                    })
                                except ValueError:
                                    continue
                            else:
                                # Обрабатываем эстафеты с несколькими дистанциями (800-600-400-200 м)
                                relay_match = re.search(r'эстафет', item, re.IGNORECASE)
                                if relay_match:
                                    # Извлекаем все числа из строки эстафеты
                                    numbers = re.findall(r'(\d+)', item)
                                    unit_match = re.search(r'(км|м)(?!\w)', item, re.IGNORECASE)

                                    if numbers and unit_match:
                                        # Берем последнее число как базовую дистанцию для эстафеты
                                        # (обычно это последний этап)
                                        value = float(numbers[-1])
                                        unit = unit_match.group(1).lower()

                                        if unit == 'м':
                                            distance_km = value / 1000
                                        else:
                                            distance_km = value

                                        distances.append({
                                            "name": item,
                                            "distance": distance_km
                                        })

        # Формируем текстовое описание
        if distances_by_day:
            distances_text = "\n".join(distances_by_day)
        else:
            # Стратегия 2: Универсальный парсинг (fallback)
            distance_pattern = re.compile(r'(\d+(?:[.,]\d+)?)\s*(км|м|метр)', re.IGNORECASE)
            potential_elements = soup.find_all(['li', 'div', 'span', 'td', 'a'], string=distance_pattern)

            seen_distances = set()

            for elem in potential_elements:
                text = elem.get_text(strip=True)
                matches = distance_pattern.findall(text)

                for match in matches:
                    distance_value_str, unit = match
                    distance_value_str = distance_value_str.replace(',', '.')

                    try:
                        distance_value = float(distance_value_str)

                        if unit.lower() in ['м', 'метр']:
                            distance_km = distance_value / 1000
                        else:
                            distance_km = distance_value

                        if distance_km >= 1:
                            name = f"{distance_value_str} {unit}"
                        else:
                            name = f"{int(distance_value)} м"

                        if distance_km not in seen_distances:
                            seen_distances.add(distance_km)
                            distances.append({
                                "name": name,
                                "distance": distance_km
                            })

                    except ValueError:
                        continue

            # Сортируем по расстоянию
            distances.sort(key=lambda x: x["distance"])

            # Формируем текст из списка
            distances_text = ", ".join([d["name"] for d in distances]) if distances else "Уточняется"

        logger.info(f"Parsed {len(distances)} distances from detail page")
        logger.info(f"Distances text: {distances_text[:200]}")

        return distances, distances_text

    except Exception as e:
        logger.error(f"Error parsing distances: {e}", exc_info=True)
        return [], "Уточняется"
