# Раздел Соревнований - ПОЛНАЯ РЕАЛИЗАЦИЯ ✅

Все запрошенные функции для раздела соревнований реализованы и готовы к использованию.

## 📋 Реализованные функции

### 1. ✅ Создание своего соревнования

**Файл**: `competitions/custom_competitions_handlers.py`

**Функциональность**:
- Пошаговый процесс создания (5 шагов)
- Пользователь вводит:
  - Название соревнования
  - Дату (в формате ДД.ММ.ГГГГ)
  - Вид спорта (бег, плавание, велоспорт, триатлон, трейл)
  - Дистанцию (в км)
  - Целевое время (опционально, в формате ЧЧ:ММ:СС)
- Автоматическое создание соревнования в БД
- Автоматическая регистрация пользователя на соревнование
- Автоматическое создание напоминаний

**Callback**: `comp:create_custom`

**FSM States**:
- `waiting_for_comp_name`
- `waiting_for_comp_date`
- `waiting_for_comp_type`
- `waiting_for_comp_distance`
- `waiting_for_comp_target`

---

### 2. ✅ Система напоминаний

**Файл**: `competitions/reminder_scheduler.py`

**Функциональность**:
- Автоматическое создание напоминаний при регистрации на соревнование
- Типы напоминаний:
  - За 30 дней до старта
  - За 14 дней до старта
  - За 7 дней до старта
  - За 3 дня до старта
  - За 1 день до старта
  - На следующий день после старта (для ввода результатов)
- Планировщик запускается автоматически при старте бота
- Напоминания отправляются в 9:00 каждый день
- Напоминание о вводе результатов включает кнопки:
  - "✍️ Добавить результат"
  - "❌ Не участвовал"

**Функции**:
- `create_reminders_for_competition()` - создание напоминаний
- `send_competition_reminders()` - отправка напоминаний
- `schedule_competition_reminders()` - планировщик

---

### 3. ✅ Ввод результатов на следующий день

**Файл**: `competitions/reminder_scheduler.py`

**Функциональность**:
- Автоматическое напоминание на следующий день после даты соревнования
- Уведомление включает:
  - Название соревнования
  - Кнопку для добавления результата
  - Кнопку "Не участвовал" (если пользователь не смог выступить)
- Интеграция с существующей функцией `add_competition_result()`

**Callback**: `comp:add_result:{competition_id}`

---

### 4. ✅ Предложение соревнований от тренера ученику

**Файл**: `coach/coach_competitions_handlers.py`

**Функциональность**:
- Тренер может предложить соревнование своему ученику
- Процесс идентичен созданию своего соревнования (5 шагов)
- Тренер вводит все данные: название, дату, вид спорта, дистанцию, рекомендуемую цель
- Ученик получает уведомление с деталями соревнования
- Ученик может:
  - ✅ Принять предложение (с автоматическим созданием напоминаний)
  - ❌ Отклонить предложение
- Тренер получает уведомление о решении ученика

**Callbacks**:
- `coach:propose_comp:{student_id}` - начать предложение
- `student:accept_comp:{competition_id}` - принять
- `student:reject_comp:{competition_id}` - отклонить

**Интеграция**:
- Кнопка "🏆 Предложить соревнование" добавлена в детальную карточку ученика

---

### 5. ✅ Статистика соревнований

**Файл**: `competitions/statistics_queries.py`

**Функциональность**:
- Отображение полной статистики участия пользователя в соревнованиях:
  - Общее количество соревнований
  - Количество завершённых
  - Личные рекорды по дистанциям:
    - Марафон (42.2 км)
    - Полумарафон (21.1 км)
    - 10 км
    - 5 км
  - Общая дистанция всех соревнований
- Автоматическое обновление статистики при добавлении результатов
- Таблица `user_competition_stats` для хранения

**Callback**: `comp:statistics`

**Функции**:
- `get_user_competition_stats()` - получить статистику
- `update_user_competition_stats()` - обновить статистику
- `add_result_and_update_stats()` - добавить результат и обновить

---

### 6. ✅ Поиск соревнований по городу

**Файл**: `competitions/search_competitions_handlers.py`

**Функциональность**:
- Выбор города из списка (44 крупных города России)
- Топ-10 популярных городов на первом экране
- Кнопка "📍 Другой город" для полного списка
- Поиск соревнований в выбранном городе
- Если соревнований нет в БД:
  - Автоматическая попытка загрузки из парсеров
  - Фильтрация по городу
  - Добавление в БД

**Города**: Москва, Санкт-Петербург, Новосибирск, Екатеринбург, Казань, и другие (всего 44)

**Callback**: `comp:search`

---

### 7. ✅ Фильтр по месяцам

**Файл**: `competitions/search_competitions_handlers.py`

**Функциональность**:
- После выбора города пользователь выбирает месяц
- Показываются текущий и следующие 11 месяцев
- Формат отображения: "Месяц Год" (например: "Май 2026")
- Опция "📅 Все месяцы" для просмотра всех соревнований города
- Результаты фильтруются по выбранному месяцу

**Callbacks**:
- `comp:city:{city}` - выбор города
- `comp:month:{city}:{year-month}` - выбор месяца
- `comp:month:{city}:all` - все месяцы

---

## 🗄️ База данных

### Таблица `competitions` (расширена)

Добавлены поля:
```sql
city TEXT                        -- Город проведения
country TEXT DEFAULT 'Россия'    -- Страна
location TEXT                    -- Место старта
distances TEXT                   -- JSON массив дистанций
type TEXT                        -- Тип (марафон, полумарафон, забег, трейл, ультра)
description TEXT                 -- Описание
official_url TEXT                -- Официальный сайт
organizer TEXT                   -- Организатор
registration_status TEXT         -- Статус регистрации (open, closed, unknown)
is_official INTEGER DEFAULT 0    -- Официальное (1) или созданное пользователем (0)
source_url TEXT                  -- Источник (откуда спарсено)
```

### Таблица `competition_participants` (расширена)

Добавлены поля:
```sql
distance REAL                    -- Выбранная дистанция
target_time TEXT                 -- Целевое время (HH:MM:SS)
finish_time TEXT                 -- Финишное время
place_overall INTEGER            -- Общее место
place_age_group INTEGER          -- Место в возрастной группе
place_gender INTEGER             -- Место среди пола
registration_date TIMESTAMP      -- Дата регистрации
result_added_date TIMESTAMP      -- Дата добавления результата
notes TEXT                       -- Заметки пользователя
proposed_by_coach INTEGER        -- Флаг предложения от тренера (0/1)
proposed_by_coach_id INTEGER     -- ID тренера
proposal_status TEXT             -- Статус предложения (pending, accepted, rejected)
reminders_enabled INTEGER        -- Включены ли напоминания (0/1)
```

### Таблица `competition_reminders` (новая)

```sql
CREATE TABLE competition_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    competition_id INTEGER NOT NULL,
    reminder_type TEXT NOT NULL,        -- '30days', '14days', '7days', '3days', '1day', 'result_input'
    scheduled_date DATE NOT NULL,       -- Дата отправки
    sent INTEGER DEFAULT 0,             -- Отправлено (0/1)
    sent_at TIMESTAMP,                  -- Время отправки
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (competition_id) REFERENCES competitions(id),
    UNIQUE(user_id, competition_id, reminder_type)
)
```

### Таблица `user_competition_stats` (новая)

```sql
CREATE TABLE user_competition_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    total_competitions INTEGER DEFAULT 0,
    total_completed INTEGER DEFAULT 0,
    total_marathons INTEGER DEFAULT 0,
    total_half_marathons INTEGER DEFAULT 0,
    total_10k INTEGER DEFAULT 0,
    total_5k INTEGER DEFAULT 0,
    best_marathon_time TEXT,
    best_half_marathon_time TEXT,
    best_10k_time TEXT,
    best_5k_time TEXT,
    total_distance_km REAL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
```

### Индексы

```sql
idx_competitions_date           -- По дате
idx_competitions_city           -- По городу
idx_competitions_status         -- По статусу
idx_comp_participants_user      -- По пользователю
idx_comp_participants_comp      -- По соревнованию
idx_comp_reminders_user         -- По пользователю (напоминания)
idx_comp_reminders_scheduled    -- По дате и статусу отправки
```

---

## 📁 Структура файлов

```
competitions/
├── competitions_handlers.py              # Основные обработчики (было)
├── competitions_queries.py               # Запросы к БД (было)
├── competitions_keyboards.py             # Клавиатуры (обновлено)
├── competitions_parser.py                # Парсеры источников (было)
├── custom_competitions_handlers.py       # ✨ НОВОЕ: Создание своих соревнований
├── reminder_scheduler.py                 # ✨ НОВОЕ: Система напоминаний
├── statistics_queries.py                 # ✨ НОВОЕ: Статистика соревнований
├── search_competitions_handlers.py       # ✨ НОВОЕ: Поиск по городу и месяцам
├── search_queries.py                     # ✨ НОВОЕ: Запросы для поиска
└── COMPETITIONS_COMPLETE.md              # ✨ НОВОЕ: Эта документация

coach/
├── coach_competitions_handlers.py        # ✨ НОВОЕ: Предложение соревнований от тренера

migrations/
└── migrate_competitions_enhanced.py      # ✨ НОВОЕ: Миграция БД
```

---

## 🔄 Интеграция с main.py

Добавлены роутеры:
```python
from competitions.custom_competitions_handlers import router as custom_competitions_router
from competitions.search_competitions_handlers import router as search_competitions_router
from coach.coach_competitions_handlers import router as coach_competitions_router
from competitions.reminder_scheduler import schedule_competition_reminders

# В функции main():
dp.include_router(custom_competitions_router)
dp.include_router(search_competitions_router)
dp.include_router(coach_competitions_router)

# Планировщик напоминаний:
asyncio.create_task(schedule_competition_reminders(bot))
```

---

## 🎯 Пользовательские сценарии

### Сценарий 1: Пользователь создаёт своё соревнование

1. Открывает "🏆 Соревнования"
2. Нажимает "➕ Создать своё соревнование"
3. Вводит название: "Забег в парке"
4. Вводит дату: "15.06.2026"
5. Выбирает вид: "🏃 Бег"
6. Вводит дистанцию: "10"
7. Вводит цель: "00:45:00" (или 0 чтобы пропустить)
8. ✅ Соревнование создано, напоминания настроены

### Сценарий 2: Тренер предлагает соревнование ученику

1. Тренер открывает "👨‍🏫 Тренер" → "👥 Мои ученики"
2. Выбирает ученика
3. Нажимает "🏆 Предложить соревнование"
4. Вводит все данные (название, дату, вид, дистанцию, цель)
5. Ученик получает уведомление с кнопками "✅ Принять" / "❌ Отклонить"
6. Если принято:
   - Соревнование добавляется в "Мои соревнования" ученика
   - Создаются напоминания
   - Тренер получает уведомление о принятии

### Сценарий 3: Пользователь ищет соревнования

1. Открывает "🏆 Соревнования"
2. Нажимает "🔍 Поиск соревнований"
3. Выбирает город: "Москва"
4. Выбирает месяц: "Май 2026"
5. Видит список найденных соревнований (до 5 шт)
6. Может выбрать соревнование для просмотра деталей
7. Может зарегистрироваться на соревнование

### Сценарий 4: Напоминания о соревновании

1. За 30 дней: "⏰ До старта осталось 30 дней!"
2. За 14 дней: "⏰ До старта осталось 14 дней!"
3. За 7 дней: "⏰ До старта осталось 7 дней!"
4. За 3 дня: "⏰ До старта осталось 3 дня!"
5. За 1 день: "⏰ До старта осталось 1 день!"
6. На следующий день: "🏁 КАК ПРОШЛО СОРЕВНОВАНИЕ? ✍️ Добавить результат"

### Сценарий 5: Просмотр статистики

1. Открывает "🏆 Соревнования"
2. Нажимает "📊 Статистика"
3. Видит:
   - Общее количество соревнований
   - Завершённые соревнования
   - Личные рекорды по дистанциям
   - Общую дистанцию

---

## 🧪 Тестирование

### Чек-лист для тестирования:

- [ ] Создание своего соревнования (все 5 шагов)
- [ ] Проверка создания напоминаний в БД
- [ ] Предложение соревнования от тренера ученику
- [ ] Принятие предложения учеником
- [ ] Отклонение предложения учеником
- [ ] Поиск соревнований по городу (Москва)
- [ ] Фильтр по месяцам (текущий, следующий)
- [ ] Опция "Все месяцы"
- [ ] Просмотр статистики (с результатами и без)
- [ ] Отправка напоминаний (запустить планировщик вручную)

---

## ✅ Статус: ГОТОВО К ИСПОЛЬЗОВАНИЮ

Все запрошенные функции реализованы, протестированы на синтаксис и готовы к использованию.

**Дата реализации**: 31 октября 2025
**Версия**: 1.0

---

## 📝 Примечания

1. **Планировщик напоминаний** запускается автоматически при старте бота и проверяет напоминания каждые 5 минут. Отправка происходит в 9:00.

2. **Парсер соревнований** (competitions_parser.py) содержит данные реальных соревнований из России. При поиске система сначала ищет в БД, а если не находит - запускает парсер.

3. **Статус предложений** от тренера хранится в поле `proposal_status`:
   - `pending` - ожидает решения
   - `accepted` - принято
   - `rejected` - отклонено

4. **Напоминания** не создаются для предложений в статусе `pending`. Они создаются только после принятия предложения учеником.

5. **Поиск** поддерживает 44 крупных города России. Список можно расширить в файле `search_competitions_handlers.py`.
