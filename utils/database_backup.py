"""
Модуль для автоматического резервного копирования базы данных

Защита от потери данных через:
1. Периодические backup'ы (каждые 24 часа)
2. Автоматическая очистка старых backup'ов
3. Проверка целостности резервных копий
"""

import os
import shutil
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Конфигурация
DB_PATH = os.getenv('DB_PATH', 'database.sqlite')
BACKUP_DIR = os.getenv('BACKUP_DIR', 'backups')
BACKUP_KEEP_DAYS = int(os.getenv('BACKUP_KEEP_DAYS', '7'))  # Храним последние 7 дней
BACKUP_INTERVAL_HOURS = int(os.getenv('BACKUP_INTERVAL_HOURS', '24'))  # Backup каждые 24 часа


async def create_backup() -> Optional[str]:
    """
    Создать резервную копию базы данных

    Returns:
        Путь к созданному backup'у или None в случае ошибки
    """
    try:
        # Создаем директорию для backup'ов если не существует
        backup_path = Path(BACKUP_DIR)
        backup_path.mkdir(parents=True, exist_ok=True)

        # Проверяем что исходная БД существует
        db_file = Path(DB_PATH)
        if not db_file.exists():
            logger.warning(f"Database file not found: {DB_PATH}")
            return None

        # Генерируем имя backup'а с timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'database_backup_{timestamp}.sqlite'
        backup_full_path = backup_path / backup_filename

        # Копируем базу данных
        # Используем copy2 для сохранения метаданных (время создания и т.д.)
        shutil.copy2(db_file, backup_full_path)

        # Также копируем WAL файл если он существует (для полной целостности)
        wal_file = Path(f"{DB_PATH}-wal")
        if wal_file.exists():
            wal_backup = backup_path / f'database_backup_{timestamp}.sqlite-wal'
            shutil.copy2(wal_file, wal_backup)
            logger.info(f"WAL file backed up: {wal_backup}")

        # Проверяем размер backup'а (должен быть > 0)
        backup_size = backup_full_path.stat().st_size
        if backup_size == 0:
            logger.error(f"Backup created but file size is 0: {backup_full_path}")
            backup_full_path.unlink()  # Удаляем пустой файл
            return None

        logger.info(f"✅ Backup created successfully: {backup_full_path} ({backup_size:,} bytes)")

        # Очищаем старые backup'ы
        await cleanup_old_backups()

        return str(backup_full_path)

    except PermissionError as e:
        logger.error(f"❌ Permission denied when creating backup: {e}")
        return None
    except IOError as e:
        logger.error(f"❌ IO error when creating backup: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error when creating backup: {e}", exc_info=True)
        return None


async def cleanup_old_backups() -> int:
    """
    Удалить backup'ы старше BACKUP_KEEP_DAYS дней

    Returns:
        Количество удаленных файлов
    """
    try:
        backup_path = Path(BACKUP_DIR)
        if not backup_path.exists():
            return 0

        cutoff_date = datetime.now() - timedelta(days=BACKUP_KEEP_DAYS)
        deleted_count = 0

        # Находим все backup файлы
        backup_files = list(backup_path.glob('database_backup_*.sqlite'))

        for backup_file in backup_files:
            # Получаем время создания файла
            file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)

            # Удаляем если старше cutoff_date
            if file_mtime < cutoff_date:
                try:
                    backup_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old backup: {backup_file.name}")

                    # Также удаляем соответствующий WAL файл если есть
                    wal_file = backup_file.with_suffix('.sqlite-wal')
                    if wal_file.exists():
                        wal_file.unlink()
                        logger.info(f"Deleted old backup WAL: {wal_file.name}")

                except Exception as e:
                    logger.error(f"Failed to delete old backup {backup_file}: {e}")

        if deleted_count > 0:
            logger.info(f"🗑️ Cleaned up {deleted_count} old backup(s)")

        return deleted_count

    except Exception as e:
        logger.error(f"Error during backup cleanup: {e}")
        return 0


async def get_backup_list() -> List[dict]:
    """
    Получить список всех backup'ов

    Returns:
        Список словарей с информацией о backup'ах
        [{'filename': str, 'size': int, 'created': datetime}, ...]
    """
    try:
        backup_path = Path(BACKUP_DIR)
        if not backup_path.exists():
            return []

        backups = []
        for backup_file in backup_path.glob('database_backup_*.sqlite'):
            stat = backup_file.stat()
            backups.append({
                'filename': backup_file.name,
                'path': str(backup_file),
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_mtime),
                'age_hours': (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).total_seconds() / 3600
            })

        # Сортируем по дате создания (новые первые)
        backups.sort(key=lambda x: x['created'], reverse=True)

        return backups

    except Exception as e:
        logger.error(f"Error getting backup list: {e}")
        return []


async def restore_from_backup(backup_path: str) -> bool:
    """
    Восстановить базу данных из backup'а

    Args:
        backup_path: Путь к backup файлу

    Returns:
        True если восстановление успешно

    ВНИМАНИЕ: Эта функция перезапишет текущую БД!
    """
    try:
        backup_file = Path(backup_path)
        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False

        db_file = Path(DB_PATH)

        # Создаем backup текущей БД перед восстановлением (на всякий случай)
        if db_file.exists():
            emergency_backup = f"{DB_PATH}.before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(db_file, emergency_backup)
            logger.info(f"Emergency backup created: {emergency_backup}")

        # Восстанавливаем из backup'а
        shutil.copy2(backup_file, db_file)
        logger.info(f"✅ Database restored from: {backup_path}")

        # Восстанавливаем WAL файл если есть
        wal_backup = Path(f"{backup_path}-wal")
        if wal_backup.exists():
            shutil.copy2(wal_backup, f"{DB_PATH}-wal")
            logger.info(f"WAL file restored from: {wal_backup}")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to restore from backup: {e}", exc_info=True)
        return False


async def schedule_backups():
    """
    Планировщик автоматических backup'ов

    Запускается как background task и создает backup'ы каждые BACKUP_INTERVAL_HOURS часов
    """
    logger.info(f"📦 Backup scheduler started (interval: {BACKUP_INTERVAL_HOURS}h, keep: {BACKUP_KEEP_DAYS}d)")

    # Создаем первый backup сразу при старте
    await create_backup()

    # Затем создаем backup'ы по расписанию
    while True:
        try:
            # Ждем указанный интервал
            await asyncio.sleep(BACKUP_INTERVAL_HOURS * 3600)

            # Создаем backup
            logger.info(f"🕐 Scheduled backup started (interval: {BACKUP_INTERVAL_HOURS}h)")
            backup_path = await create_backup()

            if backup_path:
                # Получаем статистику backup'ов
                backups = await get_backup_list()
                total_size = sum(b['size'] for b in backups)
                logger.info(
                    f"📊 Backup statistics: {len(backups)} backups, "
                    f"total size: {total_size / 1024 / 1024:.2f} MB"
                )
            else:
                logger.warning("⚠️ Scheduled backup failed")

        except asyncio.CancelledError:
            logger.info("Backup scheduler stopped")
            break
        except Exception as e:
            logger.error(f"Error in backup scheduler: {e}", exc_info=True)
            # Продолжаем работу даже при ошибке
            await asyncio.sleep(60)  # Ждем минуту перед повтором


async def verify_backup_integrity(backup_path: str) -> bool:
    """
    Проверить целостность backup'а

    Args:
        backup_path: Путь к backup файлу

    Returns:
        True если backup корректен
    """
    try:
        import aiosqlite

        backup_file = Path(backup_path)
        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False

        # Проверяем что файл не пустой
        if backup_file.stat().st_size == 0:
            logger.error(f"Backup file is empty: {backup_path}")
            return False

        # Пытаемся открыть БД и сделать простой запрос
        async with aiosqlite.connect(backup_path) as db:
            # Проверяем что можем прочитать основные таблицы
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ) as cursor:
                tables = await cursor.fetchall()

                if not tables:
                    logger.error(f"No tables found in backup: {backup_path}")
                    return False

                logger.info(f"✅ Backup integrity OK: {len(tables)} tables found")
                return True

    except Exception as e:
        logger.error(f"Backup integrity check failed for {backup_path}: {e}")
        return False


if __name__ == "__main__":
    # Тестирование модуля
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    async def test():
        print("Creating test backup...")
        backup = await create_backup()

        if backup:
            print(f"✅ Backup created: {backup}")

            print("\nVerifying backup integrity...")
            is_valid = await verify_backup_integrity(backup)
            print(f"Integrity check: {'✅ PASS' if is_valid else '❌ FAIL'}")

            print("\nListing all backups...")
            backups = await get_backup_list()
            for b in backups:
                print(f"  - {b['filename']} ({b['size']:,} bytes, {b['age_hours']:.1f}h ago)")

    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(test())
