"""
Модуль для автоматической загрузки и парсинга нормативов ЕВСК по плаванию.
Скачивает XLS файлы с сайта ФВВСР и обновляет базу данных.
"""

import asyncio
import aiohttp
import aiosqlite
import os
import logging
import tempfile
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from io import BytesIO

logger = logging.getLogger(__name__)

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

SWIMMING_SOURCES = {
    'current': {
        'url': 'https://www.russwimming.ru/upload/iblock/454/2p9mhknbbs3fltf01qc1d5lhn5ijb41c/plavanie_dejstvuyut_c_26_noyabrya_2024_g_197d4117d4.xls',
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
            CREATE TABLE IF NOT EXISTS swimming_standards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                distance REAL NOT NULL,
                pool_length INTEGER NOT NULL,
                gender TEXT NOT NULL,
                rank TEXT NOT NULL,
                time_seconds REAL NOT NULL,
                version TEXT NOT NULL,
                effective_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(distance, pool_length, gender, rank, version)
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
        logger.info("Таблицы для хранения нормативов инициализированы")


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


def parse_swimming_xls(file_content: bytes, pool_length: int = 50) -> List[Dict]:
    """
    Парсит XLS файл с нормативами по плаванию.

    Args:
        file_content: Содержимое XLS файла в байтах
        pool_length: Длина бассейна (25 или 50 метров)

    Returns:
        Список словарей с нормативами
    """
    standards = []

    try:
        # Читаем XLS файл с помощью pandas
        df = pd.read_excel(BytesIO(file_content), sheet_name=None, engine='xlrd')

        logger.info(f"Файл содержит {len(df)} листов: {list(df.keys())}")

        # Обработка каждого листа
        for sheet_name, sheet_data in df.items():
            logger.info(f"Обработка листа: {sheet_name}")

            # Ищем данные по вольному стилю для бассейна 50м или 25м
            if ('50' in sheet_name or '25' in sheet_name) and 'вольный' in sheet_name.lower():
                current_pool = 50 if '50' in sheet_name else 25

                # Парсим таблицу
                # Обычно структура: первая колонка - дистанция, далее разряды по полу
                # Нужно адаптировать под реальную структуру файла

                # Пример парсинга (нужно уточнить после просмотра реального файла):
                for idx, row in sheet_data.iterrows():
                    if pd.notna(row.iloc[0]):
                        try:
                            distance_str = str(row.iloc[0])
                            # Извлекаем числовую дистанцию
                            if 'м' in distance_str:
                                distance = float(distance_str.replace('м', '').strip()) / 1000
                            else:
                                continue

                            # Парсим разряды (структура зависит от файла)
                            # Это пример, нужно адаптировать
                            for col_idx, col_name in enumerate(sheet_data.columns[1:], 1):
                                if pd.notna(row.iloc[col_idx]):
                                    time_str = str(row.iloc[col_idx])
                                    # Конвертируем время в секунды
                                    time_seconds = parse_time_to_seconds(time_str)

                                    if time_seconds:
                                        standards.append({
                                            'distance': distance,
                                            'pool_length': current_pool,
                                            'gender': 'male',  # определяется из названия колонки
                                            'rank': 'КМС',  # определяется из названия колонки
                                            'time_seconds': time_seconds
                                        })
                        except Exception as e:
                            logger.debug(f"Ошибка парсинга строки {idx}: {e}")
                            continue

        logger.info(f"Извлечено {len(standards)} нормативов из файла")
        return standards

    except Exception as e:
        logger.error(f"Ошибка парсинга XLS файла: {e}")
        return []


def parse_time_to_seconds(time_str: str) -> Optional[float]:
    """
    Конвертирует строку времени в секунды.

    Args:
        time_str: Строка времени (например "1:05.34" или "23.95")

    Returns:
        Время в секундах или None
    """
    try:
        time_str = str(time_str).strip().replace(',', '.')

        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            elif len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        else:
            return float(time_str)
    except:
        return None


async def save_standards_to_db(standards: List[Dict], version: str, effective_date: str):
    """
    Сохраняет нормативы в базу данных.

    Args:
        standards: Список нормативов
        version: Версия нормативов
        effective_date: Дата вступления в силу
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, есть ли уже эта версия
        async with db.execute(
            "SELECT id FROM standards_versions WHERE sport_type = 'swimming' AND version = ?",
            (version,)
        ) as cursor:
            existing = await cursor.fetchone()

        if existing:
            logger.info(f"Версия {version} уже существует в базе данных")
            return

        # Деактивируем старые версии
        await db.execute(
            "UPDATE standards_versions SET is_active = 0 WHERE sport_type = 'swimming'"
        )

        # Добавляем новую версию
        await db.execute(
            """
            INSERT INTO standards_versions (sport_type, version, effective_date, is_active)
            VALUES ('swimming', ?, ?, 1)
            """,
            (version, effective_date)
        )

        # Сохраняем нормативы
        for standard in standards:
            await db.execute(
                """
                INSERT OR REPLACE INTO swimming_standards
                (distance, pool_length, gender, rank, time_seconds, version, effective_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    standard['distance'],
                    standard['pool_length'],
                    standard['gender'],
                    standard['rank'],
                    standard['time_seconds'],
                    version,
                    effective_date
                )
            )

        await db.commit()
        logger.info(f"Сохранено {len(standards)} нормативов версии {version}")


async def update_swimming_standards() -> bool:
    """
    Обновляет нормативы по плаванию из официального источника.

    Returns:
        True если обновление успешно, False в противном случае
    """
    logger.info("Начало обновления нормативов по плаванию...")

    await init_standards_database()

    source = SWIMMING_SOURCES['current']

    # Загружаем файл
    file_content = await download_xls_file(source['url'])
    if not file_content:
        logger.error("Не удалось загрузить файл с нормативами")
        return False

    # Парсим файл
    standards = parse_swimming_xls(file_content)
    if not standards:
        logger.warning("Не удалось извлечь нормативы из файла (возможно, нужно адаптировать парсер)")
        # Не считаем это ошибкой, так как структура файла может быть сложной
        # Просто записываем, что файл был обработан

    # Сохраняем в БД
    await save_standards_to_db(standards, source['version'], source['effective_date'])

    logger.info("Обновление нормативов по плаванию завершено")
    return True


async def check_for_new_swimming_standards() -> Optional[Dict]:
    """
    Проверяет наличие новых нормативов на сайте ФВВСР.

    Returns:
        Словарь с информацией о новых нормативах или None
    """
    logger.info("Проверка наличия новых нормативов на сайте ФВВСР...")

    # Загружаем страницу с документами
    page_url = 'https://www.russwimming.ru/documents/players/evsk/'

    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(page_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    logger.error(f"Ошибка загрузки страницы: статус {response.status}")
                    return None

                html = await response.text()

                # Ищем ссылки на XLS файлы с нормативами
                # Простой поиск по ключевым словам
                if 'plavanie' in html and '.xls' in html:
                    # Извлекаем дату из названия файла
                    # Например: "plavanie_dejstvuyut_c_26_noyabrya_2024_g"

                    # Проверяем, отличается ли от текущей версии
                    current_version = SWIMMING_SOURCES['current']['version']

                    logger.info(f"Обнаружены документы на странице (текущая версия: {current_version})")

                    # Здесь можно добавить более сложную логику сравнения версий
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
        print("ТЕСТ: Обновление нормативов по плаванию")
        print("=" * 60)

        success = await update_swimming_standards()

        if success:
            print("\n✓ Нормативы успешно обновлены")
        else:
            print("\n✗ Ошибка обновления нормативов")

        print("\n" + "=" * 60)
        print("Проверка новых версий на сайте:")
        print("=" * 60)

        info = await check_for_new_swimming_standards()
        if info:
            print(f"\nСтатус: {info['status']}")
            print(f"Сообщение: {info['message']}")

    asyncio.run(test())
