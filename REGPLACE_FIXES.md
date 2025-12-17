# Исправления для reg.place

## Версия 2 - Дополнительные исправления

### ❌ Неверный URL события
**Причина:** URL формировался как `https://reg.place/event/{slug}` но может быть неправильным
**Решение:**
1. Сначала пытаемся получить URL напрямую из API (поля `url` или `link`)
2. Если URL относительный, делаем его абсолютным
3. Только если URL нет в API, формируем сами из идентификатора
4. Добавлено логирование для отладки URL

**Код ([regplace_parser.py:250-260](competitions/regplace_parser.py#L250-L260)):**
```python
# URL события - пробуем получить из API или формируем сами
event_url = event.get('url', '') or event.get('link', '')
if not event_url:
    # Формируем URL из идентификатора
    event_url = f"https://reg.place/event/{identifier}"

# Если URL относительный, делаем абсолютным
if event_url and not event_url.startswith('http'):
    event_url = f"https://reg.place{event_url if event_url.startswith('/') else '/' + event_url}"

logger.debug(f"Event URL: {event_url} (from API: {bool(event.get('url'))})")
```

### ❌ Фильтр "месяц" работал неправильно
**Было:** Фильтр "1 месяц" означал 30 дней от текущей даты
**Стало:** Фильтр "1 месяц" означает календарный месяц (с 1 по последнее число текущего месяца)

**Реализация ([regplace_parser.py:136-164](competitions/regplace_parser.py#L136-L164)):**
- **1 месяц** - с 1-го до последнего дня текущего месяца
- **6 месяцев** - от текущей даты + 180 дней
- **12 месяцев** - с 01.01 до 31.12 текущего года

Логика полностью соответствует RussiaRunning парсеру.

### Улучшена обработка идентификаторов
Теперь используется либо `slug`, либо `id`/`event_id` из API:
```python
slug = event.get('slug', '')
event_id = event.get('id', '') or event.get('event_id', '')
identifier = slug or event_id
```

### Добавлено подробное логирование
- Структура первого события (для отладки)
- Предупреждения при отсутствии идентификатора или названия
- Логи формирования URL
- Логи фильтрации по периоду

## Версия 1 - Первоначальные исправления

## Проблемы которые были исправлены

### 1. ❌ Ошибка при открытии события
**Причина:** Отсутствовало поле `place` в данных соревнования
**Где:** В [upcoming_competitions_handlers.py:568](competitions/upcoming_competitions_handlers.py#L568) код пытается получить `comp['place']`
**Решение:** Добавлено поле `place` в парсер reg.place ([regplace_parser.py:251](competitions/regplace_parser.py#L251))

```python
'place': city_name,  # Для совместимости (используется в show_competition_detail)
```

### 2. ❌ Ошибка форматирования дат
**Причина:** Поле `begin_date` было в формате `YYYY-MM-DD` вместо ISO формата
**Где:** В [upcoming_competitions_handlers.py:555](competitions/upcoming_competitions_handlers.py#L555) код парсит дату через `datetime.fromisoformat()`
**Решение:** Изменен формат дат на ISO в парсере

**Было:**
```python
'begin_date': start_time.strftime('%Y-%m-%d'),  # Формат YYYY-MM-DD
'end_date': start_time,  # datetime объект
```

**Стало:**
```python
'begin_date': start_time.isoformat(),  # ISO формат: 2025-01-15T10:00:00
'end_date': start_time.isoformat(),    # ISO формат: 2025-01-15T10:00:00
```

### 3. ❌ Фильтры не работают

#### 3.1 Фильтр по периоду
**Причина:** Не была реализована фильтрация по `period_months`
**Решение:** Добавлена логика фильтрации в [regplace_parser.py:145-149](competitions/regplace_parser.py#L145-L149)

```python
# Фильтр по периоду
if period_months and max_date:
    comp_date = comp.get('start_time')
    if comp_date and comp_date > max_date:
        continue
```

#### 3.2 Фильтр по городу и спорту
**Проверка:** Функция `matches_filters()` работает корректно
- Фильтр по городу: регистронезависимый поиск подстроки
- Фильтр по спорту: точное совпадение sport_code

## Дополнительные улучшения

### Добавлено поле `name`
Для совместимости с некоторыми обработчиками добавлено дублирующее поле:
```python
'name': name,  # Дублируем title для совместимости
```

### Улучшено логирование
Добавлены подробные логи для отладки:
- Попытки различных endpoint'ов
- Успешное подключение к API
- Количество найденных и отфильтрованных событий

## Структура данных reg.place

Финальная структура данных соревнования от reg.place:

```python
{
    'id': 'event-slug',                    # Уникальный идентификатор
    'title': 'Название события',           # Основное название
    'name': 'Название события',            # Дубликат для совместимости
    'url': 'https://reg.place/event/...',  # URL события
    'city': 'Москва',                      # Город
    'place': 'Москва',                     # Место (дубликат города)
    'date': '31.12.2025',                  # Дата в формате ДД.ММ.ГГГГ
    'begin_date': '2025-12-31T10:00:00',   # Дата начала в ISO формате
    'end_date': '2025-12-31T10:00:00',     # Дата окончания в ISO формате
    'sport_code': 'run',                   # Код спорта
    'service': 'reg.place',                # Идентификатор сервиса
    'distances': [                         # Массив дистанций
        {
            'distance': 5.0,               # Дистанция в км
            'name': '5 км'                 # Название дистанции
        }
    ],
    'start_time': datetime_object          # Объект datetime для сортировки
}
```

## Что протестировать

1. **Открытие события reg.place**
   - Нажмите на любое событие от reg.place
   - Должна открыться детальная информация без ошибок
   - Должны отображаться: название, дата, место, вид спорта, дистанции (если есть)

2. **Фильтр по городу**
   - Выберите конкретный город в фильтрах
   - Должны показываться только события из этого города

3. **Фильтр по виду спорта**
   - Выберите конкретный вид спорта (например, "Бег")
   - Должны показываться только события этого вида спорта

4. **Фильтр по периоду**
   - Выберите период (например, "1 месяц")
   - Должны показываться только события в течение этого периода

5. **Регистрация на событие**
   - Нажмите "Я участвую" на событии reg.place
   - Выберите дистанцию (если доступны несколько)
   - Введите целевое время
   - Событие должно появиться в "Мои соревнования"

## Возможные проблемы

### Если API endpoint не работает
Парсер пробует несколько endpoint'ов:
1. `https://api.reg.place/v1/events`
2. `https://api.reg.place/v1/event/list`
3. `https://api.reg.place/v1/search`
4. `https://reg.place/api/events`

Если ни один не работает, события от reg.place не будут отображаться, но остальные сервисы будут работать нормально.

### Если структура API отличается
Парсер адаптирован под предполагаемую структуру данных. Если реальная структура отличается, может потребоваться корректировка парсинга полей:
- `slug` - идентификатор события
- `name` или `title` - название
- `start_time`, `date`, или `start_date` - дата
- `city` - город (может быть объектом или строкой)
- `sport_type`, `sport`, или `type` - тип спорта
- `races` - массив дистанций

## Логи для отладки

Если возникают проблемы, проверьте логи бота. Будут полезны следующие сообщения:

```
INFO:competitions.regplace_parser:Trying reg.place endpoint: https://...
INFO:competitions.regplace_parser:SUCCESS! reg.place endpoint ... returned status 200
INFO:competitions.regplace_parser:Response type: list
INFO:competitions.regplace_parser:Found 50 events from reg.place
INFO:competitions.regplace_parser:Parsed 25 competitions from reg.place after filters
```

Или ошибки:
```
ERROR:competitions.regplace_parser:No working endpoint found for reg.place
ERROR:competitions.regplace_parser:Error parsing reg.place event: ...
ERROR:competitions.regplace_parser:Error fetching from reg.place: ...
```
