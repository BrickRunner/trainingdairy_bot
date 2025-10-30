"""
Модели базы данных (схемы таблиц)
"""

# SQL-схемы для создания таблиц

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    level TEXT DEFAULT 'новичок',
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
    duration INTEGER NOT NULL,
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
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
    target_time TEXT,  -- целевое время (HH:MM:SS)

    -- Результат после забега
    finish_time TEXT,  -- финишное время (HH:MM:SS)
    place_overall INTEGER,  -- место в общем зачёте
    place_age_category INTEGER,  -- место в возрастной категории
    age_category TEXT,  -- возрастная категория (например M30-39)
    result_comment TEXT,  -- впечатления
    result_photo TEXT,  -- путь к фото финишера

    -- Статусы
    status TEXT DEFAULT 'registered',  -- 'registered', 'dns' (не стартовал), 'dnf' (не финишировал), 'finished'

    -- Даты
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    result_added_at TIMESTAMP,

    FOREIGN KEY (competition_id) REFERENCES competitions(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(competition_id, user_id, distance)
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    removed_at TIMESTAMP,
    FOREIGN KEY (coach_id) REFERENCES users(id),
    FOREIGN KEY (student_id) REFERENCES users(id),
    UNIQUE(coach_id, student_id)
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

    -- Метаданные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (competition_id) REFERENCES competitions(id),
    UNIQUE(user_id, distance)
)
"""

# Список всех таблиц для инициализации
ALL_TABLES = [
    CREATE_USERS_TABLE,
    CREATE_TRAININGS_TABLE,
    CREATE_COMPETITIONS_TABLE,
    CREATE_COMPETITION_PARTICIPANTS_TABLE,
    CREATE_ACHIEVEMENTS_TABLE,
    CREATE_RATINGS_TABLE,
    CREATE_COACH_LINKS_TABLE,
    CREATE_HEALTH_METRICS_TABLE,
    CREATE_USER_SETTINGS_TABLE,
    CREATE_PERSONAL_RECORDS_TABLE
]