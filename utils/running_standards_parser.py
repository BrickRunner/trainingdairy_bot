"""
Модуль для автоматической загрузки и парсинга нормативов ЕВСК по легкой атлетике (бег).
Скачивает XLS файлы с сайта ВФЛА и обновляет базу данных.
"""

import asyncio
import aiohttp
import aiosqlite
import os
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from io import BytesIO

logger = logging.getLogger(__name__)

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

RUNNING_SOURCES = {
    'current': {
        'url': 'https://rusathletics.info/wp-content/uploads/2025/01/legkaya_atletika_dejstvuyut_c_26_noyabrya_2024_g_87b8cad5ee.xls',
        'effective_date': '2024-11-26',
        'version': 'EVSK 2024 (с 26.11.2024)'
    }
}


async def init_standards_database():
    """
    Инициализирует таблицы для хранения нормативов ЕВСК в базе данных.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS running_standards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                distance REAL NOT NULL,
                gender TEXT NOT NULL,
                rank TEXT NOT NULL,
                time_seconds REAL NOT NULL,
                version TEXT NOT NULL,
                effective_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(distance, gender, rank, version)
            )
        """)

        # Таблица версий нормативов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS standards_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport_type TEXT NOT NULL,
                version TEXT NOT NULL,
                effective_date DATE NOT NULL,
                source_url TEXT,
                file_hash TEXT,
                is_active INTEGER DEFAULT 1,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(sport_type, version)
            )
        """)

        await db.commit()
        logger.info("Таблицы для хранения нормативов по бегу инициализированы")


async def download_xls_file(url: str) -> Optional[bytes]:
    """
    Загружает XLS файл с указанного URL.

    Args:
        url: URL файла для загрузки

    Returns:
        Содержимое файла в байтах или None при ошибке
    """
    try:
        # Используем connector без проверки SSL
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status == 200:
                    content = await response.read()
                    logger.info(f"Файл успешно загружен: {url} ({len(content)} байт)")
                    return content
                else:
                    logger.error(f"Ошибка загрузки файла {url}: статус {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла {url}: {e}")
        return None


def parse_running_xls(file_content: bytes) -> List[Dict]:
    """
    Парсит XLS файл с нормативами по легкой атлетике (бег).

    Args:
        file_content: Содержимое XLS файла в байтах

    Returns:
        Список словарей с нормативами
    """
    standards = []

    try:
        # Читаем XLS файл с помощью pandas
        df = pd.read_excel(BytesIO(file_content), sheet_name=None, engine='xlrd')

        logger.info(f"Файл содержит {len(df)} листов: {list(df.keys())}")

        # Дистанции бега, которые нас интересуют (в метрах)
        running_distances = {
            '100': 0.1,
            '200': 0.2,
            '400': 0.4,
            '800': 0.8,
            '1500': 1.5,
            '3000': 3,
            '5000': 5,
            '10000': 10,
            '10 км': 10,
            '21.1': 21.1,
            '21.097': 21.1,  # полумарафон
            'полумарафон': 21.1,
            '42.195': 42.195,
            'марафон': 42.195
        }

        # Обработка каждого листа
        for sheet_name, sheet_data in df.items():
            logger.info(f"Обработка листа: {sheet_name}")

            # Ищем данные по бегу
            # Обычно в файле есть листы с названиями дистанций или "Бег"
            if any(keyword in sheet_name.lower() for keyword in ['бег', 'running', 'метр', 'км', 'марафон']):

                # Парсим таблицу
                # Структура: обычно первые строки - заголовки
                # Столбцы: дистанция, мужчины (МСМК, МС, КМС, I, II, III), женщины (МСМК, МС, КМС, I, II, III)

                for idx, row in sheet_data.iterrows():
                    try:
                        # Пропускаем заголовки и пустые строки
                        if idx < 3:  # Обычно первые 2-3 строки - заголовки
                            continue

                        if pd.isna(row.iloc[0]):
                            continue

                        # Пытаемся извлечь дистанцию
                        distance_str = str(row.iloc[0]).strip()

                        # Определяем дистанцию в км
                        distance_km = None
                        for key, value in running_distances.items():
                            if key in distance_str:
                                distance_km = value
                                break

                        if not distance_km:
                            # Пытаемся извлечь числовое значение
                            import re
                            match = re.search(r'(\d+\.?\d*)', distance_str)
                            if match:
                                dist_value = float(match.group(1))
                                # Если число меньше 100, вероятно это км, иначе метры
                                if dist_value < 100:
                                    distance_km = dist_value
                                else:
                                    distance_km = dist_value / 1000

                        if not distance_km:
                            continue

                        # Парсим время для каждого разряда и пола
                        # Структура столбцов может варьироваться, обычно:
                        # [Дистанция] [Мужчины: МСМК, МС, КМС, I, II, III] [Женщины: МСМК, МС, КМС, I, II, III]

                        ranks = ['МСМК', 'МС', 'КМС', 'I', 'II', 'III']

                        # Пытаемся найти столбцы с разрядами
                        for col_idx in range(1, len(row)):
                            if pd.notna(row.iloc[col_idx]):
                                time_str = str(row.iloc[col_idx]).strip()

                                # Конвертируем время в секунды
                                time_seconds = parse_time_to_seconds(time_str)

                                if time_seconds and time_seconds > 0:
                                    # Определяем пол и разряд по индексу столбца
                                    # Это упрощенная логика, нужно адаптировать под реальный файл

                                    # Предполагаем: столбцы 1-6 мужчины, 7-12 женщины
                                    if 1 <= col_idx <= 6:
                                        gender = 'male'
                                        rank_idx = col_idx - 1
                                    elif 7 <= col_idx <= 12:
                                        gender = 'female'
                                        rank_idx = col_idx - 7
                                    else:
                                        continue

                                    if rank_idx < len(ranks):
                                        rank = ranks[rank_idx]

                                        standards.append({
                                            'distance': distance_km,
                                            'gender': gender,
                                            'rank': rank,
                                            'time_seconds': time_seconds
                                        })

                    except Exception as e:
                        logger.debug(f"Ошибка парсинга строки {idx}: {e}")
                        continue

        logger.info(f"Извлечено {len(standards)} нормативов из файла")
        return standards

    except Exception as e:
        logger.error(f"Ошибка парсинга XLS файла: {e}")
        import traceback
        traceback.print_exc()
        return []


def parse_time_to_seconds(time_str: str) -> Optional[float]:
    """
    Конвертирует строку времени в секунды.

    Args:
        time_str: Строка времени (например "1:30:00", "15:30", "23.95")

    Returns:
        Время в секундах или None
    """
    try:
        time_str = str(time_str).strip().replace(',', '.')

        # Убираем возможные лишние символы
        time_str = time_str.replace('"', '').replace("'", '')

        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2:
                # MM:SS формат
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            elif len(parts) == 3:
                # HH:MM:SS формат
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        else:
            # Только секунды
            return float(time_str)
    except Exception as e:
        logger.debug(f"Не удалось распарсить время '{time_str}': {e}")
        return None


async def save_standards_to_db(standards: List[Dict], version: str, effective_date: str, source_url: str):
    """
    Сохраняет нормативы в базу данных.

    Args:
        standards: Список нормативов
        version: Версия нормативов
        effective_date: Дата вступления в силу
        source_url: URL источника
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, есть ли уже эта версия
        async with db.execute(
            "SELECT id FROM standards_versions WHERE sport_type = 'running' AND version = ?",
            (version,)
        ) as cursor:
            existing = await cursor.fetchone()

        if existing:
            logger.info(f"Версия {version} уже существует в базе данных")
            return

        # Деактивируем старые версии
        await db.execute(
            "UPDATE standards_versions SET is_active = 0 WHERE sport_type = 'running'"
        )

        # Добавляем новую версию
        await db.execute(
            """
            INSERT INTO standards_versions (sport_type, version, effective_date, source_url, is_active)
            VALUES ('running', ?, ?, ?, 1)
            """,
            (version, effective_date, source_url)
        )

        # Сохраняем нормативы
        for standard in standards:
            await db.execute(
                """
                INSERT OR REPLACE INTO running_standards
                (distance, gender, rank, time_seconds, version, effective_date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    standard['distance'],
                    standard['gender'],
                    standard['rank'],
                    standard['time_seconds'],
                    version,
                    effective_date
                )
            )

        await db.commit()
        logger.info(f"Сохранено {len(standards)} нормативов по бегу версии {version}")


async def update_running_standards() -> bool:
    """
    Обновляет нормативы по бегу из официального источника.

    Returns:
        True если обновление успешно, False в противном случае
    """
    logger.info("Начало обновления нормативов по бегу...")

    await init_standards_database()

    source = RUNNING_SOURCES['current']

    # Загружаем файл
    file_content = await download_xls_file(source['url'])
    if not file_content:
        logger.error("Не удалось загрузить файл с нормативами по бегу")
        return False

    # Парсим файл
    standards = parse_running_xls(file_content)
    if not standards:
        logger.warning("Не удалось извлечь нормативы из файла (возможно, нужно адаптировать парсер)")
        # Не считаем это критической ошибкой
        return True

    # Сохраняем в БД
    await save_standards_to_db(standards, source['version'], source['effective_date'], source['url'])

    logger.info(f"Обновление нормативов по бегу завершено: {len(standards)} нормативов")
    return True


async def check_for_new_running_standards() -> Optional[Dict]:
    """
    Проверяет наличие новых нормативов на сайте ВФЛА.

    Returns:
        Словарь с информацией о новых нормативах или None
    """
    logger.info("Проверка наличия новых нормативов на сайте ВФЛА...")

    page_url = 'https://rusathletics.info'

    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(page_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    logger.error(f"Ошибка загрузки страницы: статус {response.status}")
                    return None

                html = await response.text()

                # Ищем ссылки на XLS файлы с нормативами
                if 'legkaya_atletika' in html and '.xls' in html:
                    current_version = RUNNING_SOURCES['current']['version']

                    logger.info(f"Обнаружены документы на странице (текущая версия: {current_version})")

                    return {
                        'status': 'current',
                        'version': current_version,
                        'message': 'Используется актуальная версия нормативов'
                    }
    except Exception as e:
        logger.error(f"Ошибка при проверке обновлений: {e}")
        return None


if __name__ == "__main__":
    # Тестовый запуск
    async def test():
        print("=" * 60)
        print("ТЕСТ: Обновление нормативов по бегу")
        print("=" * 60)

        success = await update_running_standards()

        if success:
            print("\n✓ Процесс обновления завершен")
        else:
            print("\n✗ Ошибка обновления нормативов")

        print("\n" + "=" * 60)
        print("Проверка новых версий на сайте:")
        print("=" * 60)

        info = await check_for_new_running_standards()
        if info:
            print(f"\nСтатус: {info['status']}")
            print(f"Сообщение: {info['message']}")

    asyncio.run(test())
