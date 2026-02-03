"""
Модели базы данных (схемы таблиц)
"""

# SQL-схемы для создания таблиц

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    level TEXT DEFAULT 'новичок',
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
    type TEXT NOT NULL,
    date DATE NOT NULL,
    time TEXT,
    duration INTEGER,  -- Nullable для запланированных тренировок
    distance REAL,
    avg_pace TEXT,
    pace_unit TEXT,
    avg_pulse INTEGER,
    max_pulse INTEGER,
    exercises TEXT,
    intervals TEXT,
    calculated_volume REAL,
    description TEXT,
    results TEXT,
    comment TEXT,
    fatigue_level INTEGER,
    added_by_coach_id INTEGER,  -- ID тренера, если тренировка добавлена тренером
    is_planned INTEGER DEFAULT 0,  -- 1 если это запланированная тренировка
    swimming_location TEXT,  -- Место плавания: 'бассейн' или 'открытая вода'
    pool_length INTEGER,  -- Длина бассейна: 25 или 50 метров
    swimming_styles TEXT,  -- JSON массив стилей плавания
    swimming_sets TEXT,  -- Описание отрезков для плавания
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (added_by_coach_id) REFERENCES users(id)
)
"""

CREATE_COMPETITIONS_TABLE = """
CREATE TABLE IF NOT EXISTS competitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Основная информация
    name TEXT NOT NULL,
    date DATE NOT NULL,
    city TEXT,
    country TEXT DEFAULT 'Россия',
    location TEXT,

    -- Детали соревнования
    distances TEXT,  -- JSON массив: ["42.195", "21.1", "10", "5"]
    type TEXT,  -- 'марафон', 'полумарафон', 'трейл', 'забег', 'ультра'
    sport_type TEXT DEFAULT 'бег',  -- 'бег', 'велоспорт', 'плавание', 'триатлон'
    description TEXT,
    official_url TEXT,

    -- Организатор
    organizer TEXT,  -- 'Беговое сообщество', 'Russia Running', 'Лига героев' и т.д.

    -- Статусы
    registration_status TEXT DEFAULT 'unknown',  -- 'open', 'closed', 'upcoming', 'unknown'
    status TEXT DEFAULT 'upcoming',  -- 'upcoming', 'ongoing', 'finished', 'cancelled'

    -- Метаданные
    created_by INTEGER,  -- user_id создателя (если это пользовательское)
    is_official BOOLEAN DEFAULT 0,  -- официальное или созданное пользователем
    source_url TEXT,  -- URL источника данных

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

    -- Выбор дистанции и цели
    distance REAL,  -- выбранная дистанция (42.195, 21.1, 10, 5 и т.д.)
    distance_name TEXT,  -- название дистанции (для комплексных дистанций типа акватлон)
    target_time TEXT,  -- целевое время (HH:MM:SS)

    -- Результат после забега
    finish_time TEXT,  -- финишное время (HH:MM:SS)
    place_overall INTEGER,  -- место в общем зачёте
    place_age_category INTEGER,  -- место в возрастной категории
    age_category TEXT,  -- возрастная категория (например M30-39)
    heart_rate INTEGER,  -- средний пульс во время забега
    qualification TEXT,  -- выполненный разряд (КМС, МС, МСМК и т.д.)
    result_comment TEXT,  -- впечатления
    result_photo TEXT,  -- путь к фото финишера

    -- Статусы
    status TEXT DEFAULT 'registered',  -- 'registered', 'dns' (не стартовал), 'dnf' (не финишировал), 'finished'

    -- Предложение от тренера
    proposed_by_coach INTEGER DEFAULT 0,  -- 1 если предложено тренером
    proposed_by_coach_id INTEGER,  -- ID тренера, предложившего соревнование
    proposal_status TEXT,  -- 'pending', 'accepted', 'rejected'

    -- Напоминания
    reminders_enabled INTEGER DEFAULT 1,  -- Включены ли напоминания

    -- Даты
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    result_added_at TIMESTAMP,

    FOREIGN KEY (competition_id) REFERENCES competitions(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (proposed_by_coach_id) REFERENCES users(id),
    UNIQUE(competition_id, user_id, distance, distance_name)
)
"""

CREATE_ACHIEVEMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    date_awarded DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
"""

CREATE_RATINGS_TABLE = """
CREATE TABLE IF NOT EXISTS ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    sport_type TEXT DEFAULT 'общий',
    points REAL DEFAULT 0,
    global_rank INTEGER,
    week_points REAL DEFAULT 0,
    month_points REAL DEFAULT 0,
    season_points REAL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
"""

CREATE_COACH_LINKS_TABLE = """
CREATE TABLE IF NOT EXISTS coach_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coach_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    status TEXT DEFAULT 'active',  -- 'active', 'pending', 'removed'
    link_code TEXT UNIQUE,
    coach_nickname TEXT,  -- Псевдоним ученика (виден только тренеру)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    removed_at TIMESTAMP,
    FOREIGN KEY (coach_id) REFERENCES users(id),
    FOREIGN KEY (student_id) REFERENCES users(id),
    UNIQUE(coach_id, student_id)
)
"""

CREATE_TRAINING_COMMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS training_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    training_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
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

    -- Утренние показатели
    morning_pulse INTEGER,
    weight REAL,
    sleep_duration REAL,  -- в часах (например, 7.5)
    sleep_quality INTEGER, -- 1-5 (1=плохо, 5=отлично)

    -- Дополнительные показатели
    mood INTEGER, -- 1-5
    stress_level INTEGER, -- 1-5
    energy_level INTEGER, -- 1-5

    -- Заметки
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, date)
)
"""

CREATE_USER_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS user_settings (
    user_id INTEGER PRIMARY KEY,
    
    -- Персональные данные
    name TEXT,
    birth_date DATE,
    gender TEXT,
    weight REAL,
    height REAL,
    
    -- Основные типы тренировок (JSON массив)
    main_training_types TEXT DEFAULT '["кросс"]',
    
    -- Пульсовые зоны (автоматически или вручную)
    max_pulse INTEGER,
    zone1_min INTEGER,
    zone1_max INTEGER,
    zone2_min INTEGER,
    zone2_max INTEGER,
    zone3_min INTEGER,
    zone3_max INTEGER,
    zone4_min INTEGER,
    zone4_max INTEGER,
    zone5_min INTEGER,
    zone5_max INTEGER,
    
    -- Целевые показатели
    weekly_volume_goal REAL,
    weekly_trainings_goal INTEGER,
    weight_goal REAL,
    
    -- Цели по типам тренировок (JSON объект)
    -- {"кросс": 30, "плавание": 5, "силовая": 2}
    training_type_goals TEXT DEFAULT '{}',
    
    -- Единицы измерения
    distance_unit TEXT DEFAULT 'км',
    weight_unit TEXT DEFAULT 'кг',
    date_format TEXT DEFAULT 'ДД.ММ.ГГГГ',
    timezone TEXT DEFAULT 'Europe/Moscow',

    -- Уведомления
    daily_pulse_weight_time TEXT,
    weekly_report_day TEXT DEFAULT 'Понедельник',
    weekly_report_time TEXT DEFAULT '09:00',
    last_goal_notification_week TEXT,  -- Неделя последнего уведомления о достижении цели (формат: YYYY-WW) - DEPRECATED, используем goal_notifications
    goal_notifications TEXT,  -- JSON с информацией о достигнутых целях {week: {goal_type: True/False}}

    -- Напоминания о тренировках
    training_reminders_enabled INTEGER DEFAULT 0,  -- Включены ли напоминания о тренировках
    training_reminder_days TEXT DEFAULT '[]',  -- JSON массив с днями недели для напоминаний
    training_reminder_time TEXT,  -- Время напоминания (HH:MM)

    -- Режим тренера
    is_coach BOOLEAN DEFAULT 0,  -- Является ли пользователь тренером
    coach_link_code TEXT UNIQUE,  -- Уникальный код для подключения учеников
    
    -- Дата создания и обновления
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id)
)
"""

CREATE_PERSONAL_RECORDS_TABLE = """
CREATE TABLE IF NOT EXISTS personal_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,
    distance REAL NOT NULL,  -- 5, 10, 21.1, 42.195 и т.д.

    -- Лучший результат
    best_time TEXT NOT NULL,  -- лучшее время (HH:MM:SS)
    competition_id INTEGER,  -- на каком соревновании установлен (если есть)
    date DATE NOT NULL,  -- дата установления рекорда
    qualification TEXT,  -- выполненный разряд (КМС, МС, МСМК и т.д.)

    -- Метаданные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (competition_id) REFERENCES competitions(id),
    UNIQUE(user_id, distance)
)
"""

CREATE_COMPETITION_REMINDERS_TABLE = """
CREATE TABLE IF NOT EXISTS competition_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    competition_id INTEGER NOT NULL,
    reminder_type TEXT NOT NULL,  -- '7days', '3days', '1day'
    scheduled_date DATE NOT NULL,
    sent INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (competition_id) REFERENCES competitions(id),
    UNIQUE(user_id, competition_id, reminder_type)
)
"""

# Таблицы для хранения нормативов ЕВСК
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
    distance REAL NOT NULL,
    pool_length INTEGER NOT NULL,
    gender TEXT NOT NULL,
    rank TEXT NOT NULL,
    time_seconds REAL NOT NULL,
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
    distance REAL NOT NULL,
    discipline TEXT NOT NULL,  -- 'шоссе' (разряды присваиваются только за шоссейные гонки)
    gender TEXT NOT NULL,
    rank TEXT NOT NULL,
    time_seconds REAL,  -- Nullable, так как для велоспорта разряды присваиваются по местам, а не по времени
    place INTEGER,  -- Место, необходимое для присвоения разряда
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
    sport_type TEXT NOT NULL,
    version TEXT NOT NULL,
    effective_date DATE NOT NULL,
    source_url TEXT,
    file_hash TEXT,
    is_active INTEGER DEFAULT 1,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sport_type, version)
)
"""

# ==================== TRAINING ASSISTANT TABLES ====================

CREATE_TRAINING_PLANS_TABLE = """
CREATE TABLE IF NOT EXISTS training_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,

    -- Параметры плана
    plan_type TEXT NOT NULL,              -- 'week', 'month'
    sport_type TEXT NOT NULL,             -- 'run', 'swim', 'bike', 'triathlon'
    target_distance REAL,                 -- Целевая дистанция (если есть)
    target_competition_id INTEGER,        -- ID соревнования (если планируем под него)
    current_fitness_level TEXT,           -- 'beginner', 'intermediate', 'advanced'
    available_days TEXT NOT NULL,         -- JSON массив доступных дней ["Пн", "Ср", "Пт"]
    goal_description TEXT,                -- Описание цели (результат, просто финиш и т.д.)

    -- AI сгенерированный план
    plan_content TEXT NOT NULL,           -- JSON структура с планом
    ai_explanation TEXT,                  -- Объяснение от AI почему такой план

    -- Статус и метаданные
    status TEXT DEFAULT 'active',         -- 'active', 'completed', 'abandoned'
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
    plan_id INTEGER,                      -- Связь с планом (если есть)

    -- Обратная связь от пользователя
    user_feedback TEXT NOT NULL,          -- 'too_hard', 'too_easy', 'high_pulse', 'didnt_finish', etc.
    user_comment TEXT,                    -- Комментарий пользователя

    -- AI коррекция
    ai_analysis TEXT NOT NULL,            -- Анализ от AI
    ai_recommendation TEXT NOT NULL,      -- Рекомендация для следующих тренировок
    correction_applied TEXT,              -- JSON с примененными изменениями

    -- Метаданные
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

    -- Параметры подготовки
    days_before INTEGER NOT NULL,         -- 7, 5, 3, 1
    race_distance REAL NOT NULL,
    target_time TEXT,

    -- AI рекомендации
    recommendations TEXT NOT NULL,        -- JSON структура с рекомендациями
    ai_explanation TEXT,

    -- Метаданные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (competition_id) REFERENCES competitions(id),
    UNIQUE(user_id, competition_id, days_before)
)
"""

CREATE_RACE_TACTICS_TABLE = """
CREATE TABLE IF NOT EXISTS race_tactics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    competition_id INTEGER NOT NULL,

    -- Параметры забега
    distance REAL NOT NULL,
    target_time TEXT NOT NULL,
    race_type TEXT,                       -- 'flat', 'hilly', 'trail', etc.

    -- AI тактика
    tactics_plan TEXT NOT NULL,           -- JSON со сплитами и рекомендациями
    pacing_strategy TEXT NOT NULL,        -- Стратегия темпа
    key_points TEXT,                      -- Ключевые моменты по дистанции

    -- Метаданные
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

    -- Контекст разговора
    conversation_type TEXT NOT NULL,      -- 'psychologist', 'general', 'plan', 'correction'
    context_data TEXT,                    -- JSON с контекстом (план, тренировка и т.д.)

    -- Сообщения
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,

    -- Метаданные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
)
"""

CREATE_RESULT_PREDICTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS result_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,

    -- Параметры прогноза
    distance REAL NOT NULL,
    based_on_trainings_period TEXT NOT NULL,  -- Период анализа ('last_month', 'last_2_weeks')

    -- Прогноз
    predicted_time_realistic TEXT NOT NULL,   -- Реалистичный прогноз
    predicted_time_optimistic TEXT NOT NULL,  -- Оптимистичный
    predicted_time_conservative TEXT NOT NULL,-- Осторожный

    confidence_level REAL,                    -- Уровень уверенности (0-100%)
    ai_explanation TEXT NOT NULL,             -- Объяснение прогноза
    key_factors TEXT,                         -- JSON с ключевыми факторами

    -- Метаданные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
)
"""

CREATE_TA_USER_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS ta_user_settings (
    user_id INTEGER PRIMARY KEY,

    -- Предпочтения пользователя
    preferred_ai_style TEXT DEFAULT 'friendly',  -- 'friendly', 'professional', 'motivational'
    coaching_experience TEXT DEFAULT 'none',     -- 'none', 'self', 'with_coach'
    injury_history TEXT,                         -- JSON с историей травм

    -- Статистика использования
    total_plans_generated INTEGER DEFAULT 0,
    total_corrections_made INTEGER DEFAULT 0,
    total_ai_chats INTEGER DEFAULT 0,

    -- Метаданные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
)
"""

# Список всех таблиц для инициализации
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