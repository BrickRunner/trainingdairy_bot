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
    creator_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    date DATE NOT NULL,
    status TEXT DEFAULT 'planned',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES users(id)
)
"""

CREATE_COMPETITION_PARTICIPANTS_TABLE = """
CREATE TABLE IF NOT EXISTS competition_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_id INTEGER NOT NULL,
    participant_id INTEGER NOT NULL,
    place INTEGER,
    FOREIGN KEY (competition_id) REFERENCES competitions(id),
    FOREIGN KEY (participant_id) REFERENCES users(id)
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
    status TEXT DEFAULT 'pending',
    link_code TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (coach_id) REFERENCES users(id),
    FOREIGN KEY (student_id) REFERENCES users(id)
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
    CREATE_COACH_LINKS_TABLE
]