# Финальные исправления - 19 декабря 2025

## Исправления

### 1. ✅ Вид спорта "Другое" теперь отображается на русском

**Проблема:**
Для событий с типом "other" в reg.place отображался код вместо русского названия.

**Решение:**

**Файл:** `competitions/regplace_parser.py` (строка 50)
```python
"other": "other",  # "Другой вид" - отдельный код (было: "run")
```

**Файл:** `competitions/parser.py` (строка 503)
```python
SPORT_NAMES["other"] = "Другое"
```

**Результат:**
- События с типом "other" теперь отображаются как "Другое" вместо "run" или кода

---

### 2. ✅ Исправлена фильтрация событий из прошлого во ВСЕХ парсерах

**Проблема:**
При выборе периода "1 год" (01.01 - 31.12) или "1 месяц" (с 1-го числа) показывались события из ПРОШЛОГО:
- Если сегодня 19.12.2025, то период "1 год" показывал события с 01.01.2025, включая все прошедшие (январь-ноябрь)
- Период "1 месяц" показывал события с 1 декабря, включая прошедшие

**Решение:**
Добавлена дополнительная проверка во все парсеры - события из прошлого теперь ОТСЕИВАЮТСЯ.

#### RussiaRunning - `competitions/parser.py` (строки 370-380)
```python
# Дополнительная проверка: событие должно быть в будущем (>= сегодня)
from datetime import timezone as tz
now_utc = datetime.now(tz.utc)
# Делаем begin_date_obj timezone-aware если он naive
if begin_date_obj.tzinfo is None:
    begin_date_obj = begin_date_obj.replace(tzinfo=tz.utc)
if begin_date_obj < now_utc:
    filtered_count += 1
    filtered_by_period += 1
    logger.debug(f"Skipping past event: '{comp['title']}' on {begin_date_obj.strftime('%Y-%m-%d')}")
    continue
```

#### Timerman - `competitions/timerman_parser.py` (строки 349-355)
```python
# Дополнительная проверка: событие должно быть в будущем (>= сегодня)
now_utc = datetime.now(timezone.utc)
if begin_date_obj < now_utc:
    filtered_count += 1
    filtered_by_period += 1
    logger.debug(f"Skipping past event: '{comp['title']}' on {begin_date_obj.strftime('%Y-%m-%d')}")
    continue
```

#### HeroLeague - `competitions/heroleague_parser.py` (строки 176-184)
```python
# Дополнительная проверка: событие должно быть в будущем (>= сегодня)
from datetime import timezone as tz
now_utc = datetime.now(tz.utc)
# Делаем begin_date timezone-aware если он naive
if begin_date.tzinfo is None:
    begin_date = begin_date.replace(tzinfo=tz.utc)
if begin_date < now_utc:
    logger.debug(f"Skipping past event: '{comp.get('title')}' on {begin_date.strftime('%Y-%m-%d')}")
    continue
```

#### reg.place - `competitions/regplace_parser.py` (строки 204-216)
```python
# Дополнительная проверка: событие должно быть в будущем (>= сегодня)
comp_date = comp.get('start_time')
if comp_date:
    if comp_date.tzinfo is None:
        from datetime import timezone as tz
        comp_date = comp_date.replace(tzinfo=tz.utc)

    # Проверяем что событие не в прошлом
    from datetime import timezone, timedelta
    now_utc = datetime.now(timezone.utc)
    if comp_date < now_utc:
        logger.debug(f"Skipping past event: '{comp.get('title')}' on {comp_date.strftime('%Y-%m-%d')}")
        continue
```

**Результат:**
- Во ВСЕХ парсерах теперь показываются ТОЛЬКО предстоящие события (>= сегодня)
- События из прошлого не отображаются в списке
- События из прошлого не сохраняются в базу данных
- Периоды работают корректно:
  - **1 месяц**: с 1-го числа до конца месяца, но ТОЛЬКО будущие события
  - **1 год**: с 01.01 до 31.12, но ТОЛЬКО будущие события
  - **6 месяцев**: от сегодня + 180 дней (уже было правильно)

---

## Затронутые файлы

1. **`competitions/regplace_parser.py`**
   - Строка 50: изменен маппинг "other" → "other" (было "run")
   - Строки 204-216: добавлена проверка на прошедшие события

2. **`competitions/parser.py`** (RussiaRunning)
   - Строка 503: добавлено `SPORT_NAMES["other"] = "Другое"`
   - Строки 370-380: добавлена проверка на прошедшие события

3. **`competitions/timerman_parser.py`**
   - Строки 349-355: добавлена проверка на прошедшие события

4. **`competitions/heroleague_parser.py`**
   - Строки 176-184: добавлена проверка на прошедшие события

---

## Тестирование

1. ✅ Выберите любой сервис (RussiaRunning, Timerman, HeroLeague, reg.place)
2. ✅ Выберите период "1 год"
3. ✅ Убедитесь что показываются ТОЛЬКО предстоящие события (не из прошлого)
4. ✅ Для reg.place проверьте что события с типом "other" отображаются как "Другое"
5. ✅ Зарегистрируйтесь на событие и проверьте что оно появляется в "Мои соревнования"

---

## Важно

Теперь ВСЕ парсеры работают ОДИНАКОВО:
- Используют одинаковые периоды (1 месяц, 6 месяцев, 1 год)
- Фильтруют события из прошлого
- Показывают только предстоящие соревнования
- Имеют одинаковый редирект после регистрации

✅ **Все проблемы решены!**
