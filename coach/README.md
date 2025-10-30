# Модуль "Тренер"

Модуль для работы с тренерами и учениками в Training Diary Bot.

## Функциональность

### Для тренеров:
- ✅ Включение режима тренера в настройках
- ✅ Получение уникального кода/ссылки для подключения учеников
- ✅ Просмотр списка своих учеников
- ✅ Просмотр информации о конкретном ученике
- ✅ Удаление ученика из списка
- 🔄 Просмотр тренировок ученика (в разработке)
- 🔄 Просмотр статистики ученика (в разработке)
- 🔄 Просмотр данных о здоровье ученика (в разработке)

### Для учеников:
- ✅ Подключение к тренеру по коду или ссылке
- ✅ Просмотр информации о своём тренере
- ✅ Отключение от тренера
- 🔄 Тренер видит тренировки ученика

## Структура модуля

```
coach/
├── __init__.py              # Инициализация модуля
├── coach_queries.py         # Запросы к БД
├── coach_keyboards.py       # Клавиатуры интерфейса
├── coach_handlers.py        # Обработчики событий
└── README.md               # Документация
```

## База данных

### Таблица `user_settings`
Добавлены поля:
- `is_coach` (BOOLEAN) - является ли пользователь тренером
- `coach_link_code` (TEXT UNIQUE) - уникальный код для подключения учеников

### Таблица `coach_links`
```sql
CREATE TABLE coach_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coach_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    status TEXT DEFAULT 'active',  -- 'active', 'pending', 'removed'
    link_code TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    removed_at TIMESTAMP,
    UNIQUE(coach_id, student_id)
)
```

## Как использовать

### Стать тренером:
1. Перейти в ⚙️ Настройки
2. Нажать "❌ Режим тренера" (переключится на "✅ Режим тренера")
3. Получить код для учеников
4. В главном меню появится кнопка "👨‍🏫 Тренер"

### Подключиться к тренеру (ученик):
1. Перейти в ⚙️ Настройки
2. Нажать "👨‍🏫 Мой тренер"
3. Нажать "✏️ Ввести код тренера"
4. Ввести код, полученный от тренера

Альтернативно: перейти по ссылке вида `https://t.me/botname?start=coach_XXXXXXXX`

## API функций

### coach_queries.py

```python
async def set_coach_mode(user_id: int, is_coach: bool) -> str:
    """Включить/выключить режим тренера"""

async def is_user_coach(user_id: int) -> bool:
    """Проверить, является ли пользователь тренером"""

async def get_coach_link_code(user_id: int) -> Optional[str]:
    """Получить код тренера для подключения учеников"""

async def find_coach_by_code(link_code: str) -> Optional[int]:
    """Найти тренера по коду"""

async def add_student_to_coach(coach_id: int, student_id: int) -> bool:
    """Добавить ученика к тренеру"""

async def remove_student_from_coach(coach_id: int, student_id: int) -> bool:
    """Удалить ученика от тренера"""

async def get_coach_students(coach_id: int) -> List[Dict[str, Any]]:
    """Получить список учеников тренера"""

async def get_student_coach(student_id: int) -> Optional[Dict[str, Any]]:
    """Получить тренера ученика"""

async def remove_coach_from_student(student_id: int) -> bool:
    """Ученик отключается от тренера"""
```

## FSM States

```python
class CoachStates(StatesGroup):
    waiting_for_coach_code = State()  # Ввод кода тренера
```

## Интеграция

### main.py
```python
from coach.coach_handlers import router as coach_router
dp.include_router(coach_router)
```

### bot/handlers.py
```python
@router.message(F.text == "👨‍🏫 Тренер")
async def show_coach_section(message: Message):
    """Обработчик кнопки Тренер"""
```

### settings/settings_handlers_full.py
```python
@router.callback_query(F.data == "settings:coach_mode")
async def toggle_coach_mode(callback: CallbackQuery):
    """Переключение режима тренера"""
```

## Миграция

Для применения изменений в БД:
```bash
python migrate_coach_mode.py
```

## Планы на будущее

- [ ] Добавить возможность тренеру создавать тренировочные планы для учеников
- [ ] Добавить комментарии тренера к тренировкам ученика
- [ ] Добавить систему уведомлений (тренер → ученик)
- [ ] Добавить аналитику прогресса ученика
- [ ] Добавить возможность группировать учеников
- [ ] Добавить чат тренер-ученик

## Примечания

- Один ученик может быть связан только с одним тренером
- Тренер может иметь неограниченное количество учеников
- Код тренера генерируется автоматически при включении режима (8 символов, буквы+цифры)
- При отключении режима тренера код сохраняется (можно снова включить)
