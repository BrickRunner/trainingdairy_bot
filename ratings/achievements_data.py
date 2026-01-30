"""
Данные о достижениях пользователей

Всего 55 достижений, разделенных по категориям:
- Соревнования (20)
- Результаты (6)
- Активность (12)
- География (6)
- Специальные (11)
"""

# Категории достижений
ACHIEVEMENT_CATEGORIES = {
    'competitions': {
        'name': 'Соревнования',
        'emoji': '🏃',
        'order': 1
    },
    'results': {
        'name': 'Результаты',
        'emoji': '🏆',
        'order': 2
    },
    'activity': {
        'name': 'Активность',
        'emoji': '📊',
        'order': 3
    },
    'geography': {
        'name': 'География',
        'emoji': '🌍',
        'order': 4
    },
    'special': {
        'name': 'Специальные',
        'emoji': '🎯',
        'order': 5
    }
}

# Уровни сложности достижений
ACHIEVEMENT_LEVELS = {
    'white': {'name': 'Белый', 'emoji': '⚪', 'order': 1},
    'green': {'name': 'Зеленый', 'emoji': '🟢', 'order': 2},
    'blue': {'name': 'Синий', 'emoji': '🔵', 'order': 3},
    'purple': {'name': 'Фиолетовый', 'emoji': '🟣', 'order': 4},
    'gold': {'name': 'Золотой', 'emoji': '🟡', 'order': 5}
}

# Все достижения (55 штук)
ACHIEVEMENTS = {
    # ============== СОРЕВНОВАНИЯ (20) ==============
    'first_competition': {
        'id': 'first_competition',
        'category': 'competitions',
        'emoji': '🎯',
        'name': 'Первый старт',
        'description': 'Участие в первом соревновании',
        'level': 'white',
        'points': 10,
        'order': 1
    },
    'ten_k_first': {
        'id': 'ten_k_first',
        'category': 'competitions',
        'emoji': '🔟',
        'name': 'Десятка',
        'description': 'Участие в первом забеге на 10 км',
        'level': 'white',
        'points': 20,
        'order': 2
    },
    'half_marathon_first': {
        'id': 'half_marathon_first',
        'category': 'competitions',
        'emoji': '🏃',
        'name': 'Полумарафонец',
        'description': 'Участие в первом полумарафоне',
        'level': 'green',
        'points': 40,
        'order': 3
    },
    'marathon_first': {
        'id': 'marathon_first',
        'category': 'competitions',
        'emoji': '🏁',
        'name': 'Марафонец',
        'description': 'Участие в первом марафоне',
        'level': 'blue',
        'points': 80,
        'order': 4
    },
    'ultra_marathon': {
        'id': 'ultra_marathon',
        'category': 'competitions',
        'emoji': '⚡',
        'name': 'Ультрамарафонец',
        'description': 'Участие в ультрамарафоне (42+ км)',
        'level': 'purple',
        'points': 120,
        'order': 5
    },
    'triathlon_first': {
        'id': 'triathlon_first',
        'category': 'competitions',
        'emoji': '🏊🚴🏃',
        'name': 'Триатлет',
        'description': 'Участие в триатлоне',
        'level': 'blue',
        'points': 60,
        'order': 6
    },
    'swimmer': {
        'id': 'swimmer',
        'category': 'competitions',
        'emoji': '🏊',
        'name': 'Пловец',
        'description': 'Участие в 5 соревнованиях по плаванию',
        'level': 'green',
        'points': 30,
        'order': 7
    },
    'cyclist': {
        'id': 'cyclist',
        'category': 'competitions',
        'emoji': '🚴',
        'name': 'Велосипедист',
        'description': 'Участие в 5 велозаездах',
        'level': 'green',
        'points': 30,
        'order': 8
    },
    'mid_distance': {
        'id': 'mid_distance',
        'category': 'competitions',
        'emoji': '🏃‍♀️',
        'name': 'Средневик',
        'description': 'Участие в 10 забегах 5-10 км',
        'level': 'green',
        'points': 30,
        'order': 9
    },
    'versatile': {
        'id': 'versatile',
        'category': 'competitions',
        'emoji': '🏊‍♂️🚴‍♂️🏃‍♂️',
        'name': 'Универсал',
        'description': 'Участие в соревнованиях по 3 разным видам спорта',
        'level': 'green',
        'points': 50,
        'order': 10
    },
    'distance_collector': {
        'id': 'distance_collector',
        'category': 'competitions',
        'emoji': '🎯',
        'name': 'Коллекционер дистанций',
        'description': 'Участие в стартах на всех популярных дистанциях (5, 10, 21.1, 42.2 км)',
        'level': 'blue',
        'points': 100,
        'order': 11
    },
    'enthusiast': {
        'id': 'enthusiast',
        'category': 'competitions',
        'emoji': '🏃',
        'name': 'Любитель',
        'description': 'Участие в 5 соревнованиях',
        'level': 'white',
        'points': 20,
        'order': 12
    },
    'active_runner': {
        'id': 'active_runner',
        'category': 'competitions',
        'emoji': '🏃‍♂️',
        'name': 'Энтузиаст',
        'description': 'Участие в 10 соревнованиях',
        'level': 'green',
        'points': 30,
        'order': 13
    },
    'experienced_runner': {
        'id': 'experienced_runner',
        'category': 'competitions',
        'emoji': '🏅',
        'name': 'Опытный бегун',
        'description': 'Участие в 25 соревнованиях',
        'level': 'blue',
        'points': 50,
        'order': 14
    },
    'veteran': {
        'id': 'veteran',
        'category': 'competitions',
        'emoji': '🎖️',
        'name': 'Ветеран',
        'description': 'Участие в 50 соревнованиях',
        'level': 'purple',
        'points': 100,
        'order': 15
    },
    'legend': {
        'id': 'legend',
        'category': 'competitions',
        'emoji': '👑',
        'name': 'Легенда',
        'description': 'Участие в 100 соревнованиях',
        'level': 'gold',
        'points': 200,
        'order': 16
    },
    'annual_marathon': {
        'id': 'annual_marathon',
        'category': 'competitions',
        'emoji': '📅',
        'name': 'Годовой марафон',
        'description': 'Участие в 12+ соревнованиях за год',
        'level': 'blue',
        'points': 50,
        'order': 17
    },
    'streak_3_months': {
        'id': 'streak_3_months',
        'category': 'competitions',
        'emoji': '🔥',
        'name': 'Серийник',
        'description': 'Участие в соревнованиях 3 месяца подряд',
        'level': 'green',
        'points': 30,
        'order': 18
    },
    'streak_6_months': {
        'id': 'streak_6_months',
        'category': 'competitions',
        'emoji': '🔥🔥',
        'name': 'Непрерывная полоса',
        'description': 'Участие в соревнованиях 6 месяцев подряд',
        'level': 'blue',
        'points': 60,
        'order': 19
    },
    'streak_12_months': {
        'id': 'streak_12_months',
        'category': 'competitions',
        'emoji': '🔥🔥🔥',
        'name': 'Соревнования на автомате',
        'description': 'Участие в соревнованиях 12 месяцев подряд',
        'level': 'purple',
        'points': 120,
        'order': 20
    },

    # ============== РЕЗУЛЬТАТЫ (6) ==============
    'first_podium': {
        'id': 'first_podium',
        'category': 'results',
        'emoji': '🥉',
        'name': 'Первый подиум',
        'description': 'Первое место в топ-3',
        'level': 'green',
        'points': 40,
        'order': 1
    },
    'podium_5_times': {
        'id': 'podium_5_times',
        'category': 'results',
        'emoji': '🏆',
        'name': 'Подиумист',
        'description': '5 раз в топ-3',
        'level': 'blue',
        'points': 100,
        'order': 2
    },
    'pr_improvement': {
        'id': 'pr_improvement',
        'category': 'results',
        'emoji': '💥',
        'name': 'Прорыв',
        'description': 'Улучшение ЛР на 5+ минут',
        'level': 'blue',
        'points': 60,
        'order': 3
    },
    'progress_streak': {
        'id': 'progress_streak',
        'category': 'results',
        'emoji': '📈',
        'name': 'Серия прогресса',
        'description': 'Улучшение ЛР 3 раза подряд на одной дистанции',
        'level': 'green',
        'points': 50,
        'order': 4
    },
    'record_holder': {
        'id': 'record_holder',
        'category': 'results',
        'emoji': '⭐',
        'name': 'Рекордсмен',
        'description': 'Установка ЛР на 5 разных дистанциях',
        'level': 'blue',
        'points': 70,
        'order': 5
    },
    'goal_achiever': {
        'id': 'goal_achiever',
        'category': 'results',
        'emoji': '🎯',
        'name': 'Целеустремленный',
        'description': 'Выполнение целевого времени 5 раз',
        'level': 'green',
        'points': 50,
        'order': 6
    },

    # ============== АКТИВНОСТЬ (12) ==============
    'first_result': {
        'id': 'first_result',
        'category': 'activity',
        'emoji': '📖',
        'name': 'Дневник готов',
        'description': 'Добавление первого результата',
        'level': 'white',
        'points': 10,
        'order': 1
    },
    'historian_10': {
        'id': 'historian_10',
        'category': 'activity',
        'emoji': '📚',
        'name': 'Историк',
        'description': 'Добавление 10 результатов',
        'level': 'green',
        'points': 30,
        'order': 2
    },
    'archivist': {
        'id': 'archivist',
        'category': 'activity',
        'emoji': '🗂️',
        'name': 'Архивариус',
        'description': 'Добавление 50 результатов',
        'level': 'blue',
        'points': 80,
        'order': 3
    },
    'first_training': {
        'id': 'first_training',
        'category': 'activity',
        'emoji': '🏋️',
        'name': 'Первая тренировка',
        'description': 'Добавление первой тренировки',
        'level': 'white',
        'points': 5,
        'order': 4
    },
    'training_month': {
        'id': 'training_month',
        'category': 'activity',
        'emoji': '💪',
        'name': 'Тренировочный месяц',
        'description': '20+ тренировок за месяц',
        'level': 'green',
        'points': 40,
        'order': 5
    },
    'regularity': {
        'id': 'regularity',
        'category': 'activity',
        'emoji': '📅',
        'name': 'Регулярность',
        'description': 'Тренировки 7 дней подряд',
        'level': 'green',
        'points': 30,
        'order': 6
    },
    'mileage_100': {
        'id': 'mileage_100',
        'category': 'activity',
        'emoji': '🏃‍♂️',
        'name': 'Километраж',
        'description': '100 км за месяц в тренировках',
        'level': 'green',
        'points': 50,
        'order': 7
    },
    'mileage_200': {
        'id': 'mileage_200',
        'category': 'activity',
        'emoji': '🏃‍♂️💨',
        'name': 'Марафонский километраж',
        'description': '200+ км за месяц в тренировках',
        'level': 'blue',
        'points': 80,
        'order': 8
    },
    'first_registration': {
        'id': 'first_registration',
        'category': 'activity',
        'emoji': '📝',
        'name': 'Планировщик',
        'description': 'Регистрация на первое соревнование через бота',
        'level': 'white',
        'points': 5,
        'order': 9
    },
    'active_planner': {
        'id': 'active_planner',
        'category': 'activity',
        'emoji': '📋',
        'name': 'Активный планировщик',
        'description': 'Регистрация на 10 соревнований через бота',
        'level': 'green',
        'points': 20,
        'order': 10
    },
    'calendar_full': {
        'id': 'calendar_full',
        'category': 'activity',
        'emoji': '📆',
        'name': 'Календарь полон',
        'description': 'Одновременная регистрация на 5+ предстоящих соревнований',
        'level': 'green',
        'points': 30,
        'order': 11
    },
    'detailer': {
        'id': 'detailer',
        'category': 'activity',
        'emoji': '📊',
        'name': 'Детализатор',
        'description': 'Добавление полной информации (время, место, категория, фото) 10 раз',
        'level': 'green',
        'points': 40,
        'order': 12
    },

    # ============== ГЕОГРАФИЯ (6) ==============
    'traveler': {
        'id': 'traveler',
        'category': 'geography',
        'emoji': '🗺️',
        'name': 'Путешественник',
        'description': 'Участие в соревнованиях в 5 разных городах',
        'level': 'green',
        'points': 30,
        'order': 1
    },
    'russia_geography': {
        'id': 'russia_geography',
        'category': 'geography',
        'emoji': '🌍',
        'name': 'География России',
        'description': 'Участие в соревнованиях в 10 разных городах',
        'level': 'blue',
        'points': 60,
        'order': 2
    },
    'explorer': {
        'id': 'explorer',
        'category': 'geography',
        'emoji': '🧭',
        'name': 'Исследователь',
        'description': 'Участие в соревнованиях в 20 разных городах',
        'level': 'purple',
        'points': 100,
        'order': 3
    },
    'regions_5': {
        'id': 'regions_5',
        'category': 'geography',
        'emoji': '🗾',
        'name': 'Регионы России',
        'description': 'Участие в соревнованиях в 5 разных регионах',
        'level': 'green',
        'points': 50,
        'order': 4
    },
    'regions_10': {
        'id': 'regions_10',
        'category': 'geography',
        'emoji': '🇷🇺',
        'name': 'Всероссийский',
        'description': 'Участие в соревнованиях в 10 разных регионах',
        'level': 'blue',
        'points': 100,
        'order': 5
    },
    'moscow_spb': {
        'id': 'moscow_spb',
        'category': 'geography',
        'emoji': '🏛️',
        'name': 'Москвич/Питерец',
        'description': 'Участие в 10 соревнованиях в Москве или СПб',
        'level': 'green',
        'points': 40,
        'order': 6
    },

    # ============== СПЕЦИАЛЬНЫЕ (11) ==============
    'bot_1_year': {
        'id': 'bot_1_year',
        'category': 'special',
        'emoji': '🎂',
        'name': 'Долгожитель',
        'description': 'Использование бота 1 год',
        'level': 'green',
        'points': 50,
        'order': 1
    },
    'bot_2_years': {
        'id': 'bot_2_years',
        'category': 'special',
        'emoji': '🎂🎂',
        'name': 'Ветеран бота',
        'description': 'Использование бота 2 года',
        'level': 'blue',
        'points': 100,
        'order': 2
    },
    'russia_running_fan': {
        'id': 'russia_running_fan',
        'category': 'special',
        'emoji': '🏃‍♂️🇷🇺',
        'name': 'Russia Running фанат',
        'description': 'Участие в 10 соревнованиях Russia Running',
        'level': 'green',
        'points': 40,
        'order': 3
    },
    'hero_league': {
        'id': 'hero_league',
        'category': 'special',
        'emoji': '🦸',
        'name': 'Лига героев',
        'description': 'Участие в 5 соревнованиях Hero League',
        'level': 'green',
        'points': 40,
        'order': 4
    },
    'parkrun_regular': {
        'id': 'parkrun_regular',
        'category': 'special',
        'emoji': '🌳',
        'name': 'Паркранер',
        'description': 'Участие в 10 паркранах',
        'level': 'green',
        'points': 30,
        'order': 5
    },
    'trail_runner': {
        'id': 'trail_runner',
        'category': 'special',
        'emoji': '⛰️',
        'name': 'Трейлраннер',
        'description': 'Участие в 5 трейловых забегах',
        'level': 'green',
        'points': 40,
        'order': 6
    },
    'night_runner': {
        'id': 'night_runner',
        'category': 'special',
        'emoji': '🌙',
        'name': 'Ночной бегун',
        'description': 'Участие в 3 ночных забегах',
        'level': 'green',
        'points': 30,
        'order': 7
    },
    'relay_team': {
        'id': 'relay_team',
        'category': 'special',
        'emoji': '🤝',
        'name': 'Командный игрок',
        'description': 'Участие в 3 эстафетах',
        'level': 'green',
        'points': 30,
        'order': 8
    },
    'virtual_runner': {
        'id': 'virtual_runner',
        'category': 'special',
        'emoji': '💻',
        'name': 'Виртуальный бегун',
        'description': 'Участие в 5 виртуальных забегах',
        'level': 'white',
        'points': 20,
        'order': 9
    },
    'charity_runner': {
        'id': 'charity_runner',
        'category': 'special',
        'emoji': '❤️',
        'name': 'Бегун с сердцем',
        'description': 'Участие в 3 благотворительных забегах',
        'level': 'green',
        'points': 40,
        'order': 10
    },
    'early_bird': {
        'id': 'early_bird',
        'category': 'special',
        'emoji': '🌅',
        'name': 'Ранняя пташка',
        'description': '10 утренних тренировок (до 7:00)',
        'level': 'white',
        'points': 20,
        'order': 11
    }
}


def get_achievement_by_id(achievement_id: str) -> dict:
    """Получить достижение по ID"""
    return ACHIEVEMENTS.get(achievement_id)


def get_achievements_by_category(category: str) -> list:
    """Получить все достижения категории"""
    return [
        ach for ach in ACHIEVEMENTS.values()
        if ach['category'] == category
    ]


def get_all_achievements() -> list:
    """Получить все достижения, отсортированные по категориям и порядку"""
    achievements = list(ACHIEVEMENTS.values())

    # Сортируем по категории и порядку
    achievements.sort(key=lambda x: (
        ACHIEVEMENT_CATEGORIES[x['category']]['order'],
        x['order']
    ))

    return achievements


def get_achievement_display_text(achievement_id: str, is_unlocked: bool = False) -> str:
    """
    Получить текст для отображения достижения

    Args:
        achievement_id: ID достижения
        is_unlocked: Разблокировано ли достижение

    Returns:
        Отформатированный текст достижения
    """
    ach = ACHIEVEMENTS.get(achievement_id)
    if not ach:
        return ""

    level_emoji = ACHIEVEMENT_LEVELS[ach['level']]['emoji']
    lock = "" if is_unlocked else "🔒 "
    check = "✅ " if is_unlocked else ""

    text = (
        f"{check}{lock}{ach['emoji']} {ach['name']} {level_emoji}\n"
        f"   {ach['description']}\n"
        f"   ⭐ {ach['points']} баллов"
    )

    return text


def get_category_achievements_text(category: str, user_achievements: list) -> str:
    """
    Получить текст со всеми достижениями категории

    Args:
        category: Категория достижений
        user_achievements: Список ID разблокированных достижений пользователя

    Returns:
        Отформатированный текст
    """
    cat_data = ACHIEVEMENT_CATEGORIES.get(category)
    if not cat_data:
        return ""

    achievements = get_achievements_by_category(category)
    achievements.sort(key=lambda x: x['order'])

    lines = [f"\n{cat_data['emoji']} {cat_data['name']}"]

    for ach in achievements:
        is_unlocked = ach['id'] in user_achievements
        lines.append(get_achievement_display_text(ach['id'], is_unlocked))

    return "\n".join(lines)
