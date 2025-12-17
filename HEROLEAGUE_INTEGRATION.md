# Интеграция Лиги Героев

## Что добавлено

Добавлена поддержка третьего сервиса для поиска соревнований - **Лига Героев** (https://heroleague.ru)

### Новые файлы

1. **competitions/heroleague_parser.py** - Парсер для API Лиги Героев
   - Endpoint: `GET https://heroleague.ru/api/event/list`
   - Поддержка фильтрации по городу, спорту, периоду
   - Автоматическое определение типа спорта по event_type

2. **test_heroleague_parser.py** - Комплексные тесты парсера
   - 6 тестов, все проходят ✅
   - Проверка всех типов фильтрации

3. **test_all_services.py** - Тесты интеграции всех сервисов

### Измененные файлы

1. **competitions/competitions_fetcher.py**
   - Добавлен импорт `heroleague_parser`
   - Добавлена логика получения соревнований из HeroLeague
   - Обновлен `SERVICE_CODES`:
     ```python
     SERVICE_CODES = {
         "RussiaRunning": "RussiaRunning",
         "Timerman": "Timerman",
         "Лига Героев": "HeroLeague",  # ← НОВОЕ
         "Все сервисы": "all",
     }
     ```

2. **competitions/upcoming_competitions_handlers.py** (будет обновлен автоматически)
   - Фильтр "Сервис для регистрации" теперь показывает 3 опции вместо 2

## Структура данных Лиги Героев

### API Response

```json
{
  "values": [
    {
      "event_type": {
        "public_id": "gonka",
        "title": "Гонка Героев"
      },
      "title": "Гонка Героев",
      "description": "Описание с дистанциями",
      "public_id": "gonka2026",
      "event_city": [
        {
          "city": {
            "name_ru": "Москва"
          },
          "address": "Адрес старта",
          "start_time": "2026-04-18T06:00:00",
          "public_id": "gonka2026_msk",
          "registration_open": "...",
          "registration_close": "..."
        }
      ]
    }
  ]
}
```

### Parsed Competition

```python
{
    "id": "gonka2026_msk",
    "title": "Гонка Героев",
    "code": "gonka2026",
    "city": "Москва",
    "place": "Адрес старта",
    "sport_code": "gonka",
    "organizer": "Лига Героев",
    "service": "HeroLeague",
    "begin_date": "2026-04-18T06:00:00",
    "formatted_date": "18.04.2026",
    "description": "Описание с дистанциями",
    "event_type": "Гонка Героев",
    "registration_open": "...",
    "registration_close": "...",
    "url": "https://heroleague.ru/event/gonka2026",
    "distances_text": "Описание дистанций из description"
}
```

## Особенности реализации

### 1. Отсутствие структурированных дистанций

В отличие от RussiaRunning и Timerman, API Лиги Героев **не возвращает структурированный список дистанций**. Дистанции указаны только в текстовом поле `description`.

**Решение:**
- Сохраняем описание в поле `distances_text`
- В будущем можно добавить парсинг текста или дополнительный API запрос

### 2. Маппинг типов спорта

Функция `matches_sport_type()` определяет соответствие event_type виду спорта:

```python
sport_mapping = {
    "run": ["gonka", "zabeg", "race", "run", "marathon", "doroga"],
    "ski": ["skirun", "snowrun", "ski", "лыж"],
    "bike": ["bike", "велос"],
    "swim": ["swim", "плав"],
    "triathlon": ["triathlon", "триатлон"],
}
```

### 3. Структура event_city

Каждый event может содержать несколько городов (`event_city`). Парсер обрабатывает каждый город как отдельное соревнование.

## Тестирование

### Запуск тестов

```bash
# Тест парсера HeroLeague
python test_heroleague_parser.py

# Тест интеграции всех сервисов
python test_all_services.py

# Проверка синтаксиса
python -m py_compile competitions/heroleague_parser.py
```

### Результаты тестов

Все тесты прошли успешно ✅:

```
✅ PASSED: Базовое получение
✅ PASSED: Фильтр по городу
✅ PASSED: Фильтр по спорту
✅ PASSED: Фильтр по периоду
✅ PASSED: Комбинированные фильтры
✅ PASSED: Структура данных
```

## Примеры использования

### Получить соревнования из Лиги Героев

```python
from competitions.heroleague_parser import fetch_competitions

# Все соревнования
comps = await fetch_competitions(limit=10)

# С фильтрами
comps = await fetch_competitions(
    city="Москва",
    sport="run",
    period_months=3,
    limit=10
)
```

### Получить из всех сервисов

```python
from competitions.competitions_fetcher import fetch_all_competitions

# Все сервисы
comps = await fetch_all_competitions(
    city="Москва",
    sport="run",
    service="all"
)

# Только Лига Героев
comps = await fetch_all_competitions(
    city="Москва",
    service="HeroLeague"
)
```

## Известные ограничения

1. **Дистанции**: Нет структурированного списка дистанций, только текстовое описание
2. **Детали**: Нет endpoint для получения детальной информации о дистанциях
3. **Регистрация**: URL ведет на страницу события, но не напрямую на регистрацию

## Возможные улучшения

1. **Парсинг дистанций из текста** - добавить регулярные выражения для извлечения дистанций
2. **Дополнительный API запрос** - найти endpoint для получения детальной информации
3. **Кэширование** - добавить кэш для API ответов (как в parser.py)
4. **Улучшенная фильтрация спорта** - более точное определение типа спорта

## Статистика

- **Типов событий**: 9 (лыжи, гонки, марафоны, забеги)
- **Соревнований**: ~70+ активных событий по всей России
- **Города**: Москва, Санкт-Петербург, и другие крупные города
- **Средний размер ответа API**: ~34KB JSON
