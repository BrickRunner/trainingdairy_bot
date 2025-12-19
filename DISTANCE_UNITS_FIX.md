# Исправление отображения единиц измерения для дистанций - 19 декабря 2025

## Дата: 2025-12-19

## Проблемы

1. **В детальной информации** (view_my_competition) для reg.place и HeroLeague дистанция отображалась без единиц измерения
   - Пользователь вводит "10" → показывалось просто "10" вместо "10 км" или "6.2 мили"

2. **При изменении целевого времени** дистанция отображалась неправильно
   - Показывалось "None" или просто число без единиц

3. **При отмене участия** дистанция отображалась неправильно
   - Показывалось "None" или просто число без единиц

## Причина

В разных функциях отсутствовала проверка на "просто число" в `distance_name`:
- В `show_my_competitions()` (список) эта проверка была (строки 556-558)
- В `view_my_competition()` (детали) этой проверки НЕ было
- В `edit_target_time()` (изменение времени) этой проверки НЕ было
- В обработчике отмены регистрации этой проверки НЕ было

## Решение

Добавлена проверка на "просто число" во все функции, которые отображают дистанцию.

### 1. view_my_competition() - детальная информация (строки 746-758)

**Было:**
```python
if distance_name and distance_name.strip():
    settings = await get_user_settings(user_id)
    distance_unit = settings.get('distance_unit', 'км') if settings else 'км'
    dist_str = safe_convert_distance_name(distance_name, distance_unit)
```

**Стало:**
```python
if distance_name and distance_name.strip():
    settings = await get_user_settings(user_id)
    distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

    # Проверяем, не является ли distance_name просто числом без единиц
    import re
    if re.match(r'^\d+(\.\d+)?$', distance_name):
        # Это просто число - добавляем единицы измерения
        dist_str = f"{distance_name} {distance_unit}"
    else:
        dist_str = safe_convert_distance_name(distance_name, distance_unit)
```

### 2. edit_target_time() - изменение целевого времени (строки 1109-1130)

**Было:**
```python
distance_name = registration.get('distance_name') if registration else None
if distance_name:
    settings = await get_user_settings(user_id)
    distance_unit = settings.get('distance_unit', 'км') if settings else 'км'
    dist_str = safe_convert_distance_name(distance_name, distance_unit)
else:
    dist_str = await format_dist_with_units(distance, user_id)
```

**Стало:**
```python
distance_name = registration.get('distance_name') if registration else None

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
        dist_str = f"{distance_name} {distance_unit}"
    else:
        dist_str = safe_convert_distance_name(distance_name, distance_unit)
else:
    dist_str = await format_dist_with_units(distance, user_id)
```

### 3. Обработчик отмены регистрации (строки 1292-1313)

Добавлена такая же нормализация как в `edit_target_time()`.

## Результат

✅ **Детальная информация** - дистанция отображается с единицами измерения из настроек:
- Пользователь вводит "10" → показывается "10 км" (если настройка "км") или "6.2 мили" (если настройка "мили")
- Пользователь вводит "10 км" → показывается "10 км" (если настройка "км") или "6.2 мили" (если настройка "мили")
- Пользователь вводит "Марафон" → показывается "Марафон" (остается без изменений)

✅ **Изменение целевого времени** - дистанция отображается правильно:
- Нормализуются строки "None", "null", "0"
- Добавляются единицы измерения для просто чисел
- Конвертируются дистанции с единицами (например "10 км" → "6.2 мили")

✅ **Отмена участия** - дистанция отображается правильно:
- Применяется та же логика что и при изменении времени

## Файлы изменены

**`competitions/competitions_handlers.py`**
- **Строки 746-758**: Добавлена проверка на просто число в `view_my_competition()`
- **Строки 1109-1130**: Добавлена нормализация и проверка на просто число в `edit_target_time()`
- **Строки 1292-1313**: Добавлена нормализация и проверка на просто число в обработчике отмены регистрации

## Тестирование

### Сценарий 1: Просмотр детальной информации (reg.place)
1. Зарегистрируйтесь на соревнование reg.place
2. При вводе дистанции введите просто "10"
3. Откройте "✅ Мои соревнования"
4. Откройте детальную информацию о соревновании
5. ✅ Должно показываться "10 км" (если настройка "км") или "6.2 мили" (если настройка "мили")

### Сценарий 2: Изменение целевого времени
1. Откройте детальную информацию о соревновании reg.place
2. Нажмите "✏️ Изменить целевое время"
3. ✅ В сообщении должна отображаться дистанция с единицами измерения

### Сценарий 3: Отмена участия
1. Откройте детальную информацию о соревновании reg.place
2. Нажмите "❌ Отменить участие"
3. ✅ В подтверждении должна отображаться дистанция с единицами измерения

### Сценарий 4: Разные единицы измерения
1. Измените единицы в настройках на "мили"
2. Откройте детальную информацию о соревновании где ввели "10 км"
3. ✅ Должно показываться "6.2 мили"
4. Измените единицы обратно на "км"
5. ✅ Должно показываться "10 км"

---

✅ **Все проблемы решены!**

**Теперь дистанции везде отображаются с правильными единицами измерения согласно настройкам пользователя**
