# Инструкция по установке и запуску

## Быстрый старт

### 1. Проверка базы данных

Если вы обновили бота и добавили модуль "Здоровье", нужно запустить миграцию:

```bash
python migrate_health_table.py
```

Вы должны увидеть:
```
Запуск миграции...
OK - Таблица health_metrics успешно создана! (или уже существует)
Структура таблицы (13 колонок):
  ...
Миграция завершена!
```

### 2. Запуск бота

```bash
python main.py
```

### 3. Проверка работы модуля "Здоровье"

1. Откройте бота в Telegram
2. Нажмите кнопку **❤️ Здоровье**
3. Попробуйте внести данные: **📝 Внести данные** → **✏️ Ввести всё**
4. После нескольких дней использования проверьте **😴 Анализ сна**

## Структура проекта

```
trainingdairy_bot/
├── main.py                         # Точка входа
├── database.sqlite                 # Основная БД (создаётся автоматически)
├── .env                           # Переменные окружения (BOT_TOKEN, DB_PATH)
│
├── bot/                           # Основные модули бота
│   ├── handlers.py               # Обработчики тренировок
│   ├── keyboards.py              # Клавиатуры
│   ├── fsm.py                    # FSM состояния
│   └── ...
│
├── health/                        # Модуль здоровья ⭐ НОВЫЙ
│   ├── health_handlers.py        # Обработчики
│   ├── health_keyboards.py       # Клавиатуры
│   ├── health_fsm.py             # FSM состояния
│   ├── health_queries.py         # Запросы к БД
│   ├── health_graphs.py          # Генерация графиков
│   ├── sleep_analysis.py         # Анализ сна
│   └── README.md                 # Документация модуля
│
├── database/
│   ├── models.py                 # Схемы таблиц (включая health_metrics)
│   └── queries.py                # CRUD операции
│
├── notifications/
│   └── notification_scheduler.py # Система уведомлений (обновлена)
│
└── migrate_health_table.py       # Миграционный скрипт ⭐ НОВЫЙ
```

## Зависимости

Все необходимые библиотеки уже указаны в `requirements.txt`:

- **aiogram** - фреймворк для бота
- **aiosqlite** - асинхронная работа с SQLite
- **matplotlib** - построение графиков
- **pandas, numpy** - анализ данных

Установка (если нужно):
```bash
pip install -r requirements.txt
```

## Переменные окружения (.env)

```env
BOT_TOKEN=your_bot_token_here
DB_PATH=database.sqlite
```

## Таблица health_metrics

Структура (создаётся автоматически):

```sql
CREATE TABLE health_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date DATE NOT NULL,

    -- Основные метрики
    morning_pulse INTEGER,
    weight REAL,
    sleep_duration REAL,
    sleep_quality INTEGER,

    -- Дополнительно
    mood INTEGER,
    stress_level INTEGER,
    energy_level INTEGER,
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, date)
)
```

## Устранение проблем

### Ошибка "no such table: health_metrics"

**Решение:** Запустите миграцию
```bash
python migrate_health_table.py
```

### Ошибка с кодировкой в Windows

**Решение:** Миграционный скрипт автоматически настраивает UTF-8 для Windows

### Бот не отвечает на кнопку "Здоровье"

**Проверьте:**
1. Роутер подключен в `main.py`: `dp.include_router(health_router)`
2. Импорт есть: `from health.health_handlers import router as health_router`
3. Таблица создана: `python migrate_health_table.py`

### Графики не генерируются

**Проверьте:**
1. Установлен matplotlib: `pip install matplotlib`
2. Есть данные за период: минимум 2-3 дня

### Анализ сна не работает

**Требования:**
- Минимум 3 дня с данными о сне
- Для точного анализа желательно 7-14 дней

## Обновление существующего бота

Если у вас уже запущен бот:

1. **Остановите бота** (Ctrl+C)
2. **Запустите миграцию:**
   ```bash
   python migrate_health_table.py
   ```
3. **Перезапустите бота:**
   ```bash
   python main.py
   ```

Все существующие данные (тренировки, пользователи) сохранятся!

## Полезные команды

### Проверка таблиц в БД
```bash
python -c "import sqlite3; conn = sqlite3.connect('database.sqlite'); cursor = conn.cursor(); cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"'); print([row[0] for row in cursor.fetchall()]); conn.close()"
```

### Проверка структуры health_metrics
```bash
python -c "import sqlite3; conn = sqlite3.connect('database.sqlite'); cursor = conn.cursor(); cursor.execute('PRAGMA table_info(health_metrics)'); print([(col[1], col[2]) for col in cursor.fetchall()]); conn.close()"
```

### Проверка данных
```bash
python -c "import sqlite3; conn = sqlite3.connect('database.sqlite'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM health_metrics'); print(f'Записей в health_metrics: {cursor.fetchone()[0]}'); conn.close()"
```

## Документация

- **[health/README.md](health/README.md)** - Техническая документация модуля
- **[HEALTH_USER_GUIDE.md](HEALTH_USER_GUIDE.md)** - Руководство пользователя

## Поддержка

При возникновении проблем:
1. Проверьте логи бота
2. Убедитесь, что миграция выполнена
3. Проверьте наличие всех таблиц в БД
4. Изучите документацию выше

---

**Готово! Модуль "Здоровье" установлен и готов к использованию! 💪**
