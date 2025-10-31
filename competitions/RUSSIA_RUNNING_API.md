# Парсеры соревнований

## Обзор

Модуль соревнований загружает данные из двух источников:
1. **Russia Running API** - централизованный API (в настоящее время использует тестовые данные)
2. **runc.run** - парсер сайта RunC.Run с реальными соревнованиями в Москве и Санкт-Петербурге

## Изменения (31 октября 2025)

### Добавлено:

✅ **RunCRunParser** - парсер runc.run (14 соревнований)
- Загружает реальные соревнования из Москвы и Санкт-Петербурга
- Поддержка фильтрации по городу и месяцу
- Интеграция с общей системой загрузки

✅ **Объединённая загрузка из всех источников**
- Функция `load_competitions_from_api()` теперь загружает из обоих источников
- Автоматическое удаление дубликатов по названию и дате
- Логирование количества загруженных соревнований из каждого источника

✅ **Защита от отображения пользовательских соревнований**
- Все поисковые запросы фильтруют по `is_official = 1`
- Пользовательские соревнования (is_official = 0) не отображаются в публичном поиске
- Пользователь видит свои соревнования только в разделе "Мои соревнования"

## Источники данных

### 1. RunCRunParser (runc.run)

```python
class RunCRunParser:
    BASE_URL = "https://runc.run"
```

**Статус:** ✅ Работает (14 соревнований на 2025 год)

**Соревнования:**
1. Соревнования "Скорость" - Москва, 8 февраля
2. Забег "Апрель" - Москва, 6 апреля
3. Кросс "Быстрый пёс" - Москва, 19 апреля
4. Кросс "Лисья гора" - Москва, 20 апреля
5. Московский полумарафон - Москва, 26 апреля
6. Эстафета по Садовому кольцу - Москва, 17 мая
7. Красочный забег - Москва, 8 июня
8. Ночной забег - Москва, 21 июня
9. Марафон "Белые ночи" - Санкт-Петербург, 5 июля
10. Большой фестиваль бега - Москва, 19 июля
11. СПБ полумарафон "Северная столица" - Санкт-Петербург, 3 августа
12. Полумарафон "Лужники" - Москва, 24 августа
13. Московский Марафон - Москва, 20 сентября
14. Крылатский трейл - Москва, 26 октября

**Методы:**
- `fetch_competitions()` - загрузить все соревнования
- `load_by_city(city)` - фильтрация по городу
- `load_by_city_and_month(city, year, month)` - фильтрация по городу и месяцу

### 2. RussiaRunningAPI

```python
class RussiaRunningAPI:
    BASE_URL = "https://russiarunning.com/api"
    EVENTS_URL = f"{BASE_URL}/events"
```

**Статус:** ⚠️ API недоступен, используются тестовые данные (8 соревнований)

#### Основные методы:

**1. fetch_events(city, year, month)**
- Загружает события из API
- Поддерживает фильтрацию по городу, году, месяцу
- Возвращает список событий в формате API

**2. convert_to_competition_format(event)**
- Конвертирует событие из API в формат БД
- Автоматически определяет тип соревнования по дистанции
- Парсит дистанции из разных форматов (list, string, comma-separated)

**3. load_events_by_city(city)**
- Загружает все соревнования для города
- Фильтрует прошедшие события
- Возвращает список в формате БД

**4. load_events_by_city_and_month(city, year, month)**
- Загружает соревнования для конкретного города и месяца
- Возвращает список в формате БД

### Публичные функции

**load_competitions_from_api(city, year, month)**
```python
# Загрузить все соревнования
competitions = await load_competitions_from_api()

# Загрузить для города
competitions = await load_competitions_from_api(city="Москва")

# Загрузить для города и месяца
competitions = await load_competitions_from_api(
    city="Москва",
    year=2026,
    month=5
)
```

**update_competitions_database_from_api(city, year, month)**
```python
# Обновить БД из API
result = await update_competitions_database_from_api()
# Возвращает: {'added': int, 'skipped': int, 'total': int}
```

**parse_all_sources()** - для обратной совместимости
```python
# Старый код продолжит работать
competitions = await parse_all_sources()
```

## Обновлённый файл: search_competitions_handlers.py

### Что изменилось:

Функция `search_by_city_and_month()` обновлена для использования Russia Running API:

**Было:**
```python
from competitions.competitions_parser import parse_all_sources
parsed_comps = await parse_all_sources()
city_comps = [c for c in parsed_comps if c.get('city') == city]
```

**Стало:**
```python
from competitions.competitions_parser import load_competitions_from_api

if period != 'all':
    year, month = period.split('-')
    api_comps = await load_competitions_from_api(
        city=city,
        year=int(year),
        month=int(month)
    )
else:
    api_comps = await load_competitions_from_api(city=city)
```

### Преимущества:

1. ✅ **Фильтрация на стороне API** - не загружаем лишние данные
2. ✅ **Точная фильтрация по месяцам** - API возвращает только нужный период
3. ✅ **Меньше трафика** - запрашиваем только нужный город и месяц
4. ✅ **Актуальные данные** - всегда свежие соревнования из Russia Running

## Формат данных Russia Running API

### Запрос:
```http
GET https://russiarunning.com/api/events?city=Москва&year=2026&month=5
```

### Ожидаемый ответ:
```json
[
  {
    "name": "Московский марафон 2026",
    "date": "2026-05-17",
    "city": "Москва",
    "location": "Лужники",
    "distances": [42.195, 21.1, 10, 5],
    "type": "марафон",
    "description": "Крупнейший марафон в России",
    "url": "https://moscowmarathon.org",
    "organizer": "Московский марафон",
    "registration_status": "open"
  }
]
```

### Конвертация в формат БД:

API поле → БД поле:
- `name` → `name`
- `date` → `date`
- `city` → `city`
- `location` → `location`
- `distances` → `distances` (JSON)
- `type` → `type` (или автоопределение)
- `description` → `description`
- `url` → `official_url`
- `organizer` → `organizer`
- `registration_status` → `registration_status`

Дополнительные поля:
- `country` = "Россия"
- `status` = "upcoming"
- `is_official` = 1
- `source_url` = "https://russiarunning.com"

## Автоопределение типа соревнования

Если поле `type` отсутствует в API, определяется автоматически по максимальной дистанции:

```python
max_distance >= 42  → "марафон"
max_distance >= 21  → "полумарафон"
max_distance >= 10  → "забег"
иначе              → "забег"
```

## Тестирование

Файл включает тестовые функции:

```bash
cd d:\desktop\coding\trainingdairy_bot-1
python competitions/competitions_parser.py
```

Тесты:
1. Загрузка всех соревнований
2. Загрузка для Москвы
3. Загрузка для Москвы на май 2026

## Обратная совместимость

Старый код продолжит работать:
- `parse_all_sources()` теперь вызывает `load_competitions_from_api()`
- Формат возвращаемых данных не изменился

## Приватность пользовательских соревнований

### Концепция

Когда пользователь создаёт "своё соревнование" через кнопку **➕ Создать своё**, он **НЕ** является организатором. Он просто записывает название и данные соревнований, в которых принимает участие, для личного трекинга.

### Разделение соревнований

**Публичные соревнования** (`is_official = 1`):
- Загружаются только из парсеров (runc.run, Russia Running API)
- Видны всем пользователям в поиске
- Имеют `source_url` (например: "https://runc.run")
- Поле `created_by` = NULL

**Пользовательские соревнования** (`is_official = 0`):
- Создаются пользователем вручную
- Видны только создателю в разделе "Мои соревнования"
- НЕ отображаются в публичном поиске
- Имеют `created_by` = user_id
- Поле `source_url` = NULL

### Защита от утечки

Все запросы к БД в следующих модулях фильтруют по `is_official = 1`:

**competitions/search_queries.py:**
- `search_competitions_by_city_and_month()`
- `search_competitions_by_city()`
- `get_available_cities()`
- `get_competitions_count_by_city()`

**competitions/competitions_queries.py:**
- `get_upcoming_competitions()`
- `search_competitions()`

### Запросы без фильтрации

Следующие запросы НЕ фильтруют по is_official (это правильно):
- `get_competition(id)` - прямой доступ по ID (нужен для регистрации)
- `get_user_competitions()` - личные соревнования пользователя

## Итоги

- **Добавлено**: Парсер runc.run (14 реальных соревнований)
- **Добавлено**: Защита приватности пользовательских соревнований
- **Добавлено**: Объединённая загрузка из нескольких источников
- **Статус Russia Running API**: ⚠️ Недоступен, используются тестовые данные
- **Статус runc.run**: ✅ Работает с реальными данными
- **Общий статус**: ✅ Готово к использованию

---

**Дата обновления**: 31 октября 2025
**Версия**: 3.0
