"""
Модели базы данных (схемы таблиц)
"""

# ==================== ОСНОВНЫЕ ТАБЛИЦЫ ====================

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,  -- Telegram ID пользователя
    username TEXT NOT NULL,
    level TEXT DEFAULT 'новичок',  -- Уровень активности (новичок, любитель, профи, элитный)
    level_updated_week TEXT,  -- Неделя последнего обновления уровня (формат: YYYY-WW)
    weight REAL,
    pulse_norm INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_TRAININGS_TABLE = """
CREATE TABLE IF NOT EXISTS trainings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,  -- Тип тренировки (кросс, плавание, велосипед, силовая и т.д.)
    date DATE NOT NULL,
    time TEXT,  -- Время начала тренировки
    duration INTEGER,  -- Длительность в минутах (nullable для запланированных)

    -- Данные о дистанции и темпе
    distance REAL,
    avg_pace TEXT,  -- Средний темп (мин/км или мин/миля)
    pace_unit TEXT,  -- Единица темпа

    -- Пульсовые данные
    avg_pulse INTEGER,
    max_pulse INTEGER,

    -- Специфичные поля для разных типов тренировок
    exercises TEXT,  -- Упражнения для силовых тренировок
    intervals TEXT,  -- Описание интервалов
    calculated_volume REAL,  -- Расчетный объем (для плавания, велосипеда)

    -- Дополнительная информация
    description TEXT,
    results TEXT,
    comment TEXT,
    fatigue_level INTEGER,  -- Уровень усталости (1-5)

    -- Связь с тренером
    added_by_coach_id INTEGER,  -- ID тренера, если тренировка добавлена тренером
    is_planned INTEGER DEFAULT 0,  -- 1 если это запланированная тренировка

    -- Специфичные поля для плавания
    swimming_location TEXT,  -- Место: 'бассейн' или 'открытая вода'
    pool_length INTEGER,  -- Длина бассейна: 25 или 50 метров
    swimming_styles TEXT,  -- JSON массив стилей плавания
    swimming_sets TEXT,  -- Описание отрезков

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (added_by_coach_id) REFERENCES users(id)
)
"""

CREATE_COMPETITIONS_TABLE = """
CREATE TABLE IF NOT EXISTS competitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Основная информация о соревновании
    name TEXT NOT NULL,
    date DATE NOT NULL,
    city TEXT,
    country TEXT DEFAULT 'Россия',
    location TEXT,  -- Место проведения

    -- Детали соревнования
    distances TEXT,  -- JSON массив дистанций: ["42.195", "21.1", "10", "5"]
    type TEXT,  -- Тип: марафон, полумарафон, трейл, забег, ультра
    sport_type TEXT DEFAULT 'бег',  -- Вид спорта: бег, велоспорт, плавание, триатлон
    description TEXT,
    official_url TEXT,  -- Ссылка на официальный сайт

    -- Организатор соревнования
    organizer TEXT,  -- Беговое сообщество, Russia Running, Лига героев и т.д.

    -- Статусы регистрации и проведения
    registration_status TEXT DEFAULT 'unknown',  -- open, closed, upcoming, unknown
    status TEXT DEFAULT 'upcoming',  -- upcoming, ongoing, finished, cancelled

    -- Метаданные и источник
    created_by INTEGER,  -- user_id создателя (для пользовательских соревнований)
    is_official BOOLEAN DEFAULT 0,  -- 0=пользовательское, 1=официальное
    source_url TEXT,  -- URL источника данных (для идентификации)

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by) REFERENCES users(id)
)
"""

CREATE_COMPETITION_PARTICIPANTS_TABLE = """
CREATE TABLE IF NOT EXISTS competition_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    competition_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,

    -- Выбранная дистанция и целевое время
    distance REAL,  -- Дистанция в км (42.195, 21.1, 10, 5)
    distance_name TEXT,  -- Название (для комплексных: акватлон, дуатлон)
    target_time TEXT,  -- Целевое время в формате HH:MM:SS

    -- Результаты после финиша
    finish_time TEXT,  -- Фактическое время финиша HH:MM:SS
    place_overall INTEGER,  -- Место в общем зачете
    place_age_category INTEGER,  -- Место в возрастной категории
    age_category TEXT,  -- Возрастная категория (M30-39, F25-29)
    heart_rate INTEGER,  -- Средний пульс на дистанции
    qualification TEXT,  -- Выполненный разряд (КМС, МС, МСМК)
    result_comment TEXT,  -- Комментарий о впечатлениях
    result_photo TEXT,  -- Путь к фото финишера

    -- Статус участия
    status TEXT DEFAULT 'registered',  -- registered, dns (не вышел), dnf (не финишировал), finished

    -- Связь с тренером (если тренер предложил соревнование)
    proposed_by_coach INTEGER DEFAULT 0,  -- 1=предложено тренером
    proposed_by_coach_id INTEGER,  -- ID тренера
    proposal_status TEXT,  -- pending (ожидает), accepted (принято), rejected (отклонено)

    -- Настройки уведомлений
    reminders_enabled INTEGER DEFAULT 1,  -- 1=напоминания включены

    -- Временные метки
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    result_added_at TIMESTAMP,

    FOREIGN KEY (competition_id) REFERENCES competitions(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (proposed_by_coach_id) REFERENCES users(id),
    -- Один пользователь может участвовать на нескольких дистанциях одного соревнования
    UNIQUE(competition_id, user_id, distance, distance_name)
)
"""

CREATE_ACHIEVEMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,  -- Название достижения (ключ из achievements_data.py)
    date_awarded DATE DEFAULT CURRENT_DATE,  -- Дата получения
    FOREIGN KEY (user_id) REFERENCES users(id)
)
"""

CREATE_RATINGS_TABLE = """
CREATE TABLE IF NOT EXISTS ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    sport_type TEXT DEFAULT 'общий',  -- Тип спорта для рейтинга

    -- Очки за разные периоды
    points REAL DEFAULT 0,  -- Общие очки за всё время
    global_rank INTEGER,  -- Глобальное место
    week_points REAL DEFAULT 0,  -- Очки за текущую неделю
    month_points REAL DEFAULT 0,  -- Очки за текущий месяц
    season_points REAL DEFAULT 0,  -- Очки за текущий сезон

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
"""

CREATE_COACH_LINKS_TABLE = """
CREATE TABLE IF NOT EXISTS coach_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coach_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,

    -- Статус связи и уникальный код
    status TEXT DEFAULT 'active',  -- active, pending, removed
    link_code TEXT UNIQUE,  -- Уникальный код для подключения
    coach_nickname TEXT,  -- Псевдоним ученика (видит только тренер)

    -- Временные метки
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    removed_at TIMESTAMP,

    FOREIGN KEY (coach_id) REFERENCES users(id),
    FOREIGN KEY (student_id) REFERENCES users(id),
    -- Один тренер может быть связан с одним учеником только один раз
    UNIQUE(coach_id, student_id)
)
"""

CREATE_TRAINING_COMMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS training_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    training_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,  -- ID автора комментария (обычно тренер)
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (training_id) REFERENCES trainings(id),
    FOREIGN KEY (author_id) REFERENCES users(id)
)
"""

CREATE_HEALTH_METRICS_TABLE = """
CREATE TABLE IF NOT EXISTS health_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date DATE NOT NULL,

    -- Утренние физические показатели
    morning_pulse INTEGER,  -- Утренний пульс в покое
    weight REAL,  -- Вес в кг или фунтах
    sleep_duration REAL,  -- Продолжительность сна в часах (7.5, 8.0)
    sleep_quality INTEGER,  -- Качество сна по шкале 1-5

    -- Психологические показатели (шкала 1-5)
    mood INTEGER,  -- Настроение
    stress_level INTEGER,  -- Уровень стресса
    energy_level INTEGER,  -- Уровень энергии

    -- Дополнительные заметки
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id),
    -- Один пользователь может иметь только одну запись на одну дату
    UNIQUE(user_id, date)
)
"""

CREATE_USER_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS user_settings (
    user_id INTEGER PRIMARY KEY,

    -- Персональные данные пользователя
    name TEXT,
    birth_date DATE,
    gender TEXT,  -- male, female
    weight REAL,
    height REAL,

    -- Основные типы тренировок (JSON массив: ["кросс", "плавание"])
    main_training_types TEXT DEFAULT '["кросс"]',

    -- Пульсовые зоны (рассчитываются автоматически или задаются вручную)
    max_pulse INTEGER,  -- Максимальный пульс
    zone1_min INTEGER, zone1_max INTEGER,  -- Зона 1: восстановительная (50-60%)
    zone2_min INTEGER, zone2_max INTEGER,  -- Зона 2: аэробная (60-70%)
    zone3_min INTEGER, zone3_max INTEGER,  -- Зона 3: темповая (70-80%)
    zone4_min INTEGER, zone4_max INTEGER,  -- Зона 4: пороговая (80-90%)
    zone5_min INTEGER, zone5_max INTEGER,  -- Зона 5: максимальная (90-100%)

    -- Целевые показатели
    weekly_volume_goal REAL,  -- Цель по недельному объему (км)
    weekly_trainings_goal INTEGER,  -- Цель по количеству тренировок в неделю
    weight_goal REAL,  -- Целевой вес

    -- Цели по типам тренировок (JSON: {"кросс": 30, "плавание": 5})
    training_type_goals TEXT DEFAULT '{}',

    -- Единицы измерения
    distance_unit TEXT DEFAULT 'км',  -- км или мили
    weight_unit TEXT DEFAULT 'кг',  -- кг или фунты
    date_format TEXT DEFAULT 'ДД.ММ.ГГГГ',
    timezone TEXT DEFAULT 'Europe/Moscow',

    -- Настройки уведомлений
    daily_pulse_weight_time TEXT,  -- Время ежедневного напоминания
    weekly_report_day TEXT DEFAULT 'Понедельник',
    weekly_report_time TEXT DEFAULT '09:00',
    last_goal_notification_week TEXT,  -- DEPRECATED
    goal_notifications TEXT,  -- JSON с достигнутыми целями

    -- Напоминания о тренировках
    training_reminders_enabled INTEGER DEFAULT 0,  -- 0=выключены, 1=включены
    training_reminder_days TEXT DEFAULT '[]',  -- JSON массив дней недели
    training_reminder_time TEXT,  -- Время напоминания HH:MM

    -- Режим тренера
    is_coach BOOLEAN DEFAULT 0,  -- 1 если пользователь - тренер
    coach_link_code TEXT UNIQUE,  -- Уникальный код для подключения учеников

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
)
"""

CREATE_PERSONAL_RECORDS_TABLE = """
CREATE TABLE IF NOT EXISTS personal_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,
    distance REAL NOT NULL,  -- Дистанция в км (5, 10, 21.1, 42.195)

    -- Данные о лучшем результате
    best_time TEXT NOT NULL,  -- Лучшее время в формате HH:MM:SS
    competition_id INTEGER,  -- ID соревнования где установлен рекорд
    date DATE NOT NULL,  -- Дата установления PR
    qualification TEXT,  -- Выполненный разряд (III, II, I, КМС, МС, МСМК)

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (competition_id) REFERENCES competitions(id),
    -- Один пользователь может иметь только один PR на каждую дистанцию
    UNIQUE(user_id, distance)
)
"""

CREATE_COMPETITION_REMINDERS_TABLE = """
CREATE TABLE IF NOT EXISTS competition_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    competition_id INTEGER NOT NULL,

    -- Тип и расписание напоминания
    reminder_type TEXT NOT NULL,  -- 7days, 3days, 1day (за сколько дней до старта)
    scheduled_date DATE NOT NULL,  -- Дата отправки напоминания

    -- Статус отправки
    sent INTEGER DEFAULT 0,  -- 0=не отправлено, 1=отправлено
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,  -- Время фактической отправки

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (competition_id) REFERENCES competitions(id),
    -- Для каждого пользователя и соревнования может быть только одно напоминание каждого типа
    UNIQUE(user_id, competition_id, reminder_type)
)
"""

# ==================== ТАБЛИЦЫ НОРМАТИВОВ ЕВСК ====================

CREATE_RUNNING_STANDARDS_TABLE = """
CREATE TABLE IF NOT EXISTS running_standards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    distance REAL NOT NULL,
    gender TEXT NOT NULL,
    rank TEXT NOT NULL,
    time_seconds REAL NOT NULL,
    version TEXT NOT NULL,
    effective_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(distance, gender, rank, version)
)
"""

CREATE_SWIMMING_STANDARDS_TABLE = """
CREATE TABLE IF NOT EXISTS swimming_standards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    distance REAL NOT NULL,  -- Дистанция в метрах (50, 100, 200, 400, 800, 1500)
    pool_length INTEGER NOT NULL,  -- Длина бассейна: 25 или 50 метров
    gender TEXT NOT NULL,
    rank TEXT NOT NULL,
    time_seconds REAL NOT NULL,  -- Норматив в секундах
    version TEXT NOT NULL,
    effective_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(distance, pool_length, gender, rank, version)
)
"""

CREATE_CYCLING_STANDARDS_TABLE = """
CREATE TABLE IF NOT EXISTS cycling_standards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    distance REAL NOT NULL,  -- Дистанция в км
    discipline TEXT NOT NULL,  -- Дисциплина (обычно 'шоссе')
    gender TEXT NOT NULL,
    rank TEXT NOT NULL,
    time_seconds REAL,  -- Nullable: для велоспорта разряды обычно по местам
    place INTEGER,  -- Место необходимое для разряда (например, 1-3 для МС)
    version TEXT NOT NULL,
    effective_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(distance, discipline, gender, rank, version)
)
"""

CREATE_STANDARDS_VERSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS standards_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport_type TEXT NOT NULL,  -- Вид спорта (бег, плавание, велоспорт)
    version TEXT NOT NULL,  -- Версия нормативов (год)
    effective_date DATE NOT NULL,  -- Дата вступления в силу
    source_url TEXT,  -- URL источника нормативов
    file_hash TEXT,  -- Хеш файла для проверки обновлений
    is_active INTEGER DEFAULT 1,  -- 1=актуальная версия
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sport_type, version)
)
"""

# ==================== ТАБЛИЦЫ TRAINING ASSISTANT (AI) ====================

CREATE_TRAINING_PLANS_TABLE = """
CREATE TABLE IF NOT EXISTS training_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,

    -- Параметры тренировочного плана
    plan_type TEXT NOT NULL,  -- week (неделя), month (месяц)
    sport_type TEXT NOT NULL,  -- run, swim, bike, triathlon
    target_distance REAL,  -- Целевая дистанция если есть
    target_competition_id INTEGER,  -- ID соревнования для подготовки
    current_fitness_level TEXT,  -- beginner, intermediate, advanced
    available_days TEXT NOT NULL,  -- JSON массив доступных дней ["Пн", "Ср", "Пт"]
    goal_description TEXT,  -- Описание цели пользователя

    -- AI сгенерированный план
    plan_content TEXT NOT NULL,  -- JSON с детальным планом тренировок
    ai_explanation TEXT,  -- Объяснение AI почему выбран такой план

    -- Статус и даты
    status TEXT DEFAULT 'active',  -- active, completed, abandoned
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (target_competition_id) REFERENCES competitions(id)
)
"""

CREATE_TRAINING_CORRECTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS training_corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    training_id INTEGER NOT NULL,
    plan_id INTEGER,  -- Связь с планом если коррекция в рамках плана

    -- Обратная связь от пользователя
    user_feedback TEXT NOT NULL,  -- too_hard, too_easy, high_pulse, didnt_finish
    user_comment TEXT,  -- Дополнительный комментарий

    -- AI анализ и рекомендации
    ai_analysis TEXT NOT NULL,  -- Анализ выполненной тренировки
    ai_recommendation TEXT NOT NULL,  -- Рекомендации для будущих тренировок
    correction_applied TEXT,  -- JSON с конкретными изменениями плана

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (training_id) REFERENCES trainings(id),
    FOREIGN KEY (plan_id) REFERENCES training_plans(id)
)
"""

CREATE_RACE_PREPARATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS race_preparations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    competition_id INTEGER NOT NULL,

    -- Параметры подготовки к старту
    days_before INTEGER NOT NULL,  -- За сколько дней (7, 5, 3, 1)
    race_distance REAL NOT NULL,
    target_time TEXT,  -- Целевое время

    -- AI рекомендации по подготовке
    recommendations TEXT NOT NULL,  -- JSON с рекомендациями (питание, сон, тренировки)
    ai_explanation TEXT,  -- Объяснение рекомендаций

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (competition_id) REFERENCES competitions(id),
    -- Для каждого соревнования может быть несколько рекомендаций на разные даты
    UNIQUE(user_id, competition_id, days_before)
)
"""

CREATE_RACE_TACTICS_TABLE = """
CREATE TABLE IF NOT EXISTS race_tactics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    competition_id INTEGER NOT NULL,

    -- Параметры забега для тактики
    distance REAL NOT NULL,
    target_time TEXT NOT NULL,
    race_type TEXT,  -- flat (ровная), hilly (холмы), trail (трейл)

    -- AI тактический план
    tactics_plan TEXT NOT NULL,  -- JSON с планом сплитов по км
    pacing_strategy TEXT NOT NULL,  -- Стратегия распределения темпа
    key_points TEXT,  -- Ключевые точки дистанции и действия

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (competition_id) REFERENCES competitions(id)
)
"""

CREATE_AI_CONVERSATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS ai_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,

    -- Контекст и тип диалога
    conversation_type TEXT NOT NULL,  -- psychologist, general, plan, correction
    context_data TEXT,  -- JSON с контекстом (данные о плане, тренировке)

    -- История переписки
    user_message TEXT NOT NULL,  -- Сообщение пользователя
    ai_response TEXT NOT NULL,  -- Ответ AI

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
)
"""

CREATE_RESULT_PREDICTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS result_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,

    -- Параметры для прогнозирования
    distance REAL NOT NULL,  -- Дистанция для прогноза
    based_on_trainings_period TEXT NOT NULL,  -- Период анализа (last_month, last_2_weeks)

    -- Три варианта прогноза
    predicted_time_realistic TEXT NOT NULL,  -- Реалистичный прогноз
    predicted_time_optimistic TEXT NOT NULL,  -- Оптимистичный (лучший сценарий)
    predicted_time_conservative TEXT NOT NULL,  -- Консервативный (безопасный)

    -- Метаданные прогноза
    confidence_level REAL,  -- Уровень уверенности 0-100%
    ai_explanation TEXT NOT NULL,  -- Объяснение от AI
    key_factors TEXT,  -- JSON с факторами влияющими на прогноз

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
)
"""

CREATE_TA_USER_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS ta_user_settings (
    user_id INTEGER PRIMARY KEY,

    -- Предпочтения взаимодействия с AI
    preferred_ai_style TEXT DEFAULT 'friendly',  -- friendly, professional, motivational
    coaching_experience TEXT DEFAULT 'none',  -- none (новичок), self (самоподготовка), with_coach (с тренером)
    injury_history TEXT,  -- JSON с историей травм и ограничений

    -- Статистика использования AI функций
    total_plans_generated INTEGER DEFAULT 0,  -- Количество созданных планов
    total_corrections_made INTEGER DEFAULT 0,  -- Количество корректировок
    total_ai_chats INTEGER DEFAULT 0,  -- Количество диалогов с AI

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
)
"""

# ==================== СПИСОК ВСЕХ ТАБЛИЦ ====================

# Список таблиц для инициализации БД при первом запуске
ALL_TABLES = [
    CREATE_USERS_TABLE,
    CREATE_TRAININGS_TABLE,
    CREATE_COMPETITIONS_TABLE,
    CREATE_COMPETITION_PARTICIPANTS_TABLE,
    CREATE_COMPETITION_REMINDERS_TABLE,
    CREATE_ACHIEVEMENTS_TABLE,
    CREATE_RATINGS_TABLE,
    CREATE_COACH_LINKS_TABLE,
    CREATE_TRAINING_COMMENTS_TABLE,
    CREATE_HEALTH_METRICS_TABLE,
    CREATE_USER_SETTINGS_TABLE,
    CREATE_PERSONAL_RECORDS_TABLE,
    # Таблицы нормативов ЕВСК
    CREATE_RUNNING_STANDARDS_TABLE,
    CREATE_SWIMMING_STANDARDS_TABLE,
    CREATE_CYCLING_STANDARDS_TABLE,
    CREATE_STANDARDS_VERSIONS_TABLE,
    # Таблицы Training Assistant
    CREATE_TRAINING_PLANS_TABLE,
    CREATE_TRAINING_CORRECTIONS_TABLE,
    CREATE_RACE_PREPARATIONS_TABLE,
    CREATE_RACE_TACTICS_TABLE,
    CREATE_AI_CONVERSATIONS_TABLE,
    CREATE_RESULT_PREDICTIONS_TABLE,
    CREATE_TA_USER_SETTINGS_TABLE
]