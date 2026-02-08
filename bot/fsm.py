"""
FSM состояния для многошаговых операций
"""

from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """Состояния для регистрации нового пользователя"""

    # Последовательные этапы заполнения профиля при первом запуске
    waiting_for_name = State()          # Ввод имени
    waiting_for_birth_date = State()    # Ввод даты рождения через календарь
    waiting_for_gender = State()        # Выбор пола (мужской/женский)
    waiting_for_height = State()        # Ввод роста в см
    waiting_for_weight = State()        # Ввод веса в кг
    selecting_main_types = State()      # Выбор основных типов тренировок (кросс, плавание и т.д.)


class AddTrainingStates(StatesGroup):
    """Состояния для добавления тренировки"""

    # Базовые параметры для всех типов тренировок
    waiting_for_type = State()          # Выбор типа тренировки
    waiting_for_date = State()          # Выбор даты через календарь или быстрые кнопки
    waiting_for_time = State()          # Ввод продолжительности в формате ЧЧ:ММ:СС
    waiting_for_duration = State()      # Автоматически рассчитывается из времени

    # Для кросса, велотренировки (не используется в силовой и интервальной)
    waiting_for_distance = State()      # Ввод дистанции в км или милях

    # Специальные поля для плавания
    waiting_for_swimming_location = State()  # Выбор: бассейн или открытая вода
    waiting_for_pool_length = State()        # Длина бассейна: 25м или 50м
    waiting_for_swimming_styles = State()    # Выбор стилей: вольный, брасс, баттерфляй, на спине, IM
    waiting_for_swimming_sets = State()      # Описание отрезков (например: 8x100м)

    # Только для силовой тренировки
    waiting_for_exercises = State()     # Описание упражнений (жим, приседания и т.д.)

    # Только для интервальной тренировки
    waiting_for_intervals = State()     # Описание интервалов (разминка, работа, заминка)

    # Опциональные параметры для всех типов
    waiting_for_avg_pulse = State()     # Средний пульс в уд/мин
    waiting_for_max_pulse = State()     # Максимальный пульс в уд/мин

    # Завершающие шаги
    waiting_for_comment = State()       # Произвольный комментарий к тренировке
    waiting_for_fatigue = State()       # Оценка усилий от 1 до 10


class ExportPDFStates(StatesGroup):
    """Состояния для экспорта тренировок в PDF"""

    # Выбор произвольного диапазона дат
    waiting_for_start_date = State()    # Начальная дата периода
    waiting_for_end_date = State()      # Конечная дата периода


class SettingsStates(StatesGroup):
    """Состояния для изменения настроек"""

    # Изменение данных профиля
    waiting_for_name = State()                  # Смена имени
    waiting_for_birth_date = State()            # Смена даты рождения
    waiting_for_gender = State()                # Смена пола
    waiting_for_weight = State()                # Обновление веса
    waiting_for_height = State()                # Обновление роста
    selecting_main_types = State()              # Изменение основных типов тренировок

    # Настройка пульсовых зон
    waiting_for_max_pulse = State()             # Макс пульс для расчета зон
    waiting_for_zone_manual = State()           # Ручной ввод границ зон

    # Настройка целей тренировок
    waiting_for_weekly_volume = State()         # Целевой недельный километраж
    waiting_for_weekly_count = State()          # Целевое кол-во тренировок в неделю
    waiting_for_type_goal = State()             # Цель по конкретному типу тренировки
    waiting_for_weight_goal = State()           # Целевой вес

    # Настройка уведомлений
    waiting_for_daily_time = State()            # Время ежедневного напоминания
    waiting_for_report_time = State()           # Время недельного отчета

    # Настройка напоминаний о тренировках
    selecting_reminder_days = State()           # Дни недели для напоминаний
    waiting_for_reminder_time = State()         # Время напоминания


class CompetitionStates(StatesGroup):
    """Состояния для работы с соревнованиями"""

    # Регистрация на соревнование - установка целевого времени
    waiting_for_target_time = State()           # Ввод целевого времени при регистрации
    waiting_for_target_time_edit = State()      # Редактирование целевого времени
    user_editing_target_time = State()          # Пользователь редактирует цель
    waiting_for_target_time_after_accept = State()  # Ввод цели после подтверждения регистрации

    # Добавление результатов соревнования
    waiting_for_finish_time = State()           # Финишное время
    waiting_for_place_overall = State()         # Место в общем зачете
    waiting_for_place_age = State()             # Место в возрастной категории
    waiting_for_heart_rate = State()            # Средний пульс на соревновании
    waiting_for_result_comment = State()        # Комментарий о соревновании
    waiting_for_result_photo = State()          # Фото финишера

    # Редактирование результатов
    editing_finish_time = State()               # Корректировка финишного времени

    # Поиск соревнований
    waiting_for_search_query = State()          # Поисковый запрос (название/город)
    waiting_for_city = State()                  # Фильтр по городу

    # Создание пользовательского соревнования
    waiting_for_comp_name = State()             # Название соревнования
    waiting_for_comp_date = State()             # Дата проведения
    waiting_for_comp_type = State()             # Тип спорта (бег, плавание и т.д.)
    waiting_for_comp_distance = State()         # Дистанция
    waiting_for_comp_target = State()           # Целевое время
    waiting_for_coach_multi_target = State()    # Множественные цели для учеников (тренерский режим)
    waiting_for_comp_city = State()             # Город проведения
    waiting_for_comp_url = State()              # Ссылка на сайт соревнования

    # Добавление прошлых соревнований вручную
    waiting_for_past_comp_name = State()        # Название прошлого соревнования
    waiting_for_past_comp_city = State()        # Город
    waiting_for_past_comp_date = State()        # Дата проведения
    waiting_for_past_comp_type = State()        # Тип спорта
    waiting_for_past_comp_distance = State()    # Дистанция
    waiting_for_past_comp_result = State()      # Результат (время)
    waiting_for_past_comp_place_overall = State()  # Место в общем зачете
    waiting_for_past_comp_place_age = State()      # Место в возрастной группе
    waiting_for_past_comp_heart_rate = State()     # Средний пульс


class CoachStates(StatesGroup):
    """Состояния для работы с тренерским разделом"""

    # Подключение ученика
    waiting_for_coach_code = State()            # Ввод кода тренера

    # Управление учеником
    waiting_for_nickname = State()              # Установка никнейма ученику

    # Добавление комментария к тренировке ученика
    waiting_for_comment = State()               # Текст комментария

    # Добавление запланированной тренировки для ученика
    waiting_for_student_training_type = State()     # Тип тренировки
    waiting_for_student_training_date = State()     # Дата
    waiting_for_student_training_time = State()     # Продолжительность
    waiting_for_student_training_duration = State() # Длительность
    waiting_for_student_training_distance = State() # Дистанция
    waiting_for_student_training_exercises = State()# Упражнения (для силовой)
    waiting_for_student_training_intervals = State()# Интервалы (для интервальной)
    waiting_for_student_training_avg_pulse = State()# Целевой средний пульс
    waiting_for_student_training_max_pulse = State()# Целевой макс пульс
    waiting_for_student_training_comment = State()  # Комментарий от тренера
    waiting_for_student_training_fatigue = State()  # Ожидаемый уровень усилий

    # Регистрация ученика на соревнование
    waiting_for_student_target_time = State()       # Целевое время для ученика
    waiting_for_student_result_time = State()       # Результат ученика
    waiting_for_student_result_place = State()      # Место ученика
    waiting_for_student_result_heart_rate = State() # Пульс ученика
