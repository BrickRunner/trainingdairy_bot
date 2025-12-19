# Исправление отображения дистанций и дат - Версия 2

## Дата: 2025-12-19

## Проблемы

1. **Дистанции**: Много событий показывают "None", "0 ярдов" или "Не указана"
   - Пример из логов: `distance_name='5'` → отображается как "5 мили"
   - Пример: `distance_name='None'` → отображается как "Не указана"

2. **Даты**: Нужно проверить что используется формат из настроек пользователя

---

## Решение

### 1. Улучшена нормализация distance_name

**Проблемы найденные в логах:**
- В БД сохраняются строки "None", "null", "0"
- В БД сохраняются просто числа без единиц: "5", "10", "42.2"

**Файл:** `competitions/competitions_handlers.py` (строки 504-527)

**Добавлена двухэтапная нормализация:**

#### Этап 1: Убираем явные "None", "null", "0"
```python
if distance_name and isinstance(distance_name, str):
    distance_name = distance_name.strip()
    if distance_name.lower() in ('none', 'null', '0', '0.0', ''):
        distance_name = None
```

#### Этап 2: Заменяем просто числа на полные названия из массива distances
```python
elif comp.get('distances') and isinstance(comp['distances'], list):
    import re
    if re.match(r'^\d+(\.\d+)?$', distance_name):
        # Это просто число - ищем в массиве distances
        try:
            num_value = float(distance_name)
            for dist_obj in comp['distances']:
                if dist_obj.get('distance') == num_value:
                    found_name = dist_obj.get('name', '')
                    if found_name and found_name != distance_name:
                        distance_name = found_name  # Заменяем "5" на "5 км"
                    break
        except ValueError:
            pass
```

**Результат:**
- ✅ Строки "None", "null", "0" → обрабатываются как NULL → ищутся в массиве
- ✅ Просто числа "5" → заменяются на "5 км" из массива distances
- ✅ Логика поиска дистанции срабатывает правильно

**Пример до/после:**
```
ДО:  distance_name='5' → "5 мили" (неправильно)
ПОСЛЕ: distance_name='5' → находим '5 км' в массиве → "3.1 миль" (правильно)

ДО:  distance_name='None' → "Не указана"
ПОСЛЕ: distance_name='None' → None → находим в массиве → "10 км"
```

### 2. Улучшено логирование

**Изменения:**
- Строка 512: Изменен уровень на `logger.info` для основной информации
- Строка 540: Изменен на `logger.info` с галочкой ✓
- Добавлено поле `has_distances` в лог

**Пример логов:**
```
INFO: Competition 'Марафон в Москве': distance_value=42.2, distance_name='42.2 км', service='RussiaRunning', has_distances=True
INFO:   ✓ Using distance_name: '42.2 км' -> '42.2 км'

WARNING:   No distance found for competition 'Забег' (distance_value=0, distance_name='None')
```

### 3. Даты уже используют формат из настроек

Проверка показала что функция `format_competition_date` уже корректно учитывает настройки:

**Файл:** `competitions/competitions_utils.py:124-138`

```python
async def format_competition_date(date_str: str, user_id: int) -> str:
    settings = await get_user_settings(user_id)
    date_format = settings.get('date_format', 'ДД.ММ.ГГГГ') if settings else 'ДД.ММ.ГГГГ'
    return DateFormatter.format_date(date_str, date_format)
```

**Используется в:**
- `show_my_competitions()` - строка 551
- `view_my_competition()` - строка 710

**Результат:**
- ✅ Даты уже отображаются в формате из настроек пользователя
- ✅ Показывается только одна дата (дата соревнования)
- ✅ Диапазон дат (начало-конец) не дублируется для однодневных событий

---

## Файлы изменены

1. **`competitions/competitions_handlers.py`** (строки 504-548)
   - Добавлена нормализация `distance_name` в функции `show_my_competitions()`
   - Улучшено логирование

2. **`competitions/competitions_handlers.py`** (строки 712-759)
   - Добавлена такая же нормализация `distance_name` в функции `view_my_competition()`
   - Исправлено отображение "none" в детальной информации при изменении времени и отмене регистрации

---

## Следующие шаги для диагностики

Если проблемы с дистанциями остаются, нужно:

1. **Проверить логи** при открытии "Мои соревнования":
   ```
   INFO: Competition 'Название': distance_value=X, distance_name='Y', service='Z', has_distances=True/False
   INFO:   ✓ Using distance_name: 'X' -> 'Y'
   WARNING:   No distance found for competition ...
   ```

2. **Проверить что сохраняется в БД** при регистрации:
   - Файл: `database/queries.py:986-993`
   - Функция: `add_competition_participant()`
   - Параметры: `distance`, `distance_name`

3. **Проверить что возвращается из парсеров**:
   - HeroLeague: вручную введенная дистанция
   - reg.place: вручную введенная дистанция
   - RussiaRunning/Timerman: дистанция из массива `distances`

---

## Тестирование

### Сценарий 1: Проверка дистанций
1. Откройте "✅ Мои соревнования"
2. Проверьте логи в консоли
3. Для каждого соревнования с "Не указана":
   - Посмотрите строку `INFO: Competition '...'`
   - Проверьте значения `distance_value` и `distance_name`
   - Проверьте есть ли `has_distances=True`

### Сценарий 2: Проверка дат
1. Измените формат даты в настройках (ДД.ММ.ГГГГ / ММ.ДД.ГГГГ)
2. Откройте "✅ Мои соревнования"
3. Убедитесь что даты отображаются в выбранном формате

---

✅ **Нормализация distance_name добавлена в обе функции**
✅ **Исправлено отображение "none" в детальной информации**

**Что исправлено:**
- В функции `show_my_competitions()` - показ списка (строки 504-548)
- В функции `view_my_competition()` - детальная информация (строки 712-759)

**Теперь оба места используют одинаковую логику:**
1. Нормализация "None", "null", "0" → NULL
2. Замена просто чисел на полные названия из массива distances
3. Поиск в массиве distances по значению distance_value
4. Улучшенное логирование с галочкой ✓
