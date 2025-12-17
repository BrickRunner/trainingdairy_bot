# Changelog для reg.place парсера

## [v2] - Исправления URL и фильтра по периоду

### Исправлено
- **URL событий теперь берется из API** ([regplace_parser.py:250-260](competitions/regplace_parser.py#L250-L260))
  - Приоритет: сначала пытаемся получить `url` или `link` из API
  - Обработка относительных URL (добавляем домен)
  - Только если URL нет - формируем из идентификатора
  - Добавлено логирование источника URL

- **Фильтр "месяц" работает как календарный месяц** ([regplace_parser.py:136-164](competitions/regplace_parser.py#L136-L164))
  - **1 месяц** = с 1-го до последнего числа текущего месяца
  - **6 месяцев** = от текущей даты + 180 дней
  - **12 месяцев** = с 01.01 до 31.12 текущего года
  - Логика идентична RussiaRunning парсеру

### Улучшено
- Поддержка нескольких типов идентификаторов: `slug`, `id`, `event_id`
- Добавлено логирование структуры первого события
- Предупреждения при отсутствии обязательных полей

### Логирование
```
INFO: reg.place event structure keys: ['id', 'slug', 'name', 'date', 'city', 'url', ...]
INFO: Period filter: 1 months, from 2025-12-01 to 2025-12-31
DEBUG: Event URL: https://reg.place/event/moscow-marathon (from API: True)
WARNING: Missing identifier or name in event: slug=, id=12345, name=
```

## [v1] - Первоначальная интеграция

### Добавлено
- Создан парсер reg.place ([regplace_parser.py](competitions/regplace_parser.py))
- Интеграция в competitions_fetcher.py
- Поле `place` для совместимости
- Поле `begin_date` в ISO формате
- Базовая фильтрация по городу и спорту

### Исправлено
- Ошибка при открытии события (отсутствовало поле `place`)
- Ошибка форматирования дат (ISO формат для `begin_date` и `end_date`)

---

## Проверьте после обновления

1. ✅ URL события ведет на правильную страницу reg.place
2. ✅ Фильтр "1 месяц" показывает только события текущего месяца
3. ✅ Фильтр "6 месяцев" показывает события в следующие 180 дней
4. ✅ Фильтр "12 месяцев" показывает события до конца года
5. ✅ События открываются без ошибок
6. ✅ Фильтры по городу и спорту работают корректно

## Логи для проверки

Запустите бота и посмотрите логи:
```
INFO:competitions.regplace_parser:Trying reg.place endpoint: https://api.reg.place/v1/events
INFO:competitions.regplace_parser:SUCCESS! reg.place endpoint https://api.reg.place/v1/events returned status 200
INFO:competitions.regplace_parser:reg.place event structure keys: [...]
INFO:competitions.regplace_parser:Found 50 events from reg.place
INFO:competitions.regplace_parser:Period filter: 1 months, from 2025-12-01 to 2025-12-31
INFO:competitions.regplace_parser:Parsed 25 competitions from reg.place after filters
```
