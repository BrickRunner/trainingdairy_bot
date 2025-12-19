# Исправление ошибки при отмене регистрации - 19 декабря 2025

## Дата: 2025-12-19

## Проблема

При нажатии кнопки "✅ Да, отменить" в подтверждении отмены регистрации появлялась ошибка:

```
❌ Ошибка при отмене регистрации
```

В консоли показывалось:

```
WARNING:🔵 confirm_cancel_registration called with callback_data: comp:cancel_reg_confirm:150:0.0
WARNING:🔵 confirm_cancel_registration: competition_id=150, distance=0.0
ERROR:confirm_cancel_registration: Failed to cancel registration - ignoring (might be auto-generated callback)
```

**Проблема:** Функция `unregister_from_competition_with_distance()` не могла удалить регистрацию, потому что использовала точное совпадение `distance = ?`, но для reg.place/HeroLeague:
- В callback_data приходит `distance=0.0`
- В базе данных хранится `distance=NULL` или `distance=0`
- SQL запрос `WHERE distance = 0.0` не находит запись с `distance IS NULL`

## Причина

В файле `competitions/competitions_queries.py` функции `unregister_from_competition()` и `update_target_time()` использовали простое сравнение:

```python
WHERE user_id = ? AND competition_id = ? AND distance = ?
```

**Проблема:** В SQL `NULL` не равен ничему, даже `NULL`. Поэтому:
- `distance = 0` НЕ находит записи где `distance IS NULL`
- `distance = 0.0` НЕ находит записи где `distance IS NULL`
- Запрос возвращает 0 строк
- `cursor.rowcount` равен 0
- Функция возвращает `False`
- Показывается ошибка пользователю

## Решение

Добавлена гибкая логика поиска для reg.place/HeroLeague событий, где `distance=0` или `NULL`.

### 1. unregister_from_competition() - строки 279-327

**Было:**
```python
async def unregister_from_competition(
    user_id: int,
    competition_id: int,
    distance: float = None
) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        if distance is not None:
            cursor = await db.execute(
                """
                DELETE FROM competition_participants
                WHERE user_id = ? AND competition_id = ? AND distance = ?
                """,
                (user_id, competition_id, distance)
            )
        else:
            cursor = await db.execute(
                """
                DELETE FROM competition_participants
                WHERE user_id = ? AND competition_id = ?
                """,
                (user_id, competition_id)
            )
        await db.commit()
        return cursor.rowcount > 0
```

**Стало:**
```python
async def unregister_from_competition(
    user_id: int,
    competition_id: int,
    distance: float = None
) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        if distance is not None:
            # Для reg.place/HeroLeague distance может быть 0 или NULL
            # Поэтому используем гибкий поиск
            if distance in (0, 0.0):
                # Для distance=0, ищем записи где distance=0, NULL или не указана
                cursor = await db.execute(
                    """
                    DELETE FROM competition_participants
                    WHERE user_id = ? AND competition_id = ?
                    AND (distance = 0 OR distance IS NULL)
                    """,
                    (user_id, competition_id)
                )
            else:
                # Для обычных дистанций используем точное совпадение
                cursor = await db.execute(
                    """
                    DELETE FROM competition_participants
                    WHERE user_id = ? AND competition_id = ? AND distance = ?
                    """,
                    (user_id, competition_id, distance)
                )
        else:
            cursor = await db.execute(
                """
                DELETE FROM competition_participants
                WHERE user_id = ? AND competition_id = ?
                """,
                (user_id, competition_id)
            )
        await db.commit()
        return cursor.rowcount > 0
```

### 2. update_target_time() - строки 350-393

**Было:**
```python
async def update_target_time(
    user_id: int,
    competition_id: int,
    distance: float,
    target_time: str
) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            UPDATE competition_participants
            SET target_time = ?
            WHERE user_id = ? AND competition_id = ? AND distance = ?
            """,
            (target_time, user_id, competition_id, distance)
        )
        await db.commit()
        return cursor.rowcount > 0
```

**Стало:**
```python
async def update_target_time(
    user_id: int,
    competition_id: int,
    distance: float,
    target_time: str
) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        # Для reg.place/HeroLeague distance может быть 0 или NULL
        # Поэтому используем гибкий поиск
        if distance in (0, 0.0, None):
            # Для distance=0/None, ищем записи где distance=0, NULL или не указана
            cursor = await db.execute(
                """
                UPDATE competition_participants
                SET target_time = ?
                WHERE user_id = ? AND competition_id = ?
                AND (distance = 0 OR distance IS NULL)
                """,
                (target_time, user_id, competition_id)
            )
        else:
            # Для обычных дистанций используем точное совпадение
            cursor = await db.execute(
                """
                UPDATE competition_participants
                SET target_time = ?
                WHERE user_id = ? AND competition_id = ? AND distance = ?
                """,
                (target_time, user_id, competition_id, distance)
            )
        await db.commit()
        return cursor.rowcount > 0
```

## Почему это работает?

**SQL логика для NULL:**

1. **Неправильно (НЕ работает):**
   ```sql
   WHERE distance = 0  -- НЕ находит записи где distance IS NULL
   ```

2. **Правильно (работает):**
   ```sql
   WHERE distance = 0 OR distance IS NULL  -- Находит ОБА случая
   ```

**Логика кода:**

- Если `distance = 0` или `distance = 0.0` → используем гибкий поиск `(distance = 0 OR distance IS NULL)`
- Если `distance` другое значение (например 5.0, 10.0, 21.1) → используем точное совпадение `distance = ?`
- Если `distance = None` в Python → также используем гибкий поиск

**Результат:**

- ✅ Для reg.place/HeroLeague с `distance=NULL` в БД → запрос находит запись
- ✅ Для reg.place/HeroLeague с `distance=0` в БД → запрос находит запись
- ✅ Для обычных соревнований с `distance=5.0, 10.0, 21.1` → запрос работает как раньше
- ✅ Нет конфликта между разными дистанциями одного соревнования

## Результат

✅ **Отмена регистрации** - работает для всех типов соревнований:
- При нажатии "❌ Отменить участие" → показывается подтверждение
- При нажатии "✅ Да, отменить" → регистрация успешно удаляется
- Возврат к списку "✅ Мои соревнования"
- Нет ошибки "❌ Ошибка при отмене регистрации"

✅ **Изменение целевого времени** - также исправлено:
- Функция `update_target_time()` теперь использует ту же логику
- Изменение времени работает для reg.place/HeroLeague

## Файлы изменены

**competitions/competitions_queries.py**
- **Строки 279-327**: `unregister_from_competition()` - добавлена гибкая логика поиска для distance=0/NULL
- **Строки 350-393**: `update_target_time()` - добавлена гибкая логика поиска для distance=0/NULL

## Тестирование

### Сценарий 1: Отмена регистрации на reg.place
1. Зарегистрируйтесь на соревнование reg.place (с вводом дистанции вручную)
2. Откройте "✅ Мои соревнования"
3. Откройте детальную информацию о соревновании
4. Нажмите "❌ Отменить участие"
5. Нажмите "✅ Да, отменить"
6. ✅ Регистрация должна быть успешно отменена
7. ✅ Должно открыться "✅ МОИ СОРЕВНОВАНИЯ"
8. ✅ Нет ошибки

### Сценарий 2: Отмена регистрации на HeroLeague
1. Зарегистрируйтесь на соревнование HeroLeague
2. Откройте "✅ Мои соревнования"
3. Откройте детальную информацию о соревновании
4. Нажмите "❌ Отменить участие"
5. Нажмите "✅ Да, отменить"
6. ✅ Регистрация должна быть успешно отменена
7. ✅ Нет ошибки

### Сценарий 3: Отмена регистрации на RussiaRunning
1. Зарегистрируйтесь на соревнование RussiaRunning (с выбором дистанции из списка)
2. Откройте "✅ Мои соревнования"
3. Откройте детальную информацию о соревновании
4. Нажмите "❌ Отменить участие"
5. Нажмите "✅ Да, отменить"
6. ✅ Регистрация должна быть успешно отменена
7. ✅ Нет ошибки

### Сценарий 4: Изменение целевого времени для reg.place
1. Откройте "✅ Мои соревнования"
2. Откройте детальную информацию о соревновании reg.place
3. Нажмите "✏️ Изменить целевое время"
4. Введите новое время (например "01:30:00")
5. ✅ Время должно быть успешно обновлено
6. ✅ Нет ошибки

---

✅ **Проблема решена!**

**Теперь отмена регистрации и изменение целевого времени работают для всех типов соревнований, включая reg.place и HeroLeague**

## Важный урок

**SQL NULL != любое значение:**
- `NULL = NULL` → `FALSE`
- `NULL = 0` → `FALSE`
- `0 = NULL` → `FALSE`

**Правильная проверка NULL:**
- Используйте `IS NULL` или `IS NOT NULL`
- Для гибкого поиска: `WHERE (column = value OR column IS NULL)`

**Python None vs SQL NULL:**
- В Python: `None == None` → `True`
- В SQL: `NULL = NULL` → `FALSE` (unknown)
- При передаче `None` в SQL через параметры, он становится `NULL`
- Поэтому нужна специальная обработка в SQL запросах
