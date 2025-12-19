# Исправление редиректов и отображения дистанций - 19 декабря 2025

## Дата: 2025-12-19

## Проблемы

1. **Неправильный редирект после регистрации**
   - После ввода целевого времени пользователя перенаправляло в главное меню соревнований
   - Должно перенаправлять в "Мои соревнования"

2. **Дистанция не отображается при изменении целевого времени**
   - В разделе "Мои соревнования" после изменения времени дистанция отображалась неправильно
   - Показывалось просто число или "None" вместо дистанции с единицами измерения

## Причина

### Проблема 1: Редирект
После последних изменений (NAVIGATION_REDIRECT_FIX.md) редирект был изменен на `show_competitions_menu()`, но правильное поведение - перенаправлять в `show_my_competitions()`.

**Затронутые функции:**
- `save_all_distances_and_redirect()` - строки 1144-1188
- `skip_target_time()` - строки 1404-1409
- `process_target_time()` - строки 1647-1676

### Проблема 2: Отображение дистанции
В функции `process_target_time_edit()` (обработчик изменения целевого времени в разделе "Мои соревнования") использовалось числовое значение `distance` вместо `distance_name`, и не применялась нормализация.

**Строка 1216:** `distance_str = await format_dist_with_units(distance, user_id)`

Для reg.place и HeroLeague `distance` может быть 0, а реальная дистанция в `distance_name`.

## Решение

### 1. Исправлены редиректы после регистрации

Изменено на использование `show_my_competitions()` вместо `show_competitions_menu()` в трех функциях:

#### save_all_distances_and_redirect() (строки 1144-1188)

**Было:**
```python
from competitions.competitions_handlers import show_competitions_menu
await show_competitions_menu(callback_or_message, state)
```

**Стало:**
```python
from competitions.competitions_handlers import show_my_competitions
await show_my_competitions(callback_or_message, state)
```

#### skip_target_time() (строки 1404-1409)

**Было:**
```python
from competitions.competitions_handlers import show_competitions_menu
await show_competitions_menu(callback, state)
```

**Стало:**
```python
from competitions.competitions_handlers import show_my_competitions
await show_my_competitions(callback, state)
```

#### process_target_time() (строки 1647-1676)

**Было:**
```python
from competitions.competitions_handlers import show_competitions_menu
await show_competitions_menu(fake_callback, state)
```

**Стало:**
```python
from competitions.competitions_handlers import show_my_competitions
await show_my_competitions(fake_callback, state)
```

### 2. Улучшена логика поиска регистрации

В функциях `edit_target_time()` и `cancel_registration()` добавлена улучшенная логика поиска регистрации:

**Было:**
```python
registration = None
for comp in user_comps:
    if comp['id'] == competition_id and comp.get('distance') == distance:
        registration = comp
        break
```

**Проблема:** Для reg.place/HeroLeague `distance` может быть 0 или None, поэтому регистрация не находилась.

**Стало:**
```python
# Находим нужную регистрацию
# Для HeroLeague/reg.place distance может быть None или 0, поэтому ищем более гибко
registration = None
for comp in user_comps:
    comp_distance = comp.get('distance')
    if comp['id'] == competition_id:
        # Если обе дистанции None или 0, считаем совпадением
        if (comp_distance == distance) or \
           (comp_distance in (None, 0) and distance in (None, 0)):
            registration = comp
            break

if not registration:
    # Если не нашли с точным совпадением дистанции, попробуем найти по ID
    # (для случаев когда у соревнования только одна регистрация)
    registrations_for_comp = [c for c in user_comps if c['id'] == competition_id]
    if len(registrations_for_comp) == 1:
        registration = registrations_for_comp[0]
    else:
        await callback.answer("❌ Регистрация не найдена", show_alert=True)
        return
```

### 3. Исправлено отображение дистанции при изменении времени

В функции `process_target_time_edit()` (строки 1211-1242) добавлена нормализация `distance_name`:

**Было:**
```python
distance_str = await format_dist_with_units(distance, user_id)
```

**Стало:**
```python
# Получаем distance_name из participant
distance_name = participant.get('distance_name')

# Нормализация distance_name
if distance_name and isinstance(distance_name, str):
    distance_name = distance_name.strip()
    if distance_name.lower() in ('none', 'null', '0', '0.0', ''):
        distance_name = None

if distance_name and distance_name.strip():
    settings = await get_user_settings(user_id)
    distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

    # Проверяем, не является ли distance_name просто числом без единиц
    import re
    if re.match(r'^\d+(\.\d+)?$', distance_name):
        # Это просто число - добавляем единицы измерения
        distance_str = f"{distance_name} {distance_unit}"
    else:
        distance_str = safe_convert_distance_name(distance_name, distance_unit)
else:
    distance_str = await format_dist_with_units(distance, user_id)
```

## Результат

✅ **Редирект после регистрации** - пользователь попадает в "Мои соревнования":
- После ввода целевого времени → "✅ Мои соревнования"
- После пропуска целевого времени → "✅ Мои соревнования"
- После регистрации на несколько дистанций → "✅ Мои соревнования"

✅ **Отображение дистанции при изменении времени** - дистанция показывается правильно:
- Нормализуются строки "None", "null", "0"
- Добавляются единицы измерения для просто чисел ("10" → "10 км")
- Конвертируются дистанции с единицами ("10 км" → "6.2 мили" если настройка "мили")

## Файлы изменены

### competitions/upcoming_competitions_handlers.py
- **Строки 1144-1188**: `save_all_distances_and_redirect()` - изменен редирект на `show_my_competitions()`
- **Строки 1404-1409**: `skip_target_time()` - изменен редирект на `show_my_competitions()`
- **Строки 1647-1676**: `process_target_time()` - изменен редирект на `show_my_competitions()`

### competitions/competitions_handlers.py
- **Строки 1088-1114**: `edit_target_time()` - улучшена логика поиска регистрации для reg.place/HeroLeague
- **Строки 1211-1242**: `process_target_time_edit()` - добавлена нормализация `distance_name` при отображении дистанции
- **Строки 1302-1327**: `cancel_registration()` - улучшена логика поиска регистрации для reg.place/HeroLeague

## Тестирование

### Сценарий 1: Редирект после регистрации (RussiaRunning)
1. Найдите соревнование RussiaRunning с одной дистанцией
2. Нажмите "✅ Я участвую"
3. Введите целевое время
4. ✅ Должно открыться "✅ МОИ СОРЕВНОВАНИЯ" (список зарегистрированных соревнований)

### Сценарий 2: Редирект после регистрации (reg.place)
1. Найдите соревнование reg.place
2. Нажмите "✅ Я участвую"
3. Введите дистанцию (например "10 км")
4. Введите целевое время
5. ✅ Должно открыться "✅ МОИ СОРЕВНОВАНИЯ"

### Сценарий 3: Редирект при пропуске времени
1. Найдите любое соревнование
2. Нажмите "✅ Я участвую"
3. Выберите дистанцию (если нужно)
4. Нажмите "Пропустить" при вводе времени
5. ✅ Должно открыться "✅ МОИ СОРЕВНОВАНИЯ"

### Сценарий 4: Отображение дистанции при изменении времени
1. Откройте "✅ Мои соревнования"
2. Откройте детальную информацию о соревновании reg.place (где вводили дистанцию вручную)
3. Нажмите "✏️ Изменить целевое время"
4. ✅ В сообщении должна отображаться дистанция с единицами измерения (например "10 км")
5. Введите новое время
6. ✅ В карточке соревнования должна отображаться дистанция с единицами

---

✅ **Все проблемы решены!**

**Теперь:**
- Редирект после регистрации ведет в "Мои соревнования" (как и должно быть)
- Дистанции отображаются правильно при изменении целевого времени
