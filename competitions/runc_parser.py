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
    normalized_code = normalize_sport_code(event_name, distances)

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

                event_items = soup.find_all('div', class_='header-menu-sub-menu-race-item')
                logger.info(f"Found {len(event_items)} event items on RunC")

                competitions = []
                processed_urls = set()  

                for item in event_items:
                    link = item.find('a', class_='header-menu-sub-menu-race-item__race-name')

                    if not link or 'results.runc.run' in link.get('href', ''):
                        continue

                    event_url = link.get('href', '')

                    if event_url in processed_urls:
                        continue

                    processed_urls.add(event_url)

                    comp = parse_competition_from_menu_item(item)

                    if not comp:
                        continue

                    if city and city.lower() not in comp.get("city", "").lower():
                        continue

                    event_name = comp.get("title", "")
                    distances_text = comp.get("distances_text", "")
                    if not matches_sport_type(event_name, distances_text, sport):
                        continue

                    try:
                        logger.info(f"Fetching details for: {comp.get('title')}")
                        detailed_comp = await get_competition_details(
                            comp.get('url'),
                            begin_date=comp.get('begin_date'),
                            end_date=comp.get('end_date')
                        )
                        if detailed_comp:
                            comp = detailed_comp
                    except Exception as e:
                        logger.warning(f"Could not fetch details for {comp.get('title')}: {e}")

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

                                if period_months == 1:
                                    from datetime import timedelta
                                    start_date = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
                                    if month == 12:
                                        end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
                                    else:
                                        next_month_first = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=timezone.utc)
                                        end_date = next_month_first - timedelta(seconds=1)

                                elif period_months == 12:
                                    start_date = datetime(year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
                                    end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

                                else:
                                    from datetime import timedelta
                                    start_date = now
                                    end_date = now + timedelta(days=180)

                                if begin_date < start_date or begin_date > end_date:
                                    continue

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
        date_elem = item.find('div', class_='header-menu-sub-menu-race-item__date')
        date_str = date_elem.get_text(strip=True) if date_elem else ""

        link = item.find('a', class_='header-menu-sub-menu-race-item__race-name')
        if not link:
            return None

        title = link.get_text(strip=True)
        url = link.get('href', '')

        if url.startswith('/'):
            url = f"{BASE_URL}{url}"

        if date_str:
            begin_date, end_date = parse_russian_date_short(date_str)
        else:
            now_iso = datetime.now(timezone.utc).isoformat()
            begin_date, end_date = now_iso, now_iso

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

        event_id = url.replace('https://', '').replace('http://', '').replace('/', '_').replace('.', '_')

        city = "Москва"

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
            "end_date": end_date,  
            "formatted_date": date_str if date_str else "Дата уточняется",
            "description": title,
            "distances_text": "Уточняется на сайте",  
            "url": url,
            "distances": [],  
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
        months_map = {
            "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
            "мая": 5, "июня": 6, "июля": 7, "августа": 8,
            "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12
        }

        pattern_range = r'(\d{1,2})-(\d{1,2})\s+(\w+)'
        pattern_single = r'(\d{1,2})\s+(\w+)'

        match_range = re.search(pattern_range, date_str)
        if match_range:
            start_day = int(match_range.group(1))
            end_day = int(match_range.group(2))
            month_name = match_range.group(3).lower()

            month = months_map.get(month_name)
            if month:
                now = datetime.now(timezone.utc)
                year = now.year

                if month < now.month:
                    year += 1
                elif month == now.month and start_day < now.day:
                    year += 1

                begin_date = datetime(year, month, start_day, 0, 0, 0, tzinfo=timezone.utc)
                end_date = datetime(year, month, end_day, 0, 0, 0, tzinfo=timezone.utc)

                return (begin_date.isoformat(), end_date.isoformat())

        match_single = re.search(pattern_single, date_str)
        if match_single:
            day = int(match_single.group(1))
            month_name = match_single.group(2).lower()

            month = months_map.get(month_name)
            if month:
                now = datetime.now(timezone.utc)
                year = now.year

                if month < now.month:
                    year += 1
                elif month == now.month and day < now.day:
                    year += 1

                date_obj = datetime(year, month, day, 0, 0, 0, tzinfo=timezone.utc)
                return (date_obj.isoformat(), date_obj.isoformat())

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
        text_content = link.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text_content.split("\n") if line.strip()]

        if len(lines) < 3:
            logger.debug(f"Not enough data in link for event {event_id}")
            return None


        title = ""
        city = "Москва"  
        distances_text = ""
        date_str = ""

        for line in lines:
            if '"' in line or "«" in line or "»" in line:
                title = line
                break
            if any(word in line.lower() for word in ["соревнован", "кросс", "марафон", "забег", "эстафет"]):
                title = line
                break

        if not title and lines:
            title = lines[0]

        for line in lines:
            if any(unit in line.lower() for unit in [" км", " м", "метр", "от ", "до "]):
                if not any(skip in line.lower() for skip in ["соревнован", "кросс", "марафон"]):
                    distances_text = line
                    break

        for line in lines:
            if any(city_name in line for city_name in ["Москва", "Санкт-Петербург", "Казань", "Екатеринбург", "Новосибирск"]):
                city = line
                break

        months_ru = ["января", "февраля", "марта", "апреля", "мая", "июня",
                     "июля", "августа", "сентября", "октября", "ноября", "декабря"]
        for line in lines:
            if any(month in line.lower() for month in months_ru):
                date_str = line
                break

        begin_date = parse_russian_date(date_str) if date_str else datetime.now(timezone.utc).isoformat()
        formatted_date = date_str if date_str else "Дата уточняется"

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
            "distances": [],  
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
        months_map = {
            "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
            "мая": 5, "июня": 6, "июля": 7, "августа": 8,
            "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12
        }

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

                title_elem = soup.find('h1') or soup.find('h2', class_=re.compile('title|name|event'))
                title = title_elem.get_text(strip=True) if title_elem else "Без названия"

                distances, distances_text = parse_distances_from_detail_page(soup)

                if not begin_date or not end_date:
                    date_elem = soup.find(text=re.compile(r'\d{1,2}\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{4}'))
                    date_str = date_elem.strip() if date_elem else ""
                    if date_str:
                        begin_date = parse_russian_date(date_str)
                        end_date = begin_date  
                    else:
                        now_iso = datetime.now(timezone.utc).isoformat()
                        begin_date = now_iso
                        end_date = now_iso

                date_str = ""
                if begin_date and end_date:
                    try:
                        begin_dt = datetime.fromisoformat(begin_date.replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

                        months_ru = ["", "января", "февраля", "марта", "апреля", "мая", "июня",
                                    "июля", "августа", "сентября", "октября", "ноября", "декабря"]

                        if begin_dt.date() == end_dt.date():
                            date_str = f"{begin_dt.day} {months_ru[begin_dt.month]} {begin_dt.year}"
                        else:
                            if begin_dt.month == end_dt.month:
                                date_str = f"{begin_dt.day}-{end_dt.day} {months_ru[begin_dt.month]} {begin_dt.year}"
                            else:
                                date_str = f"{begin_dt.day} {months_ru[begin_dt.month]} - {end_dt.day} {months_ru[end_dt.month]} {begin_dt.year}"
                    except:
                        date_str = "Дата уточняется"

                city = "Москва"  
                city_elem = soup.find(text=re.compile(r'(Москва|Санкт-Петербург|Казань|Екатеринбург|Новосибирск)'))
                if city_elem:
                    city = city_elem.strip()

                sport_code = normalize_sport_code(title, distances_text)

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

        paragraphs = soup.find_all('p')

        for p in paragraphs:
            strong = p.find('strong')
            if strong:
                strong_text = strong.get_text(strip=True)
                if any(day in strong_text.lower() for day in ['суббота', 'воскресенье', 'понедельник', 'вторник', 'среда', 'четверг', 'пятница']):
                    full_text = p.get_text(strip=True)

                    parts = re.split(r'[—\-]\s*', full_text, maxsplit=1)

                    if len(parts) == 2:
                        day_part = parts[0].strip()
                        distances_part = parts[1].strip()

                        distances_by_day.append(f"{day_part} — {distances_part}")

                        distance_items = re.split(r',\s*', distances_part)

                        for item in distance_items:
                            item = item.strip()

                            match = re.search(r'(\d+(?:[.,]\d+)?)\s*(миля|mile|км|м)(?!\w)', item, re.IGNORECASE)
                            if match:
                                value_str = match.group(1).replace(',', '.')
                                unit = match.group(2).lower()

                                try:
                                    value = float(value_str)

                                    if unit in ['миля', 'mile']:
                                        distance_km = value * 1.60934
                                    elif unit in ['км']:
                                        distance_km = value
                                    elif unit in ['м', 'm']:
                                        distance_km = value / 1000
                                    else:
                                        distance_km = value

                                    distances.append({
                                        "name": item,  
                                        "distance": distance_km
                                    })
                                except ValueError:
                                    continue
                            else:
                                relay_match = re.search(r'эстафет', item, re.IGNORECASE)
                                if relay_match:
                                    numbers = re.findall(r'(\d+)', item)
                                    unit_match = re.search(r'(км|м)(?!\w)', item, re.IGNORECASE)

                                    if numbers and unit_match:
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

        if distances_by_day:
            distances_text = "\n".join(distances_by_day)
        else:
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

            distances.sort(key=lambda x: x["distance"])

            distances_text = ", ".join([d["name"] for d in distances]) if distances else "Уточняется"

        logger.info(f"Parsed {len(distances)} distances from detail page")
        logger.info(f"Distances text: {distances_text[:200]}")

        return distances, distances_text

    except Exception as e:
        logger.error(f"Error parsing distances: {e}", exc_info=True)
        return [], "Уточняется"
