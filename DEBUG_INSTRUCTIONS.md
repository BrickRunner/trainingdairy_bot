# Инструкции по отладке проблемы с сохранением метрик

## Добавлено логирование

Я добавил подробное логирование в следующие функции:

1. **health_handlers.py** - функция `save_and_finish()` (строка 377)
   - Логирует что находится в state перед сохранением
   - Логирует какие параметры передаются в save_health_metrics

2. **health_queries.py** - функция `save_health_metrics()` (строка 16)
   - Логирует все входящие параметры
   - Логирует существует ли уже запись
   - Логирует SQL запросы UPDATE/INSERT
   - Логирует успешность commit

## Как протестировать

1. Запустите бота с логированием:
   ```bash
   python bot.py
   ```

2. Выполните следующие действия в боте:
   - Нажмите "❤️ Здоровье"
   - Нажмите "📝 Внести данные"
   - Введите **пульс** (например, 65)
   - Вернитесь в меню "📝 Внести данные"
   - Введите **вес** (например, 72)
   - Проверьте сохранились ли оба значения

3. Смотрите логи в консоли - они покажут:
   - Что находится в state при сохранении
   - Какие параметры передаются в БД
   - Какой SQL запрос выполняется
   - Успешен ли commit

## Что искать в логах

### При сохранении пульса (первый раз):
```
INFO: save_and_finish: data from state = {'pulse': 65, 'quick_input': 'pulse'}
INFO: save_and_finish: save_params = {'user_id': XXX, 'metric_date': 'YYYY-MM-DD', 'morning_pulse': 65}
INFO: save_health_metrics called: user_id=XXX, date=YYYY-MM-DD, pulse=65, weight=None, sleep=None
INFO: Existing record: None
INFO: INSERT new record with values: pulse=65, weight=None, sleep=None
INFO: Commit successful
```

### При сохранении веса (второй раз):
```
INFO: save_and_finish: data from state = {'weight': 72.0, 'quick_input': 'weight'}
INFO: save_and_finish: save_params = {'user_id': XXX, 'metric_date': 'YYYY-MM-DD', 'weight': 72.0}
INFO: save_health_metrics called: user_id=XXX, date=YYYY-MM-DD, pulse=None, weight=72.0, sleep=None
INFO: Existing record: (1,)
INFO: UPDATE query: UPDATE health_metrics SET weight = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND date = ?
INFO: UPDATE params: [72.0, XXX, 'YYYY-MM-DD']
INFO: Commit successful
```

## Пришлите мне логи

После тестирования пришлите мне логи из консоли, особенно:
1. Что показывается при сохранении пульса
2. Что показывается при сохранении веса
3. Есть ли ошибки

Это поможет точно определить где проблема!
