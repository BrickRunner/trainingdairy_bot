"""
Модуль для проверки обновлений нормативов ЕВСК на официальных сайтах федераций.
Запускается ежедневно для отслеживания изменений в разрядных таблицах.
"""

import asyncio
import hashlib
import aiohttp
import aiosqlite
import os
from datetime import datetime
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

# Пути к официальным источникам нормативов
SOURCES = {
    'running': {
        'url': 'https://rusathletics.info/sport',
        'name': 'Легкая атлетика (бег)',
        'federation': 'ВФЛА (Всероссийская федерация легкой атлетики)',
        'file_url': 'https://rusathletics.info/wp-content/uploads/2025/01/legkaya_atletika_dejstvuyut_c_26_noyabrya_2024_g_87b8cad5ee.xls'
    },
    'swimming': {
        'url': 'https://www.russwimming.ru/documents/players/evsk/',
        'name': 'Плавание',
        'federation': 'ФВВСР (Всероссийская Федерация плавания)',
        'file_url': 'https://www.russwimming.ru/upload/iblock/454/2p9mhknbbs3fltf01qc1d5lhn5ijb41c/plavanie_dejstvuyut_c_26_noyabrya_2024_g_197d4117d4.xls'
    },
    'cycling': {
        'url': 'https://fvsr.ru/deyatelnost/sportivnaya-podgotovka/normativy-i-trebovaniya/',
        'name': 'Велоспорт',
        'federation': 'ФВСР (Федерация велосипедного спорта России)',
        'file_url': 'https://fvsr.ru/wp-content/uploads/2024/11/velosport_dejstvuyut_c_26_noyabrya_2024_g.xls'
    }
}

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def get_page_hash(url: str) -> Optional[str]:
    """
    Получает хеш содержимого страницы для отслеживания изменений.

    Args:
        url: URL страницы с нормативами

    Returns:
        MD5 хеш содержимого страницы или None при ошибке
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    content = await response.text()
                    # Вычисляем хеш содержимого
                    return hashlib.md5(content.encode('utf-8')).hexdigest()
                else:
                    logger.warning(f"Не удалось загрузить {url}: статус {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка при загрузке {url}: {e}")
        return None


async def init_standards_tracking():
    """
    Инициализирует таблицу для отслеживания версий нормативов.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS standards_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport_type TEXT NOT NULL UNIQUE,
                source_url TEXT NOT NULL,
                last_check_date DATE,
                content_hash TEXT,
                last_update_date DATE,
                version TEXT DEFAULT '2022-2025',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def check_standards_updates() -> Dict[str, bool]:
    """
    Проверяет обновления нормативов на официальных сайтах.

    Returns:
        Словарь {sport_type: has_updates}
    """
    await init_standards_tracking()

    updates = {}

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        for sport_type, source in SOURCES.items():
            logger.info(f"Проверка обновлений для {source['name']}...")

            # Получаем текущий хеш страницы
            current_hash = await get_page_hash(source['url'])
            if not current_hash:
                updates[sport_type] = False
                continue

            # Получаем сохраненный хеш
            async with db.execute(
                "SELECT content_hash, last_check_date FROM standards_tracking WHERE sport_type = ?",
                (sport_type,)
            ) as cursor:
                row = await cursor.fetchone()

            if row:
                saved_hash = row['content_hash']
                has_update = (saved_hash != current_hash)

                # Обновляем информацию о проверке
                await db.execute("""
                    UPDATE standards_tracking
                    SET content_hash = ?,
                        last_check_date = date('now'),
                        last_update_date = CASE WHEN ? THEN date('now') ELSE last_update_date END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE sport_type = ?
                """, (current_hash, has_update, sport_type))

                updates[sport_type] = has_update

                if has_update:
                    logger.warning(f"⚠️ ОБНАРУЖЕНЫ ИЗМЕНЕНИЯ В НОРМАТИВАХ: {source['name']}")
                else:
                    logger.info(f"✓ Нормативы {source['name']} актуальны")
            else:
                # Первая проверка - сохраняем текущее состояние
                await db.execute("""
                    INSERT INTO standards_tracking (sport_type, source_url, content_hash, last_check_date, last_update_date)
                    VALUES (?, ?, ?, date('now'), date('now'))
                """, (sport_type, source['url'], current_hash))

                updates[sport_type] = False
                logger.info(f"✓ Инициализирована отслеживание для {source['name']}")

        await db.commit()

    return updates


async def get_admin_user_ids() -> List[int]:
    """
    Получает список ID администраторов для уведомлений.

    Returns:
        Список user_id администраторов
    """
    # Здесь можно добавить логику получения администраторов из БД
    # Пока возвращаем пустой список
    return []


async def notify_about_updates(bot, updates: Dict[str, bool]):
    """
    Отправляет уведомления администраторам об обновлениях нормативов.

    Args:
        bot: Экземпляр бота
        updates: Словарь с информацией об обновлениях
    """
    if not any(updates.values()):
        return

    admin_ids = await get_admin_user_ids()
    if not admin_ids:
        logger.warning("Нет администраторов для отправки уведомлений об обновлении нормативов")
        return

    # Формируем сообщение
    message = "⚠️ <b>ОБНАРУЖЕНЫ ИЗМЕНЕНИЯ В НОРМАТИВАХ ЕВСК</b>\n\n"

    for sport_type, has_update in updates.items():
        if has_update:
            source = SOURCES[sport_type]
            message += f"📊 <b>{source['name']}</b>\n"
            message += f"🔗 Источник: {source['url']}\n"
            message += f"🏛️ Федерация: {source['federation']}\n\n"

    message += "⚙️ <b>Необходимые действия:</b>\n"
    message += "1. Проверьте изменения на официальных сайтах\n"
    message += "2. Обновите модуль utils/qualifications.py с новыми данными\n"
    message += "3. Запустите миграцию: python migrations/update_qualifications.py\n\n"
    message += f"📅 Дата проверки: {datetime.now().strftime('%d.%m.%Y %H:%M')}"

    # Отправляем уведомления всем администраторам
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, message, parse_mode="HTML")
            logger.info(f"Уведомление об обновлениях отправлено администратору {admin_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления администратору {admin_id}: {e}")


async def daily_standards_check(bot):
    """
    Ежедневная проверка обновлений нормативов.
    Вызывается планировщиком задач.

    Args:
        bot: Экземпляр бота для отправки уведомлений
    """
    logger.info("Запуск ежедневной проверки обновлений нормативов ЕВСК")

    try:
        updates = await check_standards_updates()

        # Если есть обновления, уведомляем администраторов
        if any(updates.values()):
            await notify_about_updates(bot, updates)
            logger.warning("Обнаружены обновления нормативов, отправлены уведомления")
        else:
            logger.info("Нормативы ЕВСК актуальны")

    except Exception as e:
        logger.error(f"Ошибка при проверке обновлений нормативов: {e}")


async def get_standards_info() -> Dict[str, Dict]:
    """
    Получает информацию о текущем состоянии нормативов.

    Returns:
        Словарь с информацией о версиях и датах обновления
    """
    await init_standards_tracking()

    info = {}

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute("SELECT * FROM standards_tracking") as cursor:
            rows = await cursor.fetchall()

            for row in rows:
                sport_type = row['sport_type']
                info[sport_type] = {
                    'name': SOURCES[sport_type]['name'],
                    'version': row['version'],
                    'last_check': row['last_check_date'],
                    'last_update': row['last_update_date'],
                    'source_url': row['source_url']
                }

    return info


if __name__ == "__main__":
    # Тестовый запуск проверки
    async def test():
        print("=" * 60)
        print("ТЕСТ: Проверка обновлений нормативов ЕВСК")
        print("=" * 60)

        updates = await check_standards_updates()

        print("\nРезультаты проверки:")
        for sport_type, has_update in updates.items():
            source = SOURCES[sport_type]
            status = "⚠️ ОБНОВЛЕНЫ" if has_update else "✓ Актуальны"
            print(f"{status} - {source['name']}")

        print("\n" + "=" * 60)
        print("Информация о нормативах:")
        print("=" * 60)

        info = await get_standards_info()
        for sport_type, data in info.items():
            print(f"\n{data['name']}:")
            print(f"  Версия: {data['version']}")
            print(f"  Последняя проверка: {data['last_check']}")
            print(f"  Последнее обновление: {data['last_update']}")
            print(f"  Источник: {data['source_url']}")

    asyncio.run(test())
