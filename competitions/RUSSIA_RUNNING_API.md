# Russia Running API Integration

## Изменения

Все парсеры удалены. Теперь используется только **Russia Running API** для загрузки соревнований.

## Обновлённый файл: competitions_parser.py

### Что изменилось:

✅ **Удалено** (528 строк):
- `ProbegOrgParser` - парсер probeg.org
- `RussiaRunningParser` - статический список соревнований
- `TimermanParser` - парсер timerman.info
- `LigaStarshevParser` - парсер ligastarshev.ru
- `FruitZabegParser` - парсер fruitzabeg.ru
- Все хардкодные данные соревнований

✅ **Добавлено** (325 строк):
- `RussiaRunningAPI` - класс для работы с Russia Running API
- Методы для загрузки по городу, году и месяцу
- Автоматическая конвертация данных из API в формат БД
- Определение типа соревнования по дистанции (марафон/полумарафон/забег)

### Класс RussiaRunningAPI

```python
class RussiaRunningAPI:
    BASE_URL = "https://russiarunning.com/api"
    EVENTS_URL = f"{BASE_URL}/events"
```

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

## Итоги

- **Удалено**: ~500 строк статических данных и парсеров
- **Добавлено**: ~300 строк работы с Russia Running API
- **Результат**: Чистый, актуальный код с реальными данными из API
- **Статус**: ✅ Готово к использованию

---

**Дата обновления**: 31 октября 2025
**Версия**: 2.0
