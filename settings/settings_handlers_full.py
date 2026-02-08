"""
Полные обработчики настроек пользователя с всеми 14 пунктами
"""

from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from datetime import datetime
import re
import json

from bot.fsm import SettingsStates
from settings.settings_keyboards import (
    get_settings_menu_keyboard,
    get_profile_settings_keyboard,
    get_pulse_zones_menu_keyboard,
    get_goals_settings_keyboard,
    get_units_settings_keyboard,
    get_notifications_settings_keyboard,
    get_gender_keyboard,
    get_training_types_selection_keyboard,
    get_distance_unit_keyboard,
    get_weight_unit_keyboard,
    get_date_format_keyboard,
    get_timezone_keyboard,
    get_weekday_keyboard,
    get_training_type_goals_keyboard,
    get_simple_cancel_keyboard,
    get_cancel_delete_keyboard,
    get_training_reminder_toggle_keyboard,
    get_training_reminder_days_keyboard
)
from database.queries import (
    init_user_settings,
    get_user_settings,
    update_user_setting,
    set_pulse_zones_auto,
    set_pulse_zones_manual,
    get_pulse_zone_for_value,
    get_main_training_types,
    set_main_training_types,
    get_training_type_goals,
    set_training_type_goal,
    format_date_by_setting,
    recalculate_all_weights,
    get_training_statistics
)
from utils.goals_checker import check_weight_goal

router = Router()



async def format_birth_date(birth_date_str: str, user_id: int) -> str:
    """
    Форматирует дату рождения из формата БД (ГГГГ-ММ-ДД) в формат согласно настройкам пользователя
    
    Args:
        birth_date_str: Дата в формате ГГГГ-ММ-ДД
        user_id: ID пользователя для получения формата даты
        
    Returns:
        Отформатированная дата или 'не указана'
    """
    if not birth_date_str:
        return 'не указана'
    
    from utils.date_formatter import DateFormatter, get_user_date_format
    
    try:
        date_format = await get_user_date_format(user_id)
        return DateFormatter.format_date(birth_date_str, date_format)
    except:
        return birth_date_str



async def send_profile_menu(message: Message, user_id: int):
    """Отправить меню профиля"""
    settings = await get_user_settings(user_id)
    
    info_text = "👤 **Настройки профиля**\n\n"
    
    if settings:
        info_text += f"✏️ Имя: {settings.get('name') or 'не указано'}\n"
        birth_date_formatted = await format_birth_date(settings.get('birth_date'), user_id)
        info_text += f"🎂 Дата рождения: {birth_date_formatted}\n"

        gender = settings.get('gender')
        if gender == 'male':
            gender_text = '👨 Мужской'
        elif gender == 'female':
            gender_text = '👩 Женский'
        else:
            gender_text = 'не указан'
        info_text += f"⚧️ Пол: {gender_text}\n"

        weight_unit = settings.get('weight_unit', 'кг')
        weight_value = settings.get('weight')
        weight_display = f"{weight_value:.2f}" if weight_value else 'не указан'
        info_text += f"⚖️ Вес: {weight_display} {weight_unit}\n"
        info_text += f"📏 Рост: {settings.get('height') or 'не указан'} см\n"

        types = await get_main_training_types(user_id)
        info_text += f"🏃 Типы тренировок: {', '.join(types)}\n"
    
    info_text += "\nВыберите параметр для изменения:"
    
    await message.answer(
        info_text,
        reply_markup=get_profile_settings_keyboard(),
        parse_mode="Markdown"
    )


async def send_goals_menu(message: Message, user_id: int):
    """Отправить меню целей"""
    settings = await get_user_settings(user_id)

    info_text = "🎯 **Настройка целей**\n\n"

    if settings:
        distance_unit = settings.get('distance_unit', 'км')
        weight_unit = settings.get('weight_unit', 'кг')

        weekly_volume = settings.get('weekly_volume_goal')
        weekly_count = settings.get('weekly_trainings_goal')
        weight_goal = settings.get('weight_goal')

        stats = await get_training_statistics(user_id, 'week')
        current_volume = stats.get('total_distance', 0)
        current_count = stats.get('total_trainings', 0)

        if weekly_volume:
            progress_percent = (current_volume / weekly_volume * 100) if weekly_volume > 0 else 0
            info_text += f"📊 Недельный объем: {current_volume:.1f}/{weekly_volume} {distance_unit} ({progress_percent:.0f}%)\n"
        else:
            info_text += f"📊 Недельный объем: {current_volume:.1f} {distance_unit} (цель не задана)\n"

        if weekly_count:
            progress_percent = (current_count / weekly_count * 100) if weekly_count > 0 else 0
            info_text += f"🔢 Тренировок в неделю: {current_count}/{weekly_count} ({progress_percent:.0f}%)\n"
        else:
            info_text += f"🔢 Тренировок в неделю: {current_count} (цель не задана)\n"

        weight_goal_display = f"{weight_goal:.1f}" if weight_goal else 'не задан'
        info_text += f"⚖️ Целевой вес: {weight_goal_display} {weight_unit}\n\n"

        type_goals = await get_training_type_goals(user_id)
        if type_goals:
            info_text += "🏃 Цели по типам:\n"
            for t_type, goal in type_goals.items():
                unit = "мин/неделю" if t_type == 'силовая' else f"{distance_unit}/неделю"
                info_text += f"  • {t_type}: {goal} {unit}\n"
    else:
        info_text += "📊 Недельный объем: не задан км\n"
        info_text += "🔢 Тренировок в неделю: не задано\n"
        info_text += "⚖️ Целевой вес: не задан кг\n"

    info_text += "\nВыберите параметр для изменения:"

    await message.answer(
        info_text,
        reply_markup=get_goals_settings_keyboard(),
        parse_mode="Markdown"
    )


async def send_units_menu(message: Message, user_id: int):
    """Отправить меню единиц измерения"""
    settings = await get_user_settings(user_id)
    
    info_text = "📏 **Единицы измерения**\n\n"
    
    if settings:
        info_text += f"📏 Дистанция: {settings.get('distance_unit', 'км')}\n"
        info_text += f"⚖️ Вес: {settings.get('weight_unit', 'кг')}\n"
        info_text += f"📅 Формат даты: {settings.get('date_format', 'ДД.ММ.ГГГГ')}\n"
    
    info_text += "\nВыберите параметр для изменения:"
    
    await message.answer(
        info_text,
        reply_markup=get_units_settings_keyboard(),
        parse_mode="Markdown"
    )


async def send_notifications_menu(message: Message, user_id: int):
    """Отправить меню уведомлений"""
    settings = await get_user_settings(user_id)
    
    info_text = "🔔 **Настройка уведомлений**\n\n"
    
    if settings:
        daily_time = settings.get('daily_pulse_weight_time')
        report_day = settings.get('weekly_report_day', 'Понедельник')
        report_time = settings.get('weekly_report_time', '09:00')
        
        info_text += f"⏰ Время ежедневного ввода: {daily_time or 'не задано'}\n"
        info_text += f"📊 Недельный отчет: {report_day}, {report_time}\n"
    
    info_text += "\nВыберите параметр для изменения:"
    
    await message.answer(
        info_text,
        reply_markup=get_notifications_settings_keyboard(),
        parse_mode="Markdown"
    )



@router.message(F.text == "⚙️ Настройки")
@router.message(Command("settings"))
async def settings_menu(message: Message, state: FSMContext):
    """Главное меню настроек"""
    from coach.coach_queries import is_user_coach

    await state.clear()
    user_id = message.from_user.id
    await init_user_settings(user_id)

    settings = await get_user_settings(user_id)
    is_coach = await is_user_coach(user_id)

    info_text = "⚙️ **Настройки профиля**\n\n"

    if settings:
        info_text += f"👤 Имя: {settings.get('name') or 'не указано'}\n"
        birth_date_formatted = await format_birth_date(settings.get('birth_date'), user_id)
        info_text += f"🎂 Дата рождения: {birth_date_formatted}\n"

        gender = settings.get('gender')
        if gender == 'male':
            gender_text = '👨 Мужской'
        elif gender == 'female':
            gender_text = '👩 Женский'
        else:
            gender_text = 'не указан'
        info_text += f"⚧️ Пол: {gender_text}\n"

        weight_value = settings.get('weight')
        weight_unit = settings.get('weight_unit', 'кг')
        weight_display = f"{weight_value:.1f}" if weight_value else 'не указан'
        info_text += f"⚖️ Вес: {weight_display} {weight_unit}\n"
        info_text += f"📏 Рост: {settings.get('height') or 'не указан'} см\n"

    info_text += "\nВыберите раздел для настройки:"

    from aiogram.types import ReplyKeyboardRemove
    await message.answer(
        info_text,
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    await message.answer(
        "Выберите раздел:",
        reply_markup=get_settings_menu_keyboard(is_coach),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "settings:menu")
async def callback_settings_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню настроек"""
    from coach.coach_queries import is_user_coach

    await state.clear()
    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)
    is_coach = await is_user_coach(user_id)

    info_text = "⚙️ **Настройки профиля**\n\n"

    if settings:
        info_text += f"👤 Имя: {settings.get('name') or 'не указано'}\n"
        birth_date_formatted = await format_birth_date(settings.get('birth_date'), user_id)
        info_text += f"🎂 Дата рождения: {birth_date_formatted}\n"

        gender = settings.get('gender')
        if gender == 'male':
            gender_text = '👨 Мужской'
        elif gender == 'female':
            gender_text = '👩 Женский'
        else:
            gender_text = 'не указан'
        info_text += f"⚧️ Пол: {gender_text}\n"

        weight_value = settings.get('weight')
        weight_unit = settings.get('weight_unit', 'кг')
        weight_display = f"{weight_value:.1f}" if weight_value else 'не указан'
        info_text += f"⚖️ Вес: {weight_display} {weight_unit}\n"
        info_text += f"📏 Рост: {settings.get('height') or 'не указан'} см\n"

    info_text += "\nВыберите раздел для настройки:"

    await callback.message.edit_text(
        info_text,
        reply_markup=get_settings_menu_keyboard(is_coach),
        parse_mode="Markdown"
    )
    await callback.answer()



@router.callback_query(F.data == "settings:profile")
async def callback_profile_settings(callback: CallbackQuery):
    """Меню настроек профиля"""
    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)
    
    info_text = "👤 **Настройки профиля**\n\n"
    
    if settings:
        info_text += f"✏️ Имя: {settings.get('name') or 'не указано'}\n"
        birth_date_formatted = await format_birth_date(settings.get('birth_date'), user_id)
        info_text += f"🎂 Дата рождения: {birth_date_formatted}\n"

        gender = settings.get('gender')
        if gender == 'male':
            gender_text = '👨 Мужской'
        elif gender == 'female':
            gender_text = '👩 Женский'
        else:
            gender_text = 'не указан'
        info_text += f"⚧️ Пол: {gender_text}\n"

        weight_value = settings.get('weight')
        weight_unit = settings.get('weight_unit', 'кг')
        weight_display = f"{weight_value:.1f}" if weight_value else 'не указан'
        info_text += f"⚖️ Вес: {weight_display} {weight_unit}\n"
        info_text += f"📏 Рост: {settings.get('height') or 'не указан'} см\n"

        types = await get_main_training_types(user_id)
        types_display = ', '.join(types) if types else 'не выбраны'
        info_text += f"🏃 Типы тренировок: {types_display}\n"
    
    info_text += "\nВыберите параметр для изменения:"
    
    await callback.message.edit_text(
        info_text,
        reply_markup=get_profile_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "settings:profile:name")
async def callback_set_name(callback: CallbackQuery, state: FSMContext):
    """Начало установки имени"""
    await callback.message.answer(
        "✏️ Введите ваше имя (минимум 2 символа, максимум 50):",
        reply_markup=get_simple_cancel_keyboard()
    )
    await state.set_state(SettingsStates.waiting_for_name)
    await callback.answer()


@router.message(SettingsStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка ввода имени"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=ReplyKeyboardRemove())
        await send_profile_menu(message, message.from_user.id)
        return
    
    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer("❌ Имя слишком короткое. Минимум 2 символа.")
        return
    
    if len(name) > 50:
        await message.answer("❌ Имя слишком длинное. Максимум 50 символов.")
        return
    
    user_id = message.from_user.id
    await update_user_setting(user_id, 'name', name)
    
    await message.answer(
        f"✅ Имя успешно сохранено: {name}",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()
    await send_profile_menu(message, user_id)


@router.callback_query(F.data == "settings:profile:birth_date")
async def callback_set_birth_date(callback: CallbackQuery, state: FSMContext):
    """Начало установки даты рождения"""
    from bot.calendar_keyboard import CalendarKeyboard
    from datetime import datetime

    calendar = CalendarKeyboard.create_calendar(1, datetime.now(), "cal_birth", max_date=datetime.now())
    await callback.message.answer(
        "🎂 Выберите дату рождения из календаря:\n\n"
        "📌 Каждый год в день рождения вы будете получать поздравительное сообщение!",
        reply_markup=calendar
    )
    await state.set_state(SettingsStates.waiting_for_birth_date)
    await callback.answer()


@router.message(SettingsStates.waiting_for_birth_date)
async def process_birth_date(message: Message, state: FSMContext):
    """Обработка ввода даты рождения"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=ReplyKeyboardRemove())
        await send_profile_menu(message, message.from_user.id)
        return
    
    date_pattern = r'(\d{2})\.(\d{2})\.(\d{4})'
    match = re.match(date_pattern, message.text.strip())
    
    if not match:
        await message.answer(
            "❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ (например: 15.03.1990)"
        )
        return
    
    day, month, year = match.groups()
    
    try:
        birth_date = datetime(int(year), int(month), int(day))
        
        if birth_date > datetime.now():
            await message.answer("❌ Дата рождения не может быть в будущем!")
            return
        
        age = (datetime.now() - birth_date).days // 365
        if age < 5 or age > 120:
            await message.answer("❌ Пожалуйста, введите корректную дату рождения.")
            return
        
        user_id = message.from_user.id
        birth_date_str = birth_date.strftime('%Y-%m-%d')
        await update_user_setting(user_id, 'birth_date', birth_date_str)
        
        await message.answer(
            f"✅ Дата рождения сохранена: {day}.{month}.{year}\n"
            f"🎉 Ваш возраст: {age} лет",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        
        await send_profile_menu(message, user_id)
        
    except ValueError:
        await message.answer("❌ Некорректная дата. Проверьте правильность ввода.")


@router.callback_query(F.data == "settings:profile:gender")
async def callback_set_gender(callback: CallbackQuery):
    """Выбор пола"""
    await callback.message.edit_text(
        "⚧️ Выберите ваш пол:",
        reply_markup=get_gender_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("gender:"))
async def callback_save_gender(callback: CallbackQuery):
    """Сохранение пола"""
    gender_map = {
        "gender:male": "мужской",
        "gender:female": "женский"
    }

    gender = gender_map.get(callback.data)
    if gender:
        user_id = callback.from_user.id
        await update_user_setting(user_id, 'gender', gender)

        settings = await get_user_settings(user_id)

        info_text = "👤 **Настройки профиля**\n\n"

        if settings:
            info_text += f"✏️ Имя: {settings.get('name') or 'не указано'}\n"
            birth_date_formatted = await format_birth_date(settings.get('birth_date'), user_id)
            info_text += f"🎂 Дата рождения: {birth_date_formatted}\n"

            gender = settings.get('gender')
            if gender == 'male' or gender == 'мужской':
                gender_text = '👨 Мужской'
            elif gender == 'female' or gender == 'женский':
                gender_text = '👩 Женский'
            else:
                gender_text = 'не указан'
            info_text += f"⚧️ Пол: {gender_text}\n"

            weight_unit = settings.get('weight_unit', 'кг')
            info_text += f"⚖️ Вес: {settings.get('weight') or 'не указан'} {weight_unit}\n"
            info_text += f"📏 Рост: {settings.get('height') or 'не указан'} см\n"

            types = await get_main_training_types(user_id)
            info_text += f"🏃 Типы тренировок: {', '.join(types)}\n"

        info_text += "\nВыберите параметр для изменения:"

        await callback.message.edit_text(
            info_text,
            reply_markup=get_profile_settings_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer("Сохранено!")
    else:
        await callback.answer("Ошибка!")


@router.callback_query(F.data == "settings:profile:weight")
async def callback_set_weight(callback: CallbackQuery, state: FSMContext):
    """Начало установки веса"""
    settings = await get_user_settings(callback.from_user.id)
    weight_unit = settings.get('weight_unit', 'кг') if settings else 'кг'
    
    await callback.message.answer(
        f"⚖️ Введите ваш вес в {weight_unit} (например: 70.5):",
        reply_markup=get_simple_cancel_keyboard()
    )
    await state.set_state(SettingsStates.waiting_for_weight)
    await callback.answer()


@router.message(SettingsStates.waiting_for_weight)
async def process_weight(message: Message, state: FSMContext):
    """Обработка ввода веса"""
    if message.text == "❌ Отмена":
        await state.clear()
        await send_profile_menu(message, message.from_user.id)
        return
    
    try:
        weight = float(message.text.strip().replace(',', '.'))
        
        if weight <= 0 or weight > 500:
            await message.answer("❌ Пожалуйста, введите корректное значение веса (0-500).")
            return
        
        user_id = message.from_user.id
        await update_user_setting(user_id, 'weight', weight)

        settings = await get_user_settings(user_id)
        weight_unit = settings.get('weight_unit', 'кг')

        try:
            await check_weight_goal(user_id, weight, message.bot)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка при проверке целевого веса: {str(e)}")

        await message.answer(
            f"✅ Вес сохранен: {weight} {weight_unit}",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()

        await send_profile_menu(message, user_id)
        
    except ValueError:
        await message.answer("❌ Некорректное значение. Введите число (например: 70.5)")


@router.callback_query(F.data == "settings:profile:height")
async def callback_set_height(callback: CallbackQuery, state: FSMContext):
    """Начало установки роста"""
    await callback.message.answer(
        "📏 Введите ваш рост в сантиметрах (например: 175):",
        reply_markup=get_simple_cancel_keyboard()
    )
    await state.set_state(SettingsStates.waiting_for_height)
    await callback.answer()


@router.message(SettingsStates.waiting_for_height)
async def process_height(message: Message, state: FSMContext):
    """Обработка ввода роста"""
    if message.text == "❌ Отмена":
        await state.clear()
        await send_profile_menu(message, message.from_user.id)
        return
    
    try:
        height = float(message.text.strip().replace(',', '.'))
        
        if height <= 50 or height > 300:
            await message.answer("❌ Пожалуйста, введите корректное значение роста (50-300 см).")
            return
        
        user_id = message.from_user.id
        await update_user_setting(user_id, 'height', height)
        
        await message.answer(
            f"✅ Рост сохранен: {height} см",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        await send_profile_menu(message, message.from_user.id)
        
    except ValueError:
        await message.answer("❌ Некорректное значение. Введите число (например: 175)")


@router.callback_query(F.data == "settings:profile:main_types")
async def callback_set_main_types(callback: CallbackQuery, state: FSMContext):
    """Выбор основных типов тренировок"""
    user_id = callback.from_user.id
    selected_types = await get_main_training_types(user_id)
    
    await state.update_data(selected_types=selected_types)
    
    await callback.message.edit_text(
        "🏃 **Выберите основные типы тренировок**\n\n"
        "Эти типы будут доступны при добавлении тренировок.\n"
        "Вы можете выбрать несколько типов.",
        reply_markup=get_training_types_selection_keyboard(selected_types),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_type:"))
async def callback_toggle_type(callback: CallbackQuery, state: FSMContext):
    """Переключение выбора типа тренировки"""
    training_type = callback.data.split(":")[1]
    
    data = await state.get_data()
    selected_types = data.get('selected_types', [])
    
    if training_type in selected_types:
        selected_types.remove(training_type)
    else:
        selected_types.append(training_type)
    
    await state.update_data(selected_types=selected_types)
    
    await callback.message.edit_reply_markup(
        reply_markup=get_training_types_selection_keyboard(selected_types)
    )
    await callback.answer()


@router.callback_query(F.data == "save_training_types")
async def callback_save_training_types(callback: CallbackQuery, state: FSMContext):
    """Сохранение выбранных типов тренировок"""
    data = await state.get_data()
    selected_types = data.get('selected_types', ['кросс'])

    if not selected_types:
        await callback.answer("❌ Выберите хотя бы один тип тренировки!", show_alert=True)
        return

    user_id = callback.from_user.id
    await set_main_training_types(user_id, selected_types)
    await state.clear()

    settings = await get_user_settings(user_id)

    info_text = "👤 **Настройки профиля**\n\n"

    if settings:
        info_text += f"✏️ Имя: {settings.get('name') or 'не указано'}\n"
        birth_date_formatted = await format_birth_date(settings.get('birth_date'), user_id)
        info_text += f"🎂 Дата рождения: {birth_date_formatted}\n"

        gender = settings.get('gender')
        if gender == 'male' or gender == 'мужской':
            gender_text = '👨 Мужской'
        elif gender == 'female' or gender == 'женский':
            gender_text = '👩 Женский'
        else:
            gender_text = 'не указан'
        info_text += f"⚧️ Пол: {gender_text}\n"

        weight_value = settings.get('weight')
        weight_unit = settings.get('weight_unit', 'кг')
        weight_display = f"{weight_value:.1f}" if weight_value else 'не указан'
        info_text += f"⚖️ Вес: {weight_display} {weight_unit}\n"
        info_text += f"📏 Рост: {settings.get('height') or 'не указан'} см\n"

        types = await get_main_training_types(user_id)
        info_text += f"🏃 Типы тренировок: {', '.join(types)}\n"

    info_text += "\nВыберите параметр для изменения:"

    await callback.message.edit_text(
        info_text,
        reply_markup=get_profile_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer("Сохранено!")



async def send_pulse_zones_menu(message: Message, user_id: int):
    """Отправить меню пульсовых зон"""
    settings = await get_user_settings(user_id)

    info_text = "💓 **Настройка пульсовых зон**\n\n"

    if settings and settings.get('max_pulse'):
        info_text += f"Максимальный пульс: {settings['max_pulse']} уд/мин\n\n"
        info_text += "Ваши зоны:\n"
        info_text += f"🟢 Зона 1: {settings['zone1_min']}-{settings['zone1_max']} (восстановление)\n"
        info_text += f"🔵 Зона 2: {settings['zone2_min']}-{settings['zone2_max']} (аэробная)\n"
        info_text += f"🟡 Зона 3: {settings['zone3_min']}-{settings['zone3_max']} (темповая)\n"
        info_text += f"🟠 Зона 4: {settings['zone4_min']}-{settings['zone4_max']} (анаэробная)\n"
        info_text += f"🔴 Зона 5: {settings['zone5_min']}-{settings['zone5_max']} (максимальная)\n"
    else:
        info_text += "Пульсовые зоны не настроены.\n"
        info_text += "Настройте зоны для более точного анализа тренировок."

    await message.answer(
        info_text,
        reply_markup=get_pulse_zones_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "settings:pulse_zones")
async def callback_pulse_zones_menu(callback: CallbackQuery):
    """Меню настройки пульсовых зон"""
    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)

    info_text = "💓 **Настройка пульсовых зон**\n\n"

    if settings and settings.get('max_pulse'):
        info_text += f"Максимальный пульс: {settings['max_pulse']} уд/мин\n\n"
        info_text += "Ваши зоны:\n"
        info_text += f"🟢 Зона 1: {settings['zone1_min']}-{settings['zone1_max']} (восстановление)\n"
        info_text += f"🔵 Зона 2: {settings['zone2_min']}-{settings['zone2_max']} (аэробная)\n"
        info_text += f"🟡 Зона 3: {settings['zone3_min']}-{settings['zone3_max']} (темповая)\n"
        info_text += f"🟠 Зона 4: {settings['zone4_min']}-{settings['zone4_max']} (анаэробная)\n"
        info_text += f"🔴 Зона 5: {settings['zone5_min']}-{settings['zone5_max']} (максимальная)\n"
    else:
        info_text += "Пульсовые зоны не настроены.\n"
        info_text += "Настройте зоны для более точного анализа тренировок."

    await callback.message.edit_text(
        info_text,
        reply_markup=get_pulse_zones_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()




@router.callback_query(F.data == "settings:pulse:manual")
async def callback_pulse_manual(callback: CallbackQuery, state: FSMContext):
    """Ручной ввод максимального пульса"""
    await callback.message.answer(
        "💓 Введите ваш максимальный пульс (уд/мин):\n\n"
        "Пульсовые зоны будут рассчитаны автоматически.",
        reply_markup=get_simple_cancel_keyboard()
    )
    await state.set_state(SettingsStates.waiting_for_max_pulse)
    await callback.answer()


@router.message(SettingsStates.waiting_for_max_pulse)
async def process_max_pulse(message: Message, state: FSMContext):
    """Обработка ввода максимального пульса"""
    if message.text == "❌ Отмена":
        await state.clear()
        await send_pulse_zones_menu(message, message.from_user.id)
        return
    
    try:
        max_pulse = int(message.text.strip())

        if max_pulse < 80 or max_pulse > 220:
            await message.answer("❌ Введите корректное значение (80-220 уд/мин).")
            return
        
        user_id = message.from_user.id
        await set_pulse_zones_manual(user_id, max_pulse)
        
        settings = await get_user_settings(user_id)
        
        await message.answer(
            f"✅ Пульсовые зоны настроены!\n\n"
            f"Максимальный пульс: {max_pulse} уд/мин\n\n"
            f"🟢 Зона 1: {settings['zone1_min']}-{settings['zone1_max']}\n"
            f"🔵 Зона 2: {settings['zone2_min']}-{settings['zone2_max']}\n"
            f"🟡 Зона 3: {settings['zone3_min']}-{settings['zone3_max']}\n"
            f"🟠 Зона 4: {settings['zone4_min']}-{settings['zone4_max']}\n"
            f"🔴 Зона 5: {settings['zone5_min']}-{settings['zone5_max']}\n",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        await send_pulse_zones_menu(message, user_id)
        
    except ValueError:
        await message.answer("❌ Введите целое число.")





@router.callback_query(F.data == "settings:goals")
async def callback_goals_menu(callback: CallbackQuery):
    """Меню настройки целей"""
    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)

    info_text = "🎯 **Настройка целей**\n\n"

    if settings:
        distance_unit = settings.get('distance_unit', 'км')
        weight_unit = settings.get('weight_unit', 'кг')

        weekly_volume = settings.get('weekly_volume_goal')
        weekly_count = settings.get('weekly_trainings_goal')
        weight_goal = settings.get('weight_goal')

        stats = await get_training_statistics(user_id, 'week')
        current_volume = stats.get('total_distance', 0)
        current_count = stats.get('total_trainings', 0)

        if weekly_volume:
            progress_percent = (current_volume / weekly_volume * 100) if weekly_volume > 0 else 0
            info_text += f"📊 Недельный объем: {current_volume:.1f}/{weekly_volume} {distance_unit} ({progress_percent:.0f}%)\n"
        else:
            info_text += f"📊 Недельный объем: {current_volume:.1f} {distance_unit} (цель не задана)\n"

        if weekly_count:
            progress_percent = (current_count / weekly_count * 100) if weekly_count > 0 else 0
            info_text += f"🔢 Тренировок в неделю: {current_count}/{weekly_count} ({progress_percent:.0f}%)\n"
        else:
            info_text += f"🔢 Тренировок в неделю: {current_count} (цель не задана)\n"

        weight_goal_display = f"{weight_goal:.1f}" if weight_goal else 'не задан'
        info_text += f"⚖️ Целевой вес: {weight_goal_display} {weight_unit}\n\n"

        type_goals = await get_training_type_goals(user_id)
        if type_goals:
            info_text += "🏃 Цели по типам:\n"
            for t_type, goal in type_goals.items():
                unit = "мин/неделю" if t_type == 'силовая' else f"{distance_unit}/неделю"
                info_text += f"  • {t_type}: {goal} {unit}\n"
    else:
        info_text += "📊 Недельный объем: не задан км\n"
        info_text += "🔢 Тренировок в неделю: не задано\n"
        info_text += "⚖️ Целевой вес: не задан кг\n"

    info_text += "\nВыберите параметр для изменения:"

    await callback.message.edit_text(
        info_text,
        reply_markup=get_goals_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "settings:goals:volume")
async def callback_set_weekly_volume(callback: CallbackQuery, state: FSMContext):
    """Установка целевого недельного объема"""
    settings = await get_user_settings(callback.from_user.id)
    distance_unit = settings.get('distance_unit', 'км') if settings else 'км'
    current_goal = settings.get('weekly_volume_goal') if settings else None

    message_text = f"📊 Введите целевой объем тренировок в неделю ({distance_unit}):\n\n"
    if current_goal:
        message_text += f"Текущая цель: {current_goal} {distance_unit}\n\n"
    message_text += "Например: 30"

    keyboard = get_cancel_delete_keyboard() if current_goal else get_simple_cancel_keyboard()

    await callback.message.answer(
        message_text,
        reply_markup=keyboard
    )
    await state.set_state(SettingsStates.waiting_for_weekly_volume)
    await callback.answer()


@router.message(SettingsStates.waiting_for_weekly_volume)
async def process_weekly_volume(message: Message, state: FSMContext):
    """Обработка ввода недельного объема"""
    if message.text == "❌ Отмена":
        await state.clear()
        await send_goals_menu(message, message.from_user.id)
        return

    if message.text == "🗑 Удалить цель":
        user_id = message.from_user.id
        await update_user_setting(user_id, 'weekly_volume_goal', None)
        await message.answer(
            "✅ Цель по недельному объёму удалена",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        await send_goals_menu(message, user_id)
        return

    try:
        volume = float(message.text.strip().replace(',', '.'))

        if volume <= 0 or volume > 1000:
            await message.answer("❌ Введите корректное значение (1-1000).")
            return

        user_id = message.from_user.id
        settings = await get_user_settings(user_id)
        distance_unit = settings.get('distance_unit', 'км')

        await update_user_setting(user_id, 'weekly_volume_goal', volume)
        await message.answer(
            f"✅ Целевой недельный объем сохранен: {volume} {distance_unit}",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        await send_goals_menu(message, message.from_user.id)

    except ValueError:
        await message.answer("❌ Введите число (например: 30)")


@router.callback_query(F.data == "settings:goals:count")
async def callback_set_weekly_count(callback: CallbackQuery, state: FSMContext):
    """Установка целевого количества тренировок"""
    settings = await get_user_settings(callback.from_user.id)
    current_goal = settings.get('weekly_trainings_goal') if settings else None

    message_text = "🔢 Введите целевое количество тренировок в неделю:\n\n"
    if current_goal:
        message_text += f"Текущая цель: {current_goal} тренировок\n\n"
    message_text += "Например: 5"

    keyboard = get_cancel_delete_keyboard() if current_goal else get_simple_cancel_keyboard()

    await callback.message.answer(
        message_text,
        reply_markup=keyboard
    )
    await state.set_state(SettingsStates.waiting_for_weekly_count)
    await callback.answer()


@router.message(SettingsStates.waiting_for_weekly_count)
async def process_weekly_count(message: Message, state: FSMContext):
    """Обработка ввода количества тренировок"""
    if message.text == "❌ Отмена":
        await state.clear()
        await send_goals_menu(message, message.from_user.id)
        return

    if message.text == "🗑 Удалить цель":
        user_id = message.from_user.id
        await update_user_setting(user_id, 'weekly_trainings_goal', None)
        await message.answer(
            "✅ Цель по количеству тренировок удалена",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        await send_goals_menu(message, user_id)
        return

    try:
        count = int(message.text.strip())

        if count <= 0 or count > 30:
            await message.answer("❌ Введите корректное значение (1-30).")
            return

        user_id = message.from_user.id

        await update_user_setting(user_id, 'weekly_trainings_goal', count)
        await message.answer(
            f"✅ Целевое количество тренировок сохранено: {count} в неделю",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        await send_goals_menu(message, message.from_user.id)

    except ValueError:
        await message.answer("❌ Введите целое число.")


@router.callback_query(F.data == "settings:goals:by_type")
async def callback_set_type_goals(callback: CallbackQuery):
    """Выбор типа тренировки для установки цели"""
    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)
    distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

    main_types = await get_main_training_types(user_id)

    type_goals = await get_training_type_goals(user_id)

    await callback.message.edit_text(
        "🏃 **Цели по типам тренировок**\n\n"
        "Выберите тип тренировки для установки цели:",
        reply_markup=get_training_type_goals_keyboard(main_types, type_goals, distance_unit),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("type_goal:"))
async def callback_type_goal_input(callback: CallbackQuery, state: FSMContext):
    """Ввод цели для конкретного типа"""
    training_type = callback.data.split(":")[1]

    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)
    distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

    type_goals = await get_training_type_goals(user_id)
    current_goal = type_goals.get(training_type)

    await state.update_data(
        current_type_goal=training_type,
        type_goals_message_id=callback.message.message_id
    )

    if training_type == 'силовая':
        message_text = f"🎯 Введите цель для типа '{training_type}' в минутах/неделю:\n\n"
        if current_goal:
            message_text += f"Текущая цель: {current_goal} мин/неделю\n\n"
        message_text += "Например: 120 (2 часа в неделю)"
        keyboard = get_cancel_delete_keyboard() if current_goal else get_simple_cancel_keyboard()
        await callback.message.answer(
            message_text,
            reply_markup=keyboard
        )
    else:
        message_text = f"🎯 Введите цель для типа '{training_type}' в {distance_unit}/неделю:\n\n"
        if current_goal:
            message_text += f"Текущая цель: {current_goal} {distance_unit}/неделю\n\n"
        message_text += f"Например: 20"
        keyboard = get_cancel_delete_keyboard() if current_goal else get_simple_cancel_keyboard()
        await callback.message.answer(
            message_text,
            reply_markup=keyboard
        )

    await state.set_state(SettingsStates.waiting_for_type_goal)
    await callback.answer()


@router.message(SettingsStates.waiting_for_type_goal)
async def process_type_goal(message: Message, state: FSMContext):
    """Обработка ввода цели по типу"""
    data = await state.get_data()
    training_type = data.get('current_type_goal')
    type_goals_message_id = data.get('type_goals_message_id')
    user_id = message.from_user.id

    if message.text == "❌ Отмена":
        await state.clear()

        settings = await get_user_settings(user_id)
        distance_unit = settings.get('distance_unit', 'км') if settings else 'км'
        main_types = await get_main_training_types(user_id)
        type_goals = await get_training_type_goals(user_id)

        await message.answer(
            "🏃 **Цели по типам тренировок**\n\n"
            "Выберите тип тренировки для установки цели:",
            reply_markup=get_training_type_goals_keyboard(main_types, type_goals, distance_unit),
            parse_mode="Markdown"
        )
        return

    if message.text == "🗑 Удалить цель":
        await set_training_type_goal(user_id, training_type, None)
        await message.answer(
            f"✅ Цель для '{training_type}' удалена",
            reply_markup=ReplyKeyboardRemove()
        )

        await state.clear()

        settings = await get_user_settings(user_id)
        distance_unit = settings.get('distance_unit', 'км')
        main_types = await get_main_training_types(user_id)
        type_goals = await get_training_type_goals(user_id)

        await message.answer(
            "🏃 **Цели по типам тренировок**\n\n"
            "Выберите тип тренировки для установки цели:",
            reply_markup=get_training_type_goals_keyboard(main_types, type_goals, distance_unit),
            parse_mode="Markdown"
        )
        return

    try:
        goal = float(message.text.strip().replace(',', '.'))

        if goal < 0 or goal > 500:
            await message.answer("❌ Введите корректное значение (0-500).")
            return

        data = await state.get_data()
        training_type = data.get('current_type_goal')

        user_id = message.from_user.id
        settings = await get_user_settings(user_id)
        distance_unit = settings.get('distance_unit', 'км')

        if training_type == 'силовая':
            unit_text = "мин/неделю"
        else:
            unit_text = f"{distance_unit}/неделю"

        await set_training_type_goal(user_id, training_type, goal)
        await message.answer(
            f"✅ Цель для '{training_type}' сохранена: {goal} {unit_text}",
            reply_markup=ReplyKeyboardRemove()
        )

        await state.clear()

        main_types = await get_main_training_types(user_id)
        type_goals = await get_training_type_goals(user_id)

        await message.answer(
            "🏃 **Цели по типам тренировок**\n\n"
            "Выберите тип тренировки для установки цели:",
            reply_markup=get_training_type_goals_keyboard(main_types, type_goals, distance_unit),
            parse_mode="Markdown"
        )

    except ValueError:
        await message.answer("❌ Введите число.")


@router.callback_query(F.data == "settings:goals:weight")
async def callback_set_weight_goal(callback: CallbackQuery, state: FSMContext):
    """Установка целевого веса"""
    settings = await get_user_settings(callback.from_user.id)
    weight_unit = settings.get('weight_unit', 'кг') if settings else 'кг'
    current_goal = settings.get('weight_goal') if settings else None

    message_text = f"⚖️ Введите целевой вес в {weight_unit}:\n\n"
    if current_goal:
        message_text += f"Текущая цель: {current_goal:.1f} {weight_unit}\n\n"
    message_text += f"Например: 75"

    keyboard = get_cancel_delete_keyboard() if current_goal else get_simple_cancel_keyboard()

    await callback.message.answer(
        message_text,
        reply_markup=keyboard
    )
    await state.set_state(SettingsStates.waiting_for_weight_goal)
    await callback.answer()


@router.message(SettingsStates.waiting_for_weight_goal)
async def process_weight_goal(message: Message, state: FSMContext):
    """Обработка ввода целевого веса"""
    if message.text == "❌ Отмена":
        await state.clear()
        await send_goals_menu(message, message.from_user.id)
        return

    if message.text == "🗑 Удалить цель":
        user_id = message.from_user.id
        await update_user_setting(user_id, 'weight_goal', None)
        await message.answer(
            "✅ Целевой вес удалён",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        await send_goals_menu(message, user_id)
        return

    try:
        weight_goal = float(message.text.strip().replace(',', '.'))

        user_id = message.from_user.id
        settings = await get_user_settings(user_id)
        weight_unit = settings.get('weight_unit', 'кг')

        if weight_unit == 'кг':
            min_weight, max_weight = 30, 200
        else:  
            min_weight, max_weight = 66, 440

        if weight_goal < min_weight or weight_goal > max_weight:
            await message.answer(
                f"❌ Введите корректное значение ({min_weight}-{max_weight} {weight_unit})."
            )
            return

        await update_user_setting(user_id, 'weight_goal', weight_goal)
        await message.answer(
            f"✅ Целевой вес сохранен: {weight_goal} {weight_unit}",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        await send_goals_menu(message, message.from_user.id)

    except ValueError:
        await message.answer("❌ Введите число.")



@router.callback_query(F.data == "settings:units")
async def callback_units_menu(callback: CallbackQuery):
    """Меню единиц измерения"""
    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)

    info_text = "📏 **Единицы измерения**\n\n"

    if settings:
        info_text += f"📏 Дистанция: {settings.get('distance_unit', 'км')}\n"
        info_text += f"⚖️ Вес: {settings.get('weight_unit', 'кг')}\n"
        info_text += f"📅 Формат даты: {settings.get('date_format', 'ДД.ММ.ГГГГ')}\n"
        info_text += f"🌍 Часовой пояс: {settings.get('timezone', 'Europe/Moscow')}\n"

    info_text += "\nВыберите параметр для изменения:"

    await callback.message.edit_text(
        info_text,
        reply_markup=get_units_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "settings:units:distance")
async def callback_set_distance_unit(callback: CallbackQuery):
    """Выбор единицы дистанции"""
    await callback.message.edit_text(
        "📏 Выберите единицу измерения дистанции:",
        reply_markup=get_distance_unit_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("distance_unit:"))
async def callback_save_distance_unit(callback: CallbackQuery):
    """Сохранение единицы дистанции"""
    unit = callback.data.split(":")[1]

    user_id = callback.from_user.id
    await update_user_setting(user_id, 'distance_unit', unit)

    settings = await get_user_settings(user_id)

    info_text = "📏 **Единицы измерения**\n\n"

    if settings:
        info_text += f"📏 Дистанция: {settings.get('distance_unit', 'км')}\n"
        info_text += f"⚖️ Вес: {settings.get('weight_unit', 'кг')}\n"
        info_text += f"📅 Формат даты: {settings.get('date_format', 'ДД.ММ.ГГГГ')}\n"

    info_text += "\nВыберите параметр для изменения:"

    await callback.message.edit_text(
        info_text,
        reply_markup=get_units_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer("Сохранено!")


@router.callback_query(F.data == "settings:units:weight")
async def callback_set_weight_unit(callback: CallbackQuery):
    """Выбор единицы веса"""
    await callback.message.edit_text(
        "⚖️ Выберите единицу измерения веса:",
        reply_markup=get_weight_unit_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("weight_unit:"))
async def callback_save_weight_unit(callback: CallbackQuery):
    """Сохранение единицы веса с автоматическим пересчетом"""
    new_unit = callback.data.split(":")[1]

    user_id = callback.from_user.id

    settings = await get_user_settings(user_id)
    old_unit = settings.get('weight_unit', 'кг') if settings else 'кг'

    if old_unit == new_unit:
        info_text = "📏 **Единицы измерения**\n\n"

        if settings:
            info_text += f"📏 Дистанция: {settings.get('distance_unit', 'км')}\n"
            info_text += f"⚖️ Вес: {settings.get('weight_unit', 'кг')}\n"
            info_text += f"📅 Формат даты: {settings.get('date_format', 'ДД.ММ.ГГГГ')}\n"

        info_text += "\nВыберите параметр для изменения:"

        await callback.message.edit_text(
            info_text,
            reply_markup=get_units_settings_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer("Единица измерения не изменена")
        return

    await recalculate_all_weights(user_id, old_unit, new_unit)

    await update_user_setting(user_id, 'weight_unit', new_unit)

    settings = await get_user_settings(user_id)

    info_text = "📏 **Единицы измерения**\n\n"

    if settings:
        info_text += f"📏 Дистанция: {settings.get('distance_unit', 'км')}\n"
        info_text += f"⚖️ Вес: {settings.get('weight_unit', 'кг')}\n"
        info_text += f"📅 Формат даты: {settings.get('date_format', 'ДД.ММ.ГГГГ')}\n"

    info_text += "\nВыберите параметр для изменения:"

    await callback.message.edit_text(
        info_text,
        reply_markup=get_units_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer("Сохранено!")


@router.callback_query(F.data == "settings:units:date")
async def callback_set_date_format(callback: CallbackQuery):
    """Выбор формата даты"""
    await callback.message.edit_text(
        "📅 Выберите формат даты:",
        reply_markup=get_date_format_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("date_format:"))
async def callback_save_date_format(callback: CallbackQuery):
    """Сохранение формата даты"""
    date_format = callback.data.split(":")[1]

    user_id = callback.from_user.id
    await update_user_setting(user_id, 'date_format', date_format)

    settings = await get_user_settings(user_id)

    info_text = "📏 **Единицы измерения**\n\n"

    if settings:
        info_text += f"📏 Дистанция: {settings.get('distance_unit', 'км')}\n"
        info_text += f"⚖️ Вес: {settings.get('weight_unit', 'кг')}\n"
        info_text += f"📅 Формат даты: {settings.get('date_format', 'ДД.ММ.ГГГГ')}\n"

    info_text += "\nВыберите параметр для изменения:"

    await callback.message.edit_text(
        info_text,
        reply_markup=get_units_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer("Сохранено!")



@router.callback_query(F.data == "settings:notifications")
async def callback_notifications_menu(callback: CallbackQuery):
    """Меню уведомлений"""
    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)

    info_text = "🔔 **Настройка уведомлений**\n\n"

    if settings:
        daily_time = settings.get('daily_pulse_weight_time')
        report_day = settings.get('weekly_report_day', 'Понедельник')
        report_time = settings.get('weekly_report_time', '09:00')

        training_reminders_enabled = settings.get('training_reminders_enabled', 0)
        training_reminder_days = json.loads(settings.get('training_reminder_days', '[]')) if settings.get('training_reminder_days') else []
        training_reminder_time = settings.get('training_reminder_time', '18:00')

        info_text += f"⏰ Время ежедневного ввода: {daily_time or 'не задано'}\n"
        info_text += f"📊 Недельный отчет: {report_day}, {report_time}\n"

        if training_reminders_enabled:
            if training_reminder_days:
                days_short = []
                day_map = {
                    'Понедельник': 'Пн', 'Вторник': 'Вт', 'Среда': 'Ср',
                    'Четверг': 'Чт', 'Пятница': 'Пт', 'Суббота': 'Сб', 'Воскресенье': 'Вс'
                }
                for day in training_reminder_days:
                    days_short.append(day_map.get(day, day[:2]))
                days_str = ", ".join(days_short)
                info_text += f"🔔 Напоминания о тренировках: {days_str}, {training_reminder_time}\n"
            else:
                info_text += f"🔔 Напоминания о тренировках: включены, {training_reminder_time}\n"
        else:
            info_text += "🔔 Напоминания о тренировках: выключены\n"

    info_text += "\nВыберите параметр для изменения:"

    await callback.message.edit_text(
        info_text,
        reply_markup=get_notifications_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "settings:notif:daily_time")
async def callback_set_daily_time(callback: CallbackQuery, state: FSMContext):
    """Установка времени ежедневного сообщения"""
    await callback.message.answer(
        "⏰ Введите время для ежедневного напоминания о вводе пульса и веса\n\n"
        "Вы можете ввести время в любом удобном формате:\n"
        "• 8:0 или 8:00\n"
        "• 09:00\n"
        "• 9 (будет 09:00)\n"
        "• 23:30\n\n"
        "Каждый день в это время вы будете получать напоминание.",
        reply_markup=get_simple_cancel_keyboard()
    )
    await state.set_state(SettingsStates.waiting_for_daily_time)
    await callback.answer()


@router.message(SettingsStates.waiting_for_daily_time)
async def process_daily_time(message: Message, state: FSMContext):
    """Обработка ввода времени ежедневного сообщения"""
    if message.text == "❌ Отмена":
        await state.clear()
        await send_notifications_menu(message, message.from_user.id)
        return

    from utils.time_normalizer import validate_and_normalize_time

    success, normalized_time, error_msg = validate_and_normalize_time(message.text)

    if not success:
        await message.answer(error_msg)
        return

    user_id = message.from_user.id
    await update_user_setting(user_id, 'daily_pulse_weight_time', normalized_time)

    await message.answer(
        f"✅ Время ежедневного напоминания сохранено: {normalized_time}",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()
    await send_notifications_menu(message, message.from_user.id)


@router.callback_query(F.data == "settings:notif:weekly_report")
async def callback_set_weekly_report(callback: CallbackQuery, state: FSMContext):
    """Выбор дня недели для отчета"""
    await callback.message.edit_text(
        "📊 Выберите день недели для получения недельного отчета:",
        reply_markup=get_weekday_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("weekday:"))
async def callback_save_weekday(callback: CallbackQuery, state: FSMContext):
    """Сохранение дня недели и запрос времени"""
    weekday = callback.data.split(":")[1]
    
    await state.update_data(report_weekday=weekday)
    
    await callback.message.answer(
        f"📅 День недели выбран: {weekday}\n\n"
        "⏰ Теперь введите время отправки отчета\n\n"
        "Вы можете ввести время в любом удобном формате:\n"
        "• 8:0 или 8:00\n"
        "• 09:00\n"
        "• 9 (будет 09:00)\n"
        "• 23:30",
        reply_markup=get_simple_cancel_keyboard()
    )
    await state.set_state(SettingsStates.waiting_for_report_time)
    await callback.answer()


@router.message(SettingsStates.waiting_for_report_time)
async def process_report_time(message: Message, state: FSMContext):
    """Обработка ввода времени недельного отчета"""
    if message.text == "❌ Отмена":
        await state.clear()
        await send_notifications_menu(message, message.from_user.id)
        return

    from utils.time_normalizer import validate_and_normalize_time

    success, normalized_time, error_msg = validate_and_normalize_time(message.text)

    if not success:
        await message.answer(error_msg)
        return

    data = await state.get_data()
    weekday = data.get('report_weekday')

    user_id = message.from_user.id

    await update_user_setting(user_id, 'weekly_report_day', weekday)
    await update_user_setting(user_id, 'weekly_report_time', normalized_time)

    await message.answer(
        f"✅ Недельный отчет настроен!\n\n"
        f"📅 День: {weekday}\n"
        f"⏰ Время: {normalized_time}",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()
    await send_notifications_menu(message, message.from_user.id)


from settings.calendar_handlers_birth import register_calendar_birth_handlers

register_calendar_birth_handlers(router)



@router.callback_query(F.data == "settings:units:timezone")
async def callback_set_timezone(callback: CallbackQuery):
    """Выбор часового пояса"""
    await callback.message.edit_text(
        "🌍 Выберите ваш часовой пояс для корректной работы уведомлений:",
        reply_markup=get_timezone_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("timezone:"))
async def callback_save_timezone(callback: CallbackQuery):
    """Сохранение выбранного часового пояса"""
    timezone = callback.data.split(":")[1]
    user_id = callback.from_user.id

    await update_user_setting(user_id, 'timezone', timezone)

    settings = await get_user_settings(user_id)

    info_text = "📏 **Единицы измерения**\n\n"

    if settings:
        info_text += f"📏 Дистанция: {settings.get('distance_unit', 'км')}\n"
        info_text += f"⚖️ Вес: {settings.get('weight_unit', 'кг')}\n"
        info_text += f"📅 Формат даты: {settings.get('date_format', 'ДД.ММ.ГГГГ')}\n"
        info_text += f"🌍 Часовой пояс: {settings.get('timezone', 'Europe/Moscow')}\n"

    info_text += "\nВыберите параметр для изменения:"

    await callback.message.edit_text(
        info_text,
        reply_markup=get_units_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer("Сохранено!")



@router.callback_query(F.data == "settings:notif:training_reminders")
async def callback_training_reminders_menu(callback: CallbackQuery):
    """Меню настройки напоминаний о тренировках"""
    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)

    is_enabled = settings.get('training_reminders_enabled', 0) if settings else 0
    reminder_days = json.loads(settings.get('training_reminder_days', '[]')) if settings else []
    reminder_time = settings.get('training_reminder_time', '18:00') if settings else '18:00'

    info_text = "🔔 **Напоминания о тренировках**\n\n"

    if is_enabled:
        info_text += "✅ Напоминания включены\n\n"
        if reminder_days:
            days_str = ", ".join(reminder_days)
            info_text += f"📅 Дни: {days_str}\n"
        else:
            info_text += "📅 Дни: не выбраны\n"
        info_text += f"⏰ Время: {reminder_time}\n"
    else:
        info_text += "🔕 Напоминания выключены\n"

    info_text += "\nВыберите действие:"

    await callback.message.edit_text(
        info_text,
        reply_markup=get_training_reminder_toggle_keyboard(bool(is_enabled)),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_training_reminders:"))
async def callback_toggle_training_reminders(callback: CallbackQuery):
    """Включение/выключение напоминаний о тренировках"""
    action = callback.data.split(":")[1]
    user_id = callback.from_user.id

    if action == "on":
        await update_user_setting(user_id, 'training_reminders_enabled', 1)
        settings = await get_user_settings(user_id)
        if not settings.get('training_reminder_days') or settings.get('training_reminder_days') == '[]':
            default_days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
            await update_user_setting(user_id, 'training_reminder_days', json.dumps(default_days))
    else:
        await update_user_setting(user_id, 'training_reminders_enabled', 0)

    await callback_training_reminders_menu(callback)


@router.callback_query(F.data == "select_reminder_days")
async def callback_select_reminder_days(callback: CallbackQuery, state: FSMContext):
    """Выбор дней для напоминаний"""
    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)

    current_days = json.loads(settings.get('training_reminder_days', '[]')) if settings else []

    await state.update_data(selected_days=current_days)
    await state.set_state(SettingsStates.selecting_reminder_days)

    await callback.message.edit_text(
        "📅 Выберите дни недели для напоминаний о тренировках:\n\n"
        "Нажмите на день, чтобы добавить/убрать его из списка.",
        reply_markup=get_training_reminder_days_keyboard(current_days)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_reminder_day:"), SettingsStates.selecting_reminder_days)
async def callback_toggle_reminder_day(callback: CallbackQuery, state: FSMContext):
    """Переключение дня для напоминаний"""
    day = callback.data.split(":")[1]

    data = await state.get_data()
    selected_days = data.get('selected_days', [])

    if day in selected_days:
        selected_days.remove(day)
    else:
        selected_days.append(day)

    await state.update_data(selected_days=selected_days)

    await callback.message.edit_reply_markup(
        reply_markup=get_training_reminder_days_keyboard(selected_days)
    )
    await callback.answer()


@router.callback_query(F.data == "save_reminder_days", SettingsStates.selecting_reminder_days)
async def callback_save_reminder_days(callback: CallbackQuery, state: FSMContext):
    """Сохранение выбранных дней"""
    data = await state.get_data()
    selected_days = data.get('selected_days', [])

    if not selected_days:
        await callback.answer("❌ Выберите хотя бы один день!", show_alert=True)
        return

    user_id = callback.from_user.id
    await update_user_setting(user_id, 'training_reminder_days', json.dumps(selected_days))

    await state.clear()

    settings = await get_user_settings(user_id)
    is_enabled = settings.get('training_reminders_enabled', 0) if settings else 0
    reminder_days = json.loads(settings.get('training_reminder_days', '[]')) if settings else []
    reminder_time = settings.get('training_reminder_time', '18:00') if settings else '18:00'

    info_text = "🔔 **Напоминания о тренировках**\n\n"

    if is_enabled:
        info_text += "✅ Напоминания включены\n\n"
        if reminder_days:
            days_str = ", ".join(reminder_days)
            info_text += f"📅 Дни: {days_str}\n"
        else:
            info_text += "📅 Дни: не выбраны\n"
        info_text += f"⏰ Время: {reminder_time}\n"
    else:
        info_text += "🔕 Напоминания выключены\n"

    info_text += "\nВыберите действие:"

    await callback.message.edit_text(
        info_text,
        reply_markup=get_training_reminder_toggle_keyboard(bool(is_enabled)),
        parse_mode="Markdown"
    )
    await callback.answer("✅ Дни сохранены!")


@router.callback_query(F.data == "change_reminder_time")
async def callback_change_reminder_time(callback: CallbackQuery, state: FSMContext):
    """Изменение времени напоминаний"""
    await callback.message.answer(
        "⏰ Введите время для напоминаний о тренировках\n\n"
        "Вы можете ввести время в любом удобном формате:\n"
        "• 8:0 или 8:00\n"
        "• 18:00\n"
        "• 18 (будет 18:00)\n"
        "• 20:30\n\n"
        "В выбранные дни в это время вы будете получать напоминание о необходимости внести тренировку.",
        reply_markup=get_simple_cancel_keyboard()
    )
    await state.set_state(SettingsStates.waiting_for_reminder_time)
    await callback.answer()


@router.message(SettingsStates.waiting_for_reminder_time)
async def process_reminder_time(message: Message, state: FSMContext):
    """Обработка ввода времени напоминаний"""
    if message.text == "❌ Отмена":
        await state.clear()
        await send_notifications_menu(message, message.from_user.id)
        return

    from utils.time_normalizer import validate_and_normalize_time

    success, normalized_time, error_msg = validate_and_normalize_time(message.text)

    if not success:
        await message.answer(error_msg)
        return

    user_id = message.from_user.id
    await update_user_setting(user_id, 'training_reminder_time', normalized_time)

    await message.answer(
        f"✅ Время напоминаний сохранено: {normalized_time}",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()
    await send_notifications_menu(message, user_id)



@router.callback_query(F.data == "settings:coach_mode")
async def toggle_coach_mode(callback: CallbackQuery):
    """Переключить режим тренера"""
    from coach.coach_queries import is_user_coach, set_coach_mode
    from aiogram.exceptions import TelegramBadRequest

    user_id = callback.from_user.id
    current_mode = await is_user_coach(user_id)

    if current_mode:
        await set_coach_mode(user_id, False)
        await callback.answer("Режим тренера выключен", show_alert=True)
    else:
        link_code = await set_coach_mode(user_id, True)
        await callback.answer(
            f"Режим тренера включён!\nВаш код: {link_code}",
            show_alert=True
        )

    settings = await get_user_settings(user_id)
    is_coach_now = await is_user_coach(user_id)

    info_text = "⚙️ **Настройки профиля**\n\n"

    if settings:
        info_text += f"👤 Имя: {settings.get('name') or 'не указано'}\n"
        birth_date_formatted = await format_birth_date(settings.get('birth_date'), user_id)
        info_text += f"🎂 Дата рождения: {birth_date_formatted}\n"

        gender = settings.get('gender')
        if gender == 'male':
            gender_text = '👨 Мужской'
        elif gender == 'female':
            gender_text = '👩 Женский'
        else:
            gender_text = 'не указан'
        info_text += f"⚧️ Пол: {gender_text}\n"

        weight_value = settings.get('weight')
        weight_unit = settings.get('weight_unit', 'кг')
        if weight_value:
            info_text += f"⚖️ Вес: {weight_value:.2f} {weight_unit}\n"
        else:
            info_text += "⚖️ Вес: не указан\n"

        height_value = settings.get('height')
        if height_value:
            info_text += f"📏 Рост: {height_value} см\n"
        else:
            info_text += "📏 Рост: не указан\n"

        types = await get_main_training_types(user_id)
        info_text += f"🏃 Типы тренировок: {', '.join(types)}\n"

        info_text += f"🌍 Часовой пояс: {settings.get('timezone', 'Europe/Moscow')}\n"

    info_text += "\nВыберите раздел для настройки:"

    try:
        await callback.message.edit_text(
            info_text,
            reply_markup=get_settings_menu_keyboard(is_coach_now),
            parse_mode="Markdown"
        )
    except TelegramBadRequest:
        pass
