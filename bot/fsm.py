"""
FSM состояния для многошаговых операций
"""

from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """Состояния для регистрации нового пользователя"""

    waiting_for_name = State()          # Имя пользователя
    waiting_for_birth_date = State()    # Дата рождения
    waiting_for_gender = State()        # Пол
    waiting_for_height = State()        # Рост
    waiting_for_weight = State()        # Вес
    selecting_main_types = State()      # Основные типы тренировок


class AddTrainingStates(StatesGroup):
    """Состояния для добавления тренировки"""
    
    # Общие поля для всех типов тренировок
    waiting_for_type = State()          # Выбор типа тренировки
    waiting_for_date = State()          # Дата тренировки
    waiting_for_time = State()          # Время (ЧЧ:ММ:СС)
    waiting_for_duration = State()      # Продолжительность (минуты)
    
    # Поля для тренировок с дистанцией (кросс, плавание, велотренировка)
    waiting_for_distance = State()      # Дистанция (км)
    
    # Поля для силовой тренировки
    waiting_for_exercises = State()     # Описание упражнений
    
    # Поля для интервальной тренировки
    waiting_for_intervals = State()     # Описание интервалов
    
    # Пульс для всех типов тренировок
    waiting_for_avg_pulse = State()     # Средний пульс
    waiting_for_max_pulse = State()     # Максимальный пульс
    
    # Общие завершающие поля
    waiting_for_comment = State()       # Комментарий
    waiting_for_fatigue = State()       # Уровень усилий (1-10)


class ExportPDFStates(StatesGroup):
    """Состояния для экспорта тренировок в PDF"""
    
    waiting_for_start_date = State()    # Начальная дата периода
    waiting_for_end_date = State()      # Конечная дата периода


class SettingsStates(StatesGroup):
    """Состояния для изменения настроек"""
    
    # Профиль (1-6)
    waiting_for_name = State()                  # 1. Имя
    waiting_for_birth_date = State()            # 2. Дата рождения
    waiting_for_gender = State()                # 3. Пол
    waiting_for_weight = State()                # 4. Вес
    waiting_for_height = State()                # 5. Рост
    selecting_main_types = State()              # 6. Основные типы тренировок
    
    # Пульсовые зоны (7)
    waiting_for_max_pulse = State()             # 7. Максимальный пульс для зон
    waiting_for_zone_manual = State()           # Ручная настройка зон
    
    # Цели (8-11)
    waiting_for_weekly_volume = State()         # 8. Целевой объем
    waiting_for_weekly_count = State()          # 9. Количество тренировок в неделю
    waiting_for_type_goal = State()             # 10. Цели по типам тренировок
    waiting_for_weight_goal = State()           # 11. Целевой вес
    
    # Уведомления (13-14)
    waiting_for_daily_time = State()            # 13. Время ежедневного сообщения
    waiting_for_report_time = State()           # 14. Время недельного отчета

    # Напоминания о тренировках (15)
    selecting_reminder_days = State()           # 15. Выбор дней для напоминаний
    waiting_for_reminder_time = State()         # 15. Время напоминаний о тренировках


class CompetitionStates(StatesGroup):
    """Состояния для работы с соревнованиями"""

    # Регистрация на соревнование
    waiting_for_target_time = State()           # Целевое время

    # Добавление результата
    waiting_for_finish_time = State()           # Финишное время
    waiting_for_place_overall = State()         # Место в общем зачёте
    waiting_for_place_age = State()             # Место в возрастной категории
    waiting_for_result_comment = State()        # Комментарий к результату
    waiting_for_result_photo = State()          # Фото финишера

    # Поиск соревнований
    waiting_for_search_query = State()          # Поисковый запрос
    waiting_for_city = State()                  # Город

    # Создание пользовательского соревнования
    waiting_for_comp_name = State()             # Название
    waiting_for_comp_date = State()             # Дата
    waiting_for_comp_city = State()             # Город
    waiting_for_comp_distances = State()        # Дистанции
    waiting_for_comp_url = State()              # URL сайта


class CoachStates(StatesGroup):
    """Состояния для работы с тренерским разделом"""

    # Добавление тренера (со стороны ученика)
    waiting_for_coach_code = State()            # Ввод кода тренера