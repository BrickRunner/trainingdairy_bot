"""
Полные обработчики настроек пользователя с всеми 14 пунктами
"""

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
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
    get_weekday_keyboard,
    get_training_type_goals_keyboard,
    get_simple_cancel_keyboard
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
    format_date_by_setting
)

router = Router()


# ============== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ОТПРАВКИ МЕНЮ ==============

async def send_profile_menu(message: Message, user_id: int):
    """Отправить меню профиля"""
    settings = await get_user_settings(user_id)
    
    info_text = "👤 **Настройки профиля**\n\n"
    
    if settings:
        info_text += f"✏️ Имя: {settings.get('name') or 'не указано'}\n"
        info_text += f"🎂 Дата рождения: {settings.get('birth_date') or 'не указана'}\n"
        info_text += f"⚧️ Пол: {settings.get('gender') or 'не указан'}\n"
        weight_unit = settings.get('weight_unit', 'кг')
        info_text += f"⚖️ Вес: {settings.get('weight') or 'не указан'} {weight_unit}\n"
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
        
        info_text += f"📊 Недельный объем: {weekly_volume or 'не задан'} {distance_unit}\n"
        info_text += f"🔢 Тренировок в неделю: {weekly_count or 'не задано'}\n"
        info_text += f"⚖️ Целевой вес: {weight_goal or 'не задан'} {weight_unit}\n\n"
        
        type_goals = await get_training_type_goals(user_id)
        if type_goals:
            info_text += "🏃 Цели по типам:\n"
            for t_type, goal in type_goals.items():
                info_text += f"  • {t_type}: {goal} {distance_unit}/неделю\n"
    
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
        info_text += f"📅 Формат даты: {settings.get('date_format', 'DD.MM.YYYY')}\n"
    
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


# ============== ГЛАВНОЕ МЕНЮ НАСТРОЕК ==============

@router.message(F.text == "⚙️ Настройки")
@router.message(Command("settings"))
async def settings_menu(message: Message, state: FSMContext):
    """Главное меню настроек"""
    await state.clear()
    user_id = message.from_user.id
    await init_user_settings(user_id)
    
    settings = await get_user_settings(user_id)
    
    info_text = "⚙️ **Настройки профиля**\n\n"
    
    if settings:
        info_text += f"👤 Имя: {settings.get('name') or 'не указано'}\n"
        info_text += f"🎂 Дата рождения: {settings.get('birth_date') or 'не указана'}\n"
        info_text += f"⚧️ Пол: {settings.get('gender') or 'не указан'}\n"
        info_text += f"⚖️ Вес: {settings.get('weight') or 'не указан'} {settings.get('weight_unit', 'кг')}\n"
        info_text += f"📏 Рост: {settings.get('height') or 'не указан'} см\n"
    
    info_text += "\nВыберите раздел для настройки:"
    
    await message.answer(
        info_text,
        reply_markup=get_settings_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "settings:menu")
async def callback_settings_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню настроек"""
    await state.clear()
    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)
    
    info_text = "⚙️ **Настройки профиля**\n\n"
    
    if settings:
        info_text += f"👤 Имя: {settings.get('name') or 'не указано'}\n"
        info_text += f"🎂 Дата рождения: {settings.get('birth_date') or 'не указана'}\n"
        info_text += f"⚧️ Пол: {settings.get('gender') or 'не указан'}\n"
        info_text += f"⚖️ Вес: {settings.get('weight') or 'не указан'} {settings.get('weight_unit', 'кг')}\n"
        info_text += f"📏 Рост: {settings.get('height') or 'не указан'} см\n"
    
    info_text += "\nВыберите раздел для настройки:"
    
    await callback.message.edit_text(
        info_text,
        reply_markup=get_settings_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ============== РАЗДЕЛ: ПРОФИЛЬ ==============

@router.callback_query(F.data == "settings:profile")
async def callback_profile_settings(callback: CallbackQuery):
    """Меню настроек профиля"""
    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)
    
    info_text = "👤 **Настройки профиля**\n\n"
    
    if settings:
        info_text += f"✏️ Имя: {settings.get('name') or 'не указано'}\n"
        info_text += f"🎂 Дата рождения: {settings.get('birth_date') or 'не указана'}\n"
        info_text += f"⚧️ Пол: {settings.get('gender') or 'не указан'}\n"
        info_text += f"⚖️ Вес: {settings.get('weight') or 'не указан'} {settings.get('weight_unit', 'кг')}\n"
        info_text += f"📏 Рост: {settings.get('height') or 'не указан'} см\n"
        
        # Основные типы тренировок
        types = await get_main_training_types(user_id)
        info_text += f"🏃 Типы тренировок: {', '.join(types)}\n"
    
    info_text += "\nВыберите параметр для изменения:"
    
    await callback.message.edit_text(
        info_text,
        reply_markup=get_profile_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# 1. ИМЯ
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
        await message.answer("❌ Отменено", reply_markup={"remove_keyboard": True})
        return
    
    name = message.text.strip()
    
    # Проверка минимальной длины
    if len(name) < 2:
        await message.answer("❌ Имя слишком короткое. Минимум 2 символа.")
        return
    
    # Проверка максимальной длины
    if len(name) > 50:
        await message.answer("❌ Имя слишком длинное. Максимум 50 символов.")
        return
    
    user_id = message.from_user.id
    await update_user_setting(user_id, 'name', name)
    
    await message.answer(
        f"✅ Имя успешно сохранено: {name}",
        reply_markup={"remove_keyboard": True}
    )
    await state.clear()
    
    # Возврат в меню профиля
    settings = await get_user_settings(user_id)
    info_text = "👤 **Настройки профиля**\n\n"
    
    if settings:
        info_text += f"✏️ Имя: {settings.get('name') or 'не указано'}\n"
        info_text += f"🎂 Дата рождения: {settings.get('birth_date') or 'не указана'}\n"
        info_text += f"⚧️ Пол: {settings.get('gender') or 'не указан'}\n"
        info_text += f"⚖️ Вес: {settings.get('weight') or 'не указан'} {settings.get('weight_unit', 'кг')}\n"
        info_text += f"📏 Рост: {settings.get('height') or 'не указан'} см\n"
        
        types = await get_main_training_types(user_id)
        info_text += f"🏃 Типы тренировок: {', '.join(types)}\n"
    
    info_text += "\nВыберите параметр для изменения:"
    
    await message.answer(
        info_text,
        reply_markup=get_profile_settings_keyboard(),
        parse_mode="Markdown"
    )


# 2. ДАТА РОЖДЕНИЯ
@router.callback_query(F.data == "settings:profile:birth_date")
async def callback_set_birth_date(callback: CallbackQuery, state: FSMContext):
    """Начало установки даты рождения"""
    await callback.message.answer(
        "🎂 Введите дату рождения в формате ДД.ММ.ГГГГ (например: 15.03.1990):\n\n"
        "📌 Каждый год в день рождения вы будете получать поздравительное сообщение!",
        reply_markup=get_simple_cancel_keyboard()
    )
    await state.set_state(SettingsStates.waiting_for_birth_date)
    await callback.answer()


@router.message(SettingsStates.waiting_for_birth_date)
async def process_birth_date(message: Message, state: FSMContext):
    """Обработка ввода даты рождения"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup={"remove_keyboard": True})
        return
    
    # Проверяем формат даты
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
        
        # Проверяем что дата не в будущем
        if birth_date > datetime.now():
            await message.answer("❌ Дата рождения не может быть в будущем!")
            return
        
        # Проверяем адекватность возраста (от 5 до 120 лет)
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
            reply_markup={"remove_keyboard": True}
        )
        await state.clear()
        
        # Возврат в меню профиля
        await send_profile_menu(message, user_id)
        
    except ValueError:
        await message.answer("❌ Некорректная дата. Проверьте правильность ввода.")


# 3. ПОЛ
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
        
        await callback.message.edit_text(
            f"✅ Пол сохранен: {gender}"
        )
        await callback.answer("Сохранено!")
        
        # Возврат в меню профиля
        await callback_profile_settings(callback)
    else:
        await callback.answer("Ошибка!")


# 4. ВЕС
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
        # Возврат в подменю
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
        
        await message.answer(
            f"✅ Вес сохранен: {weight} {weight_unit}",
            reply_markup={"remove_keyboard": True}
        )
        await state.clear()
        
        # Возврат в меню профиля
        await send_profile_menu(message, user_id)
        
    except ValueError:
        await message.answer("❌ Некорректное значение. Введите число (например: 70.5)")


# 5. РОСТ
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
        # Возврат в подменю
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
            reply_markup={"remove_keyboard": True}
        )
        await state.clear()
        # Возврат в подменю
        await send_profile_menu(message, message.from_user.id)
        
    except ValueError:
        await message.answer("❌ Некорректное значение. Введите число (например: 175)")


# 6. ОСНОВНЫЕ ТИПЫ ТРЕНИРОВОК
@router.callback_query(F.data == "settings:profile:main_types")
async def callback_set_main_types(callback: CallbackQuery, state: FSMContext):
    """Выбор основных типов тренировок"""
    user_id = callback.from_user.id
    selected_types = await get_main_training_types(user_id)
    
    # Сохраняем в состояние
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
    
    await callback.message.edit_text(
        f"✅ Основные типы тренировок сохранены:\n{', '.join(selected_types)}"
    )
    await callback.answer("Сохранено!")
    await state.clear()
    
    # Возврат в меню профиля
    await callback_profile_settings(callback)


# ============== РАЗДЕЛ: ПУЛЬСОВЫЕ ЗОНЫ (7) ==============

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


@router.callback_query(F.data == "settings:pulse:auto")
async def callback_pulse_auto(callback: CallbackQuery, state: FSMContext):
    """Автоматический расчет пульсовых зон"""
    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)
    
    if settings and settings.get('birth_date'):
        birth_date = datetime.strptime(settings['birth_date'], '%Y-%m-%d')
        age = (datetime.now() - birth_date).days // 365
        
        await set_pulse_zones_auto(user_id, age)
        
        settings = await get_user_settings(user_id)
        
        await callback.message.edit_text(
            f"✅ Пульсовые зоны рассчитаны автоматически!\n\n"
            f"Ваш возраст: {age} лет\n"
            f"Максимальный пульс: {settings['max_pulse']} уд/мин\n\n"
            f"🟢 Зона 1: {settings['zone1_min']}-{settings['zone1_max']}\n"
            f"🔵 Зона 2: {settings['zone2_min']}-{settings['zone2_max']}\n"
            f"🟡 Зона 3: {settings['zone3_min']}-{settings['zone3_max']}\n"
            f"🟠 Зона 4: {settings['zone4_min']}-{settings['zone4_max']}\n"
            f"🔴 Зона 5: {settings['zone5_min']}-{settings['zone5_max']}\n"
        )
        await callback.answer("Зоны рассчитаны!")
        
        # Возврат в меню пульсовых зон
        await callback_pulse_zones_menu(callback)
    else:
        await callback.answer(
            "❌ Сначала укажите дату рождения в настройках профиля!",
            show_alert=True
        )


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
        await settings_menu(message, state)
        return
    
    try:
        max_pulse = int(message.text.strip())
        
        if max_pulse < 100 or max_pulse > 250:
            await message.answer("❌ Введите корректное значение (100-250 уд/мин).")
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
            reply_markup={"remove_keyboard": True}
        )
        await state.clear()
        await settings_menu(message, state)
        
    except ValueError:
        await message.answer("❌ Введите целое число.")


@router.callback_query(F.data == "settings:pulse:show")
async def callback_show_pulse_zones(callback: CallbackQuery):
    """Показать текущие пульсовые зоны"""
    await callback_pulse_zones_menu(callback)


# ============== РАЗДЕЛ: ЦЕЛИ (8-11) ==============

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
        
        info_text += f"📊 Недельный объем: {weekly_volume or 'не задан'} {distance_unit}\n"
        info_text += f"🔢 Тренировок в неделю: {weekly_count or 'не задано'}\n"
        info_text += f"⚖️ Целевой вес: {weight_goal or 'не задан'} {weight_unit}\n\n"
        
        # Цели по типам
        type_goals = await get_training_type_goals(user_id)
        if type_goals:
            info_text += "🏃 Цели по типам:\n"
            for t_type, goal in type_goals.items():
                info_text += f"  • {t_type}: {goal} {distance_unit}/неделю\n"
    
    info_text += "\nВыберите параметр для изменения:"
    
    await callback.message.edit_text(
        info_text,
        reply_markup=get_goals_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# 8. ЦЕЛЕВОЙ ОБЪЕМ
@router.callback_query(F.data == "settings:goals:volume")
async def callback_set_weekly_volume(callback: CallbackQuery, state: FSMContext):
    """Установка целевого недельного объема"""
    settings = await get_user_settings(callback.from_user.id)
    distance_unit = settings.get('distance_unit', 'км') if settings else 'км'
    
    await callback.message.answer(
        f"📊 Введите целевой объем тренировок в неделю ({distance_unit}):\n\n"
        "Например: 30",
        reply_markup=get_simple_cancel_keyboard()
    )
    await state.set_state(SettingsStates.waiting_for_weekly_volume)
    await callback.answer()


@router.message(SettingsStates.waiting_for_weekly_volume)
async def process_weekly_volume(message: Message, state: FSMContext):
    """Обработка ввода недельного объема"""
    if message.text == "❌ Отмена":
        await state.clear()
        # Возврат в подменю
        await send_goals_menu(message, message.from_user.id)
        return
    
    try:
        volume = float(message.text.strip().replace(',', '.'))
        
        if volume <= 0 or volume > 1000:
            await message.answer("❌ Введите корректное значение (0-1000).")
            return
        
        user_id = message.from_user.id
        await update_user_setting(user_id, 'weekly_volume_goal', volume)
        
        settings = await get_user_settings(user_id)
        distance_unit = settings.get('distance_unit', 'км')
        
        await message.answer(
            f"✅ Целевой недельный объем сохранен: {volume} {distance_unit}",
            reply_markup={"remove_keyboard": True}
        )
        await state.clear()
        # Возврат в подменю
        await send_goals_menu(message, message.from_user.id)
        
    except ValueError:
        await message.answer("❌ Введите число (например: 30)")


# 9. КОЛИЧЕСТВО ТРЕНИРОВОК В НЕДЕЛЮ
@router.callback_query(F.data == "settings:goals:count")
async def callback_set_weekly_count(callback: CallbackQuery, state: FSMContext):
    """Установка целевого количества тренировок"""
    await callback.message.answer(
        "🔢 Введите целевое количество тренировок в неделю:\n\n"
        "Например: 5",
        reply_markup=get_simple_cancel_keyboard()
    )
    await state.set_state(SettingsStates.waiting_for_weekly_count)
    await callback.answer()


@router.message(SettingsStates.waiting_for_weekly_count)
async def process_weekly_count(message: Message, state: FSMContext):
    """Обработка ввода количества тренировок"""
    if message.text == "❌ Отмена":
        await state.clear()
        # Возврат в подменю
        await send_goals_menu(message, message.from_user.id)
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
            reply_markup={"remove_keyboard": True}
        )
        await state.clear()
        # Возврат в подменю
        await send_goals_menu(message, message.from_user.id)
        
    except ValueError:
        await message.answer("❌ Введите целое число.")


# 10. ЦЕЛИ ПО ТИПАМ ТРЕНИРОВОК
@router.callback_query(F.data == "settings:goals:by_type")
async def callback_set_type_goals(callback: CallbackQuery):
    """Выбор типа тренировки для установки цели"""
    await callback.message.edit_text(
        "🏃 **Цели по типам тренировок**\n\n"
        "Выберите тип тренировки для установки цели:",
        reply_markup=get_training_type_goals_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("type_goal:"))
async def callback_type_goal_input(callback: CallbackQuery, state: FSMContext):
    """Ввод цели для конкретного типа"""
    training_type = callback.data.split(":")[1]
    
    await state.update_data(current_type_goal=training_type)
    
    settings = await get_user_settings(callback.from_user.id)
    distance_unit = settings.get('distance_unit', 'км') if settings else 'км'
    
    await callback.message.answer(
        f"🎯 Введите цель для типа '{training_type}' в {distance_unit}/неделю:\n\n"
        "Например: 20",
        reply_markup=get_simple_cancel_keyboard()
    )
    await state.set_state(SettingsStates.waiting_for_type_goal)
    await callback.answer()


@router.message(SettingsStates.waiting_for_type_goal)
async def process_type_goal(message: Message, state: FSMContext):
    """Обработка ввода цели по типу"""
    if message.text == "❌ Отмена":
        await state.clear()
        # Возврат в подменю
        await send_goals_menu(message, message.from_user.id)
        return
    
    try:
        goal = float(message.text.strip().replace(',', '.'))
        
        if goal <= 0 or goal > 500:
            await message.answer("❌ Введите корректное значение (0-500).")
            return
        
        data = await state.get_data()
        training_type = data.get('current_type_goal')
        
        user_id = message.from_user.id
        await set_training_type_goal(user_id, training_type, goal)
        
        settings = await get_user_settings(user_id)
        distance_unit = settings.get('distance_unit', 'км')
        
        await message.answer(
            f"✅ Цель для '{training_type}' сохранена: {goal} {distance_unit}/неделю",
            reply_markup={"remove_keyboard": True}
        )
        await state.clear()
        # Возврат в подменю
        await send_goals_menu(message, message.from_user.id)
        
    except ValueError:
        await message.answer("❌ Введите число.")


# 11. ЦЕЛЕВОЙ ВЕС
@router.callback_query(F.data == "settings:goals:weight")
async def callback_set_weight_goal(callback: CallbackQuery, state: FSMContext):
    """Установка целевого веса"""
    settings = await get_user_settings(callback.from_user.id)
    weight_unit = settings.get('weight_unit', 'кг') if settings else 'кг'
    
    await callback.message.answer(
        f"⚖️ Введите целевой вес в {weight_unit}:\n\n"
        "Например: 75",
        reply_markup=get_simple_cancel_keyboard()
    )
    await state.set_state(SettingsStates.waiting_for_weight_goal)
    await callback.answer()


@router.message(SettingsStates.waiting_for_weight_goal)
async def process_weight_goal(message: Message, state: FSMContext):
    """Обработка ввода целевого веса"""
    if message.text == "❌ Отмена":
        await state.clear()
        # Возврат в подменю
        await send_goals_menu(message, message.from_user.id)
        return
    
    try:
        weight_goal = float(message.text.strip().replace(',', '.'))
        
        if weight_goal <= 0 or weight_goal > 500:
            await message.answer("❌ Введите корректное значение (0-500).")
            return
        
        user_id = message.from_user.id
        await update_user_setting(user_id, 'weight_goal', weight_goal)
        
        settings = await get_user_settings(user_id)
        weight_unit = settings.get('weight_unit', 'кг')
        
        await message.answer(
            f"✅ Целевой вес сохранен: {weight_goal} {weight_unit}",
            reply_markup={"remove_keyboard": True}
        )
        await state.clear()
        # Возврат в подменю
        await send_goals_menu(message, message.from_user.id)
        
    except ValueError:
        await message.answer("❌ Введите число.")


# ============== РАЗДЕЛ: ЕДИНИЦЫ ИЗМЕРЕНИЯ (12) ==============

@router.callback_query(F.data == "settings:units")
async def callback_units_menu(callback: CallbackQuery):
    """Меню единиц измерения"""
    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)
    
    info_text = "📏 **Единицы измерения**\n\n"
    
    if settings:
        info_text += f"📏 Дистанция: {settings.get('distance_unit', 'км')}\n"
        info_text += f"⚖️ Вес: {settings.get('weight_unit', 'кг')}\n"
        info_text += f"📅 Формат даты: {settings.get('date_format', 'DD.MM.YYYY')}\n"
    
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
    
    await callback.message.edit_text(
        f"✅ Единица дистанции сохранена: {unit}"
    )
    await callback.answer("Сохранено!")
    
    # Возврат в меню единиц
    await callback_units_menu(callback)


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
    """Сохранение единицы веса"""
    unit = callback.data.split(":")[1]
    
    user_id = callback.from_user.id
    await update_user_setting(user_id, 'weight_unit', unit)
    
    await callback.message.edit_text(
        f"✅ Единица веса сохранена: {unit}"
    )
    await callback.answer("Сохранено!")
    
    # Возврат в меню единиц
    await callback_units_menu(callback)


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
    
    await callback.message.edit_text(
        f"✅ Формат даты сохранен: {date_format}"
    )
    await callback.answer("Сохранено!")
    
    # Возврат в меню единиц
    await callback_units_menu(callback)


# ============== РАЗДЕЛ: УВЕДОМЛЕНИЯ (13-14) ==============

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
        
        info_text += f"⏰ Время ежедневного ввода: {daily_time or 'не задано'}\n"
        info_text += f"📊 Недельный отчет: {report_day}, {report_time}\n"
    
    info_text += "\nВыберите параметр для изменения:"
    
    await callback.message.edit_text(
        info_text,
        reply_markup=get_notifications_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# 13. ВРЕМЯ ЕЖЕДНЕВНОГО СООБЩЕНИЯ
@router.callback_query(F.data == "settings:notif:daily_time")
async def callback_set_daily_time(callback: CallbackQuery, state: FSMContext):
    """Установка времени ежедневного сообщения"""
    await callback.message.answer(
        "⏰ Введите время для ежедневного напоминания о вводе пульса и веса\n\n"
        "Формат: ЧЧ:ММ (например: 09:00)\n\n"
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
        # Возврат в подменю
        await send_notifications_menu(message, message.from_user.id)
        return
    
    time_pattern = r'(\d{2}):(\d{2})'
    match = re.match(time_pattern, message.text.strip())
    
    if not match:
        await message.answer("❌ Неверный формат. Используйте ЧЧ:ММ (например: 09:00)")
        return
    
    hour, minute = match.groups()
    
    try:
        hour_int = int(hour)
        minute_int = int(minute)
        
        if hour_int < 0 or hour_int > 23 or minute_int < 0 or minute_int > 59:
            await message.answer("❌ Некорректное время. Часы: 00-23, минуты: 00-59")
            return
        
        user_id = message.from_user.id
        time_str = f"{hour}:{minute}"
        await update_user_setting(user_id, 'daily_pulse_weight_time', time_str)
        
        await message.answer(
            f"✅ Время ежедневного напоминания сохранено: {time_str}",
            reply_markup={"remove_keyboard": True}
        )
        await state.clear()
        # Возврат в подменю
        await send_notifications_menu(message, message.from_user.id)
        
    except ValueError:
        await message.answer("❌ Некорректное время.")


# 14. ВРЕМЯ НЕДЕЛЬНОГО ОТЧЕТА
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
        "⏰ Теперь введите время отправки отчета в формате ЧЧ:ММ (например: 09:00):",
        reply_markup=get_simple_cancel_keyboard()
    )
    await state.set_state(SettingsStates.waiting_for_report_time)
    await callback.answer()


@router.message(SettingsStates.waiting_for_report_time)
async def process_report_time(message: Message, state: FSMContext):
    """Обработка ввода времени недельного отчета"""
    if message.text == "❌ Отмена":
        await state.clear()
        # Возврат в подменю
        await send_notifications_menu(message, message.from_user.id)
        return
    
    time_pattern = r'(\d{2}):(\d{2})'
    match = re.match(time_pattern, message.text.strip())
    
    if not match:
        await message.answer("❌ Неверный формат. Используйте ЧЧ:ММ (например: 09:00)")
        return
    
    hour, minute = match.groups()
    
    try:
        hour_int = int(hour)
        minute_int = int(minute)
        
        if hour_int < 0 or hour_int > 23 or minute_int < 0 or minute_int > 59:
            await message.answer("❌ Некорректное время. Часы: 00-23, минуты: 00-59")
            return
        
        data = await state.get_data()
        weekday = data.get('report_weekday')
        
        user_id = message.from_user.id
        time_str = f"{hour}:{minute}"
        
        await update_user_setting(user_id, 'weekly_report_day', weekday)
        await update_user_setting(user_id, 'weekly_report_time', time_str)
        
        await message.answer(
            f"✅ Недельный отчет настроен!\n\n"
            f"📅 День: {weekday}\n"
            f"⏰ Время: {time_str}",
            reply_markup={"remove_keyboard": True}
        )
        await state.clear()
        # Возврат в подменю
        await send_notifications_menu(message, message.from_user.id)
        
    except ValueError:
        await message.answer("❌ Некорректное время.")
