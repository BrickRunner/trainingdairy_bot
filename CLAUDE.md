# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Trainingdiary_bot** is a Telegram bot for tracking athletic training, built with Python 3 and aiogram 3. It helps athletes log workouts, track health metrics, register for competitions, and connect with coaches. The bot supports running, swimming, cycling, strength training, and triathlon activities.

## Development Commands

### Running the Bot
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Unix/macOS

# Run the bot
python main.py
```

### Database Operations
```bash
# Initialize database (creates tables from database/models.py)
# The bot auto-initializes on startup, but you can also use:
python -c "import asyncio; from database.queries import init_db; asyncio.run(init_db())"

# Database location: database.sqlite (configurable via DB_PATH env var)
```

### Testing
```bash
# Run pytest tests
pytest

# With coverage
pytest --cov

# Syntax check a module
python -m py_compile path/to/module.py
```

### Code Quality
```bash
# Format code
black .

# Lint
flake8

# Type checking
mypy .
```

## Architecture

### Router Registration Order (CRITICAL)

The order of router registration in `main.py` is **critical** due to callback handler specificity. More specific routers MUST be registered before generic ones to prevent callback interception:

```python
dp.include_router(upcoming_competitions_router)  # FIRST - most specific
dp.include_router(registration_router)
dp.include_router(settings_router)  # Has cal_birth_ callbacks
dp.include_router(competitions_statistics_router)
dp.include_router(coach_router)
dp.include_router(coach_add_training_router)
dp.include_router(coach_competitions_router)  # BEFORE custom!
dp.include_router(competitions_router)
dp.include_router(custom_competitions_router)
dp.include_router(search_competitions_router)
dp.include_router(health_calendar_export_router)
dp.include_router(health_router)
dp.include_router(ratings_router)
dp.include_router(router)  # LAST - general commands
```

**Why this matters**: If a generic router is registered before a specific one, it may handle callbacks meant for the specific router, causing incorrect behavior or navigation issues.

### Core Modules

- **`main.py`**: Entry point; initializes bot, registers routers, starts schedulers
- **`bot/`**: Main bot functionality (handlers, keyboards, FSM states, graphs, PDF export)
- **`database/`**: SQLite database layer (models, queries, rating queries, level queries)
- **`competitions/`**: Competition management system (registration, results, search, statistics)
- **`coach/`**: Coach-student relationship management
- **`health/`**: Health metrics tracking (pulse, weight, sleep, mood)
- **`ratings/`**: User rating system and leaderboards
- **`registration/`**: New user onboarding flow
- **`settings/`**: User settings and preferences
- **`notifications/`**: Background notification scheduler system
- **`utils/`**: Shared utilities (time formatting, unit conversion, qualifications, goals)
- **`analytics/`**: Training statistics and analysis

### Database Schema

The database uses SQLite with the following key tables (see `database/models.py`):

- **`users`**: User profiles
- **`trainings`**: Training log entries (supports coach-added trainings with `added_by_coach_id`)
- **`competitions`**: Competition catalog (official + user-created)
- **`competition_participants`**: User registrations with distance selection, target times, results
- **`competition_reminders`**: Scheduled reminders (7 days, 3 days, 1 day before)
- **`personal_records`**: User PRs by distance
- **`health_metrics`**: Daily health tracking (pulse, weight, sleep, mood, stress, energy)
- **`user_settings`**: User preferences, goals, units, timezone, pulse zones
- **`coach_links`**: Coach-student relationships with unique link codes
- **`training_comments`**: Coach feedback on student trainings
- **`ratings`**: User ranking system

**Important**: The `competition_participants` table has a `UNIQUE(competition_id, user_id, distance, distance_name)` constraint, allowing users to register for multiple distances within the same competition.

### FSM (Finite State Machine)

The bot uses aiogram's FSM for multi-step interactions (see `bot/fsm.py`):

- **`RegistrationStates`**: New user registration flow
- **`AddTrainingStates`**: Training entry with type-specific fields (swimming has pool_length, styles, sets; strength has exercises; intervals has intervals description)
- **`SettingsStates`**: User preferences modification
- **`CompetitionStates`**: Competition registration, result entry, search, custom creation
- **`CoachStates`**: Coach-student interactions, training assignment
- **`ExportPDFStates`**: Date range selection for PDF reports

### Competition Data Sources

The bot integrates with multiple competition APIs:

1. **Russia Running API** (`competitions/parser.py`): Primary source for Russian running events
2. **Timerman API** (`competitions/timerman_parser.py`): Additional Russian events
3. **HeroLeague API** (`competitions/heroleague_parser.py`): Triathlon/multisport events
4. **RegPlace** (`competitions/regplace_parser.py`): Regional competitions
5. **User-created competitions** (`competitions/custom_competitions_handlers.py`): Manual entry

**Sport code normalization**: All parsers normalize sport types to: `run`, `bike`, `swim`, `triathlon`. See `SPORT_CODE_NORMALIZATION.md` for mapping details.

**Distance handling**: Some competitions (e.g., HeroLeague) have complex distances like "акватлон (0.5км плавание + 5км бег)". These are stored with both `distance` (numeric km) and `distance_name` (descriptive string).

### Background Schedulers

Multiple async schedulers run continuously (started in `main.py`):

1. **`notification_scheduler`** (`notifications/notification_scheduler.py`): Daily pulse/weight reminders, weekly reports, training reminders
2. **`birthday_checker`** (`utils/birthday_checker.py`): Daily birthday greetings at 9 AM
3. **`rating_updater`** (`ratings/rating_updater.py`): Weekly rating recalculation
4. **`competition_reminders`** (`competitions/reminder_scheduler.py`): Competition reminders (7d, 3d, 1d before)
5. **`qualifications_checker`** (`utils/qualifications_scheduler.py`): Monthly check for EVSK standard updates

### Unit System

The bot supports both metric and imperial units:

- **Distance**: km ↔ miles (see `utils/unit_converter.py`)
- **Weight**: kg ↔ pounds
- **Pace**: Automatically calculated and converted based on user preference
- **Swimming pace**: Special handling for min/100m (see `utils/swimming_pace.py`)

User preference stored in `user_settings.distance_unit` and `user_settings.weight_unit`.

### Qualifications System

Russian EVSK athletic standards (see `utils/qualifications.py`):

- Standards for run, swim, bike across distances (5K, 10K, 21.1K, 42.195K, etc.)
- Gender-specific times for: МС (Master of Sport), КМС (Candidate Master), I разряд, II разряд, III разряд
- Automatically calculates qualification when user adds competition result
- Stores in `competition_participants.qualification`

## Common Patterns

### Callback Query Naming Convention

Callbacks follow a hierarchical pattern for navigation:

- `comp:menu` - Return to competitions menu
- `comp:upcoming` - Show upcoming competitions
- `comp:{comp_id}:register` - Register for competition
- `comp:{comp_id}:distance:{idx}` - Select distance
- `health:menu` - Health section menu
- `settings:profile` - Settings profile section

### Database Queries

All database operations are async and use context managers:

```python
async with aiosqlite.connect(DB_PATH) as db:
    db.row_factory = aiosqlite.Row  # For dict-like results
    async with db.execute("SELECT ...", (params,)) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
```

### Time Formatting

Use `utils/time_formatter.py` for consistent time handling:

- `normalize_time(user_input)`: Converts various formats to HH:MM:SS
- `format_pace(seconds_per_km, unit)`: Converts seconds to pace string
- Supports both "01:30:45" and "1:30:45" formats

### Graph Generation

The bot generates training graphs using matplotlib/plotly:

- **Matplotlib** (`bot/graphs.py`): Static graphs for volume, pace trends
- **Plotly** (`bot/pdf_graphs.py`): Interactive graphs embedded in PDFs
- All graphs support both metric and imperial units based on user settings

### PDF Export

Multiple modules generate PDF reports:

- `bot/pdf_export.py`: Training diary exports
- `competitions/competitions_pdf_export.py`: Competition preparation reports
- `health/health_pdf_export.py`: Health metrics reports

PDFs use `reportlab` and include graphs, tables, and localized date formatting.

## Common Development Tasks

### Adding a New Training Type

1. No code changes needed - training types are user-configurable
2. Update `user_settings.main_training_types` JSON array
3. FSM in `AddTrainingStates` handles all types via conditional fields

### Adding a New Competition Source

1. Create parser in `competitions/{source}_parser.py`
2. Implement `fetch_competitions(city=None, sport=None, start_date=None)` function
3. Normalize sport codes to: `run`, `bike`, `swim`, `triathlon`
4. Return list of dicts with: `title`, `begin_date`, `city`, `place`, `distances`, `sport_code`, `url`
5. Integrate into `competitions/upcoming_competitions_handlers.py`

### Modifying Database Schema

1. Update table definition in `database/models.py`
2. Database auto-creates on init, but existing databases need migration
3. Write migration script (see `archive/old_migrations/` for examples)
4. Test migration on copy of production database

### Adding Background Notifications

1. Create notification function in `notifications/`
2. Add scheduler in module (see `notification_scheduler.py` pattern)
3. Register in `main.py` with `asyncio.create_task()`
4. Use `user_settings` table to check user preferences before sending

## Environment Variables

Required in `.env` file:

- `BOT_TOKEN`: Telegram Bot API token (from @BotFather)
- `DB_PATH` (optional): Database file path (default: `database.sqlite`)

## Key Files to Review

When making changes to specific features:

- **Training logging**: `bot/handlers.py` (main flow), `bot/fsm.py` (states)
- **Competition registration**: `competitions/upcoming_competitions_handlers.py`, `competitions/competitions_handlers.py`
- **Database structure**: `database/models.py` (schema), `database/queries.py` (CRUD)
- **User settings**: `settings/settings_handlers_full.py`
- **Coach features**: `coach/coach_handlers.py`, `coach/coach_queries.py`
- **Background jobs**: `notifications/notification_scheduler.py`, `competitions/reminder_scheduler.py`

## Best Practices

### CRITICAL: Always Update CHANGELOG.md

**ВАЖНО**: При любых изменениях кода ОБЯЗАТЕЛЬНО обновляйте `CHANGELOG.md`:

1. **Формат записи**:
   - Дата в формате `[ГГГГ-ММ-ДД]`
   - Краткое описание изменений
   - Разделы: `### Исправлено`, `### Добавлено`, `### Изменено`, `### Удалено`

2. **Что указывать**:
   - **Проблема**: Какая ошибка была и как она проявлялась
   - **Файлы**: Какие файлы были изменены
   - **Исправление**: Что конкретно было сделано (с примерами кода если нужно)
   - **Результат**: Что теперь работает правильно

3. **Пример записи**:
```markdown
## [2026-01-12] - Исправлена ошибка импорта

### Исправлено

#### Ошибка в модуле X
**Файл:** `path/to/file.py`

**Проблема:**
Описание ошибки и как она проявлялась

**Исправление:**
1. Что было изменено
2. Как это исправило проблему

**Результат:**
Что теперь работает
```

### Module Import Validation

**КРИТИЧЕСКИ ВАЖНО**: Перед использованием импорта ВСЕГДА проверяйте существование модуля:

1. **Проверка существования файла**:
   ```bash
   # Поиск файла
   find . -name "module_name.py"
   # или
   ls path/to/module.py
   ```

2. **Проверка функций в модуле**:
   ```bash
   # Поиск определения функции
   grep -n "def function_name" path/to/module.py
   ```

3. **Частые ошибки импорта**:
   - ❌ `from utils.calendar_utils import` → Модуль не существует
   - ✅ `from bot.calendar_keyboard import CalendarKeyboard` → Правильный путь
   - ❌ `from reports.weekly_report_pdf import` → Модуль не существует
   - ✅ `from bot.pdf_export import create_training_pdf` → Правильный путь

4. **Тестирование импорта**:
   ```bash
   # Проверка синтаксиса
   python -m py_compile path/to/file.py

   # Проверка импорта
   python -c "from module import function"
   ```

5. **Документированные модули проекта**:
   - **Календарь**: `bot.calendar_keyboard.CalendarKeyboard`
   - **PDF Export**: `bot.pdf_export.create_training_pdf`
   - **Графики**: `bot.graphs`, `bot.pdf_graphs`
   - **Форматирование**: `utils.date_formatter.DateFormatter`
   - **Конвертеры**: `utils.unit_converter`

### Calendar Usage

При работе с календарем используйте `bot.calendar_keyboard.CalendarKeyboard`:

```python
from bot.calendar_keyboard import CalendarKeyboard

# Создание календаря
calendar = CalendarKeyboard.create_calendar(
    calendar_format=1,  # 1=дни, 2=месяцы, 3=годы
    current_date=datetime.now(),
    callback_prefix="my_prefix"
)

# Парсинг callback
parsed = CalendarKeyboard.parse_callback_data(
    callback.data,
    prefix="my_prefix"
)

# Обработка навигации
new_calendar = CalendarKeyboard.handle_navigation(
    callback.data,
    prefix="my_prefix"
)
```

### PDF Report Generation

Для генерации PDF отчетов используйте `bot.pdf_export.create_training_pdf`:

```python
from bot.pdf_export import create_training_pdf
from database.queries import get_trainings_by_period, get_training_statistics

# Получение данных
trainings = await get_trainings_by_period(user_id, start_date, end_date)
stats = await get_training_statistics(user_id, start_date, end_date)

# Генерация PDF
pdf_buffer = await create_training_pdf(trainings, "период", stats, user_id)
```

## Troubleshooting

### Callback Handlers Not Working

Check router registration order in `main.py` - more specific routers must be registered first.

### Database Locked Errors

Ensure all database connections use async context managers and properly close.

### Timezone Issues

All schedulers should respect `user_settings.timezone` (default: `Europe/Moscow`). Use `pytz` for timezone conversions.

### Competition Parsing Failures

Competition APIs may change. Check parser error logs and update parsers accordingly. Each parser should gracefully handle missing fields.

### Module Import Errors

If you encounter `ModuleNotFoundError`:
1. Use `grep` or `find` to locate the correct module path
2. Check `CHANGELOG.md` for recent import fixes
3. Refer to "Module Import Validation" section above
4. Always test imports with `python -m py_compile`
