# Исправления reg.place - Версия 4

## Дата: 2025-12-17

### Исправленные проблемы

#### 1. ✅ Название сервиса с маленькой буквы

**Проблема:** В меню выбора сервиса отображалось "reg.place" с маленькой буквы.

**Решение:** Изменено отображение на "Reg.place" с большой буквы ([competitions_fetcher.py:121](competitions/competitions_fetcher.py#L121))

**Было:**
```python
SERVICE_CODES = {
    ...
    "reg.place": "reg.place",
    ...
}
```

**Стало:**
```python
SERVICE_CODES = {
    ...
    "Reg.place": "reg.place",
    ...
}
```

---

#### 2. ✅ Фильтрация по видам спорта работала некорректно

**Проблема:** События плавания, велоспорта и других видов спорта неправильно определялись как "бег".

**Причина:** В функции `normalize_sport_code()` в блоке `else` по умолчанию возвращалось "run", даже для неизвестных видов спорта.

**Решение:** Улучшена логика нормализации ([regplace_parser.py:25-58](competitions/regplace_parser.py#L25-L58))

**Изменения:**
1. Добавлена проверка на пустое значение `sport_type`
2. Добавлены дополнительные ключевые слова (trail, cycle, заплыв, duathlon и т.д.)
3. Для неизвестных типов спорта возвращается оригинальное значение в lowercase (не "run"!)
4. Добавлено подробное логирование нормализации

**Новая логика:**
```python
if not sport_type:
    logger.warning("Empty sport_type provided, defaulting to 'run'")
    return "run"

sport_lower = sport_type.lower()

if any(keyword in sport_lower for keyword in ["run", "бег", "марафон", "забег", "trail", "трейл"]):
    result = "run"
elif any(keyword in sport_lower for keyword in ["bike", "cycling", "велос", "вело", "cycle"]):
    result = "bike"
elif any(keyword in sport_lower for keyword in ["swim", "плав", "заплыв"]):
    result = "swim"
elif any(keyword in sport_lower for keyword in ["triathlon", "триатлон", "duathlon", "дуатлон"]):
    result = "triathlon"
elif any(keyword in sport_lower for keyword in ["ski", "лыж", "лыжн"]):
    result = "ski"
else:
    # Неизвестный тип - возвращаем оригинал!
    logger.warning(f"Unknown sport type '{sport_type}', keeping original value")
    result = sport_type.lower()

logger.debug(f"Normalized sport: '{sport_type}' -> '{result}'")
return result
```

**Добавлено логирование фильтрации** ([regplace_parser.py:339-368](competitions/regplace_parser.py#L339-L368)):
```python
logger.debug(f"Filtering out '{comp_title}': sport '{comp_sport}' doesn't match '{sport}'")
logger.debug(f"Event '{comp_title}' passed filters (city={city}, sport={sport})")
```

---

#### 3. ✅ Дистанции не отображаются на всех соревнованиях

**Проблема:** Дистанции не показывались для событий от reg.place, хотя логика отображения была реализована.

**Возможные причины:**
- API не возвращает поле `races`
- Поле называется по-другому (`distances`, `items`)
- Внутри race дистанция может быть в полях `distance`, `length`, `distance_km`

**Решение:** Улучшена обработка дистанций ([regplace_parser.py:275-312](competitions/regplace_parser.py#L275-L312))

**Изменения:**

1. **Проверка нескольких возможных полей для списка дистанций:**
```python
races = event.get('races', []) or event.get('distances', []) or event.get('items', [])
```

2. **Проверка нескольких возможных полей для значения дистанции:**
```python
distance = race.get('distance') or race.get('length') or race.get('distance_km')
distance_name = race.get('name', '') or race.get('title', '') or race.get('distance_name', '')
```

3. **Подробное логирование для отладки:**
```python
logger.debug(f"Event '{name}': races field = {bool(event.get('races'))}, distances field = {bool(event.get('distances'))}, items field = {bool(event.get('items'))}")
logger.debug(f"  Race {i}: distance={distance}, name={distance_name}, keys={list(race.keys())}")
logger.debug(f"  ✓ Added distance: {distance_km} km, name: '{distance_name}'")
logger.debug(f"  ✗ Skipping race without distance field: {list(race.keys())}")
logger.info(f"Event '{name}': no races data found in API response")
```

---

## Логи для отладки

### При нормализации спорта:
```
DEBUG:competitions.regplace_parser:Normalized sport: 'running' -> 'run'
DEBUG:competitions.regplace_parser:Normalized sport: 'cycling' -> 'bike'
WARNING:competitions.regplace_parser:Unknown sport type 'orienteering', keeping original value
```

### При фильтрации:
```
DEBUG:competitions.regplace_parser:Filtering out 'Московский марафон': sport 'run' doesn't match 'bike'
DEBUG:competitions.regplace_parser:Event 'Велогонка' passed filters (city=Москва, sport=bike)
```

### При парсинге дистанций:
```
DEBUG:competitions.regplace_parser:Event 'Марафон': races field = True, distances field = False, items field = False
DEBUG:competitions.regplace_parser:Event 'Марафон' has races data: True, type: <class 'list'>, count: 3
DEBUG:competitions.regplace_parser:  Race 0: distance=5000, name=5 км, keys=['distance', 'name', 'price']
DEBUG:competitions.regplace_parser:  ✓ Added distance: 5.0 km, name: '5 км'
DEBUG:competitions.regplace_parser:  Race 1: distance=10000, name=10 км, keys=['distance', 'name', 'price']
DEBUG:competitions.regplace_parser:  ✓ Added distance: 10.0 km, name: '10 км'
INFO:competitions.regplace_parser:Event 'Марафон' parsed with 2 distances (races data: True)
```

### Если дистанции не найдены:
```
DEBUG:competitions.regplace_parser:Event 'Забег': races field = False, distances field = False, items field = False
INFO:competitions.regplace_parser:Event 'Забег': no races data found in API response
INFO:competitions.regplace_parser:Event 'Забег' parsed with 0 distances (races data: False)
```

---

## Тестирование

### Тест 1: Название сервиса
1. Откройте меню фильтра по сервисам
2. **Ожидается:** "Reg.place" с большой буквы

### Тест 2: Фильтрация по виду спорта
1. Выберите фильтр "Бег"
2. **Ожидается:** Только беговые события
3. Проверьте логи на наличие сообщений о фильтрации

### Тест 3: Фильтрация велоспорта
1. Выберите фильтр "Велоспорт"
2. **Ожидается:** Только велосипедные события (не беговые!)
3. Проверьте логи: `Normalized sport: 'cycling' -> 'bike'`

### Тест 4: Дистанции отображаются
1. Откройте любое событие reg.place
2. **Ожидается:** Секция "📏 Дистанции:" со списком
3. Если нет - проверьте логи на наличие информации о парсинге дистанций

### Тест 5: События без дистанций
1. Если событие без дистанций
2. **Ожидается:** Секция "Дистанции" отсутствует (это нормально)
3. Проверьте лог: `Event 'Name': no races data found in API response`

---

## Возможные проблемы и решения

### Проблема: Дистанции все еще не отображаются

**Проверьте логи:**
1. Есть ли сообщение `races field = True` или все False?
2. Если все False - API не возвращает дистанции вообще
3. Если True, но `count: 0` - массив пуст
4. Проверьте ключи race: `keys=[...]`

**Если API не возвращает дистанции:**
- Возможно нужно добавить параметр в запрос (например, `?races=true`)
- Возможно дистанции в отдельном endpoint

### Проблема: Неправильный тип спорта

**Проверьте логи:**
```
WARNING:competitions.regplace_parser:Unknown sport type 'ориентирование', keeping original value
```

**Решение:** Добавьте новое ключевое слово в `normalize_sport_code()`:
```python
elif any(keyword in sport_lower for keyword in ["orient", "ориент"]):
    result = "orienteering"  # или подходящий код
```

### Проблема: Фильтр не работает

**Проверьте логи фильтрации:**
```
DEBUG:competitions.regplace_parser:Filtering out 'Event': sport 'run' doesn't match 'bike'
```

Если такие логи есть - фильтр работает правильно и просто нет подходящих событий.

---

## Файлы изменены

1. ✅ [competitions/competitions_fetcher.py](competitions/competitions_fetcher.py#L121) - название сервиса с большой буквы
2. ✅ [competitions/regplace_parser.py](competitions/regplace_parser.py#L25-L58) - улучшена нормализация спорта
3. ✅ [competitions/regplace_parser.py](competitions/regplace_parser.py#L275-312) - улучшена обработка дистанций
4. ✅ [competitions/regplace_parser.py](competitions/regplace_parser.py#L339-368) - добавлено логирование фильтрации
5. ✅ Синтаксис проверен, ошибок нет

---

## История изменений

- **v4 (2025-12-17):** Исправлены название сервиса, фильтрация спорта, обработка дистанций
- **v3 (2025-12-17):** Добавлено логирование дистанций, исправлена кнопка "Назад"
- **v2 (2025-12-17):** Исправлены URL и фильтр по периоду
- **v1 (2025-12-17):** Первоначальная интеграция reg.place
