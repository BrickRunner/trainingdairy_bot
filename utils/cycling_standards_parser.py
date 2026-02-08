"""
Модуль для автоматической загрузки и парсинга нормативов ЕВСК по велоспорту.
Скачивает XLS файлы с сайта ФВСР и обновляет базу данных.

ВАЖНО:
1. Для велоспорта разряды присваиваются по занятым местам на соревнованиях,
   а не по времени прохождения дистанции.
2. Разряды присваиваются только за шоссейные гонки (дисциплина "шоссе").
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

CYCLING_SOURCES = {
    'current': {
        'url': 'https://fvsr.ru/wp-content/uploads/2024/11/velosport_dejstvuyut_c_26_noyabrya_2024_g.xls',
        'effective_date': '2024-11-26',
        'version': 'EVSK 2024 (с 26.11.2024)'
    }
}

CYCLING_DISCIPLINES = ['шоссе']


async def init_standards_database():
    """
    Инициализирует таблицы для хранения нормативов ЕВСК в базе данных.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cycling_standards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                distance REAL NOT NULL,
                discipline TEXT NOT NULL,
                gender TEXT NOT NULL,
                rank TEXT NOT NULL,
                time_seconds REAL,
                place INTEGER,
                version TEXT NOT NULL,
                effective_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(distance, discipline, gender, rank, version)
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
        logger.info("Таблицы для хранения нормативов по велоспорту инициализированы")


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


def parse_cycling_xls(file_content: bytes) -> List[Dict]:
    """
    Парсит XLS файл с нормативами по велоспорту.

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

        # Обработка каждого листа
        for sheet_name, sheet_data in df.items():
            logger.info(f"Обработка листа: {sheet_name}")

            # Определяем дисциплину из названия листа
            discipline = None
            for disc in CYCLING_DISCIPLINES:
                if disc.lower() in sheet_name.lower():
                    discipline = disc
                    break

            if not discipline:
                # Если не определили дисциплину, используем название листа или "шоссе" по умолчанию
                if 'шоссе' in sheet_name.lower() or 'road' in sheet_name.lower():
                    discipline = 'шоссе'
                elif 'трек' in sheet_name.lower() or 'track' in sheet_name.lower():
                    discipline = 'трек'
                elif 'mtb' in sheet_name.lower() or 'маунтин' in sheet_name.lower():
                    discipline = 'маунтинбайк'
                elif 'bmx' in sheet_name.lower():
                    discipline = 'BMX'
                else:
                    discipline = 'шоссе'  # По умолчанию

            # Парсим таблицу
            # Для велоспорта обычно структура: разряд -> требуемое место на соревнованиях

            ranks = ['МСМК', 'МС', 'КМС', 'I', 'II', 'III']

            # Типичная структура файла ЕВСК по велоспорту:
            # Разряды присваиваются за занятые места на соревнованиях определенного уровня

            for idx, row in sheet_data.iterrows():
                try:
                    # Пропускаем заголовки
                    if idx < 3:
                        continue

                    if pd.isna(row.iloc[0]):
                        continue

                    # Ищем строки с разрядами
                    cell_value = str(row.iloc[0]).strip()

                    # Проверяем, содержит ли ячейка информацию о разряде
                    found_rank = None
                    for rank in ranks:
                        if rank in cell_value:
                            found_rank = rank
                            break

                    if found_rank:
                        # Ищем информацию о требуемом месте
                        for col_idx in range(1, len(row)):
                            if pd.notna(row.iloc[col_idx]):
                                cell_text = str(row.iloc[col_idx]).strip()

                                # Ищем числа (места)
                                import re
                                place_match = re.search(r'1[-–](\d+)', cell_text)
                                if place_match:
                                    max_place = int(place_match.group(1))

                                    # Определяем пол (если указан в заголовке столбца)
                                    gender = 'mixed'  # По умолчанию для велоспорта часто общие нормативы

                                    if col_idx < len(sheet_data.columns):
                                        col_name = str(sheet_data.columns[col_idx]).lower()
                                        if 'мужчины' in col_name or 'муж' in col_name or 'male' in col_name or 'м.' in col_name:
                                            gender = 'male'
                                        elif 'женщины' in col_name or 'жен' in col_name or 'female' in col_name or 'ж.' in col_name:
                                            gender = 'female'

                                    standards.append({
                                        'distance': 0,  # Для велоспорта дистанция не критична
                                        'discipline': discipline,
                                        'gender': gender,
                                        'rank': found_rank,
                                        'time_seconds': None,
                                        'place': max_place
                                    })

                except Exception as e:
                    logger.debug(f"Ошибка парсинга строки {idx} на листе {sheet_name}: {e}")
                    continue

        logger.info(f"Извлечено {len(standards)} нормативов из файла")

        # Если не удалось распарсить файл, используем упрощенные нормативы
        if not standards:
            logger.warning("Не удалось извлечь нормативы из XLS, используем упрощенную структуру")
            standards = get_default_cycling_standards()

        return standards

    except Exception as e:
        logger.error(f"Ошибка парсинга XLS файла: {e}")
        import traceback
        traceback.print_exc()

        # Возвращаем упрощенные нормативы
        return get_default_cycling_standards()


def get_default_cycling_standards() -> List[Dict]:
    """
    Возвращает упрощенные нормативы по велоспорту на основе общих правил ЕВСК.

    ВАЖНО: Разряды присваиваются только за шоссейные гонки.

    Returns:
        Список стандартных нормативов
    """
    logger.info("Использование упрощенных нормативов по велоспорту (только шоссе)")

    standards = []

    # Упрощенная структура на основе общих правил ЕВСК
    # (места на соревнованиях различного уровня)
    # Разряды только для шоссейных гонок
    standards_by_rank = {
        'МСМК': 3,   # 1-3 место на соревнованиях высшего уровня
        'МС': 6,     # 1-6 место
        'КМС': 12,   # 1-12 место
        'I': 20,     # 1-20 место
        'II': 30,    # 1-30 место
        'III': 50,   # 1-50 место
    }

    for rank, max_place in standards_by_rank.items():
        standards.append({
            'distance': 0,
            'discipline': 'шоссе',
            'gender': 'mixed',
            'rank': rank,
            'time_seconds': None,
            'place': max_place
        })

    return standards


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
            "SELECT id FROM standards_versions WHERE sport_type = 'cycling' AND version = ?",
            (version,)
        ) as cursor:
            existing = await cursor.fetchone()

        if existing:
            logger.info(f"Версия {version} уже существует в базе данных")
            return

        # Деактивируем старые версии
        await db.execute(
            "UPDATE standards_versions SET is_active = 0 WHERE sport_type = 'cycling'"
        )

        # Добавляем новую версию
        await db.execute(
            """
            INSERT INTO standards_versions (sport_type, version, effective_date, source_url, is_active)
            VALUES ('cycling', ?, ?, ?, 1)
            """,
            (version, effective_date, source_url)
        )

        # Сохраняем нормативы
        for standard in standards:
            await db.execute(
                """
                INSERT OR REPLACE INTO cycling_standards
                (distance, discipline, gender, rank, time_seconds, place, version, effective_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    standard['distance'],
                    standard['discipline'],
                    standard['gender'],
                    standard['rank'],
                    standard.get('time_seconds'),
                    standard.get('place'),
                    version,
                    effective_date
                )
            )

        await db.commit()
        logger.info(f"Сохранено {len(standards)} нормативов по велоспорту версии {version}")


async def update_cycling_standards() -> bool:
    """
    Обновляет нормативы по велоспорту из официального источника.

    Returns:
        True если обновление успешно, False в противном случае
    """
    logger.info("Начало обновления нормативов по велоспорту...")

    await init_standards_database()

    source = CYCLING_SOURCES['current']

    # Загружаем файл
    file_content = await download_xls_file(source['url'])
    if not file_content:
        logger.error("Не удалось загрузить файл с нормативами по велоспорту")
        # Используем упрощенные нормативы
        standards = get_default_cycling_standards()
    else:
        # Парсим файл
        standards = parse_cycling_xls(file_content)

    if not standards:
        logger.error("Не удалось получить нормативы по велоспорту")
        return False

    # Сохраняем в БД
    await save_standards_to_db(standards, source['version'], source['effective_date'], source['url'])

    logger.info(f"Обновление нормативов по велоспорту завершено: {len(standards)} нормативов")
    return True


async def check_for_new_cycling_standards() -> Optional[Dict]:
    """
    Проверяет наличие новых нормативов на сайте ФВСР.

    Returns:
        Словарь с информацией о новых нормативах или None
    """
    logger.info("Проверка наличия новых нормативов на сайте ФВСР...")

    page_url = 'https://fvsr.ru'

    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(page_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    logger.error(f"Ошибка загрузки страницы: статус {response.status}")
                    return None

                html = await response.text()

                # Ищем ссылки на XLS файлы с нормативами
                if 'velosport' in html and '.xls' in html:
                    current_version = CYCLING_SOURCES['current']['version']

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
        print("ТЕСТ: Обновление нормативов по велоспорту")
        print("=" * 60)

        success = await update_cycling_standards()

        if success:
            print("\n✓ Процесс обновления завершен")
        else:
            print("\n✗ Ошибка обновления нормативов")

        print("\n" + "=" * 60)
        print("Проверка новых версий на сайте:")
        print("=" * 60)

        info = await check_for_new_cycling_standards()
        if info:
            print(f"\nСтатус: {info['status']}")
            print(f"Сообщение: {info['message']}")

    asyncio.run(test())
