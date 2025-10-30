"""
Обработчики процесса регистрации нового пользователя
"""

import json
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.fsm import RegistrationStates
from database.queries import get_user_settings, update_user_setting, init_user_settings, set_pulse_zones_auto
from registration.registration_keyboards import (
    get_gender_keyboard,
    get_training_types_keyboard
)
from bot.keyboards import get_main_menu_keyboard

router = Router()
logger = logging.getLogger(__name__)


async def start_registration(message: Message, state: FSMContext):
    """Начать процесс регистрации"""
    await state.set_state(RegistrationStates.waiting_for_name)

    welcome_text = (
        "👋 Привет! Давай настроим твой профиль для тренировочного дневника.\n\n"
        "📝 <b>Как тебя зовут?</b>\n\n"
        "Введи своё имя:"
    )

    await message.answer(welcome_text, parse_mode="HTML")


@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка имени"""
    name = message.text.strip()

    if len(name) < 2 or len(name) > 50:
        await message.answer(
            "❌ Имя должно содержать от 2 до 50 символов. Попробуй ещё раз:"
        )
        return

    # Сохраняем имя в FSM
    await state.update_data(name=name)

    # Сохраняем в БД
    user_id = message.from_user.id
    await init_user_settings(user_id)
    await update_user_setting(user_id, 'name', name)

    # Переходим к дате рождения
    await state.set_state(RegistrationStates.waiting_for_birth_date)

    await message.answer(
        f"Приятно познакомиться, {name}! 😊\n\n"
        "📅 <b>Укажи дату рождения</b>\n\n"
        "Формат: ДД.ММ.ГГГГ (например, 15.03.1990)\n"
        "Это нужно для расчета пульсовых зон.",
        parse_mode="HTML"
    )


@router.message(RegistrationStates.waiting_for_birth_date)
async def process_birth_date(message: Message, state: FSMContext):
    """Обработка даты рождения"""
    user_id = message.from_user.id
    date_str = message.text.strip()

    # Парсим дату
    try:
        birth_date = datetime.strptime(date_str, "%d.%m.%Y")

        # Проверяем адекватность даты
        today = datetime.now()
        age = (today - birth_date).days // 365

        if age < 10 or age > 100:
            await message.answer(
                "❌ Пожалуйста, укажи корректную дату рождения.\n"
                "Формат: ДД.ММ.ГГГГ (например, 15.03.1990)"
            )
            return

        # Сохраняем дату рождения
        await state.update_data(birth_date=birth_date.strftime("%Y-%m-%d"), age=age)
        await update_user_setting(user_id, 'birth_date', birth_date.strftime("%Y-%m-%d"))

        # Переходим к выбору пола
        await state.set_state(RegistrationStates.waiting_for_gender)

        await message.answer(
            "👤 <b>Выбери пол:</b>\n\n"
            "Это нужно для расчета максимального пульса.",
            reply_markup=get_gender_keyboard(),
            parse_mode="HTML"
        )

    except ValueError:
        await message.answer(
            "❌ Неверный формат даты.\n"
            "Используй формат: ДД.ММ.ГГГГ (например, 15.03.1990)"
        )


@router.callback_query(RegistrationStates.waiting_for_gender, F.data.startswith("reg_gender:"))
async def process_gender(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора пола"""
    user_id = callback.from_user.id
    gender = callback.data.split(":")[1]  # male или female

    # Сохраняем пол
    await state.update_data(gender=gender)
    await update_user_setting(user_id, 'gender', gender)

    # Рассчитываем пульсовые зоны на основе возраста и пола
    data = await state.get_data()
    age = data.get('age')
    if age:
        await set_pulse_zones_auto(user_id, age)

    # Переходим к росту
    await state.set_state(RegistrationStates.waiting_for_height)

    gender_text = "Мужской" if gender == "male" else "Женский"
    await callback.message.edit_text(
        f"✅ Пол: {gender_text}\n\n"
        "📏 <b>Укажи рост в см</b>\n\n"
        "Например: 175",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(RegistrationStates.waiting_for_height)
async def process_height(message: Message, state: FSMContext):
    """Обработка роста"""
    user_id = message.from_user.id

    try:
        height = float(message.text.strip())

        if height < 100 or height > 250:
            await message.answer(
                "❌ Укажи корректный рост (от 100 до 250 см):"
            )
            return

        # Сохраняем рост
        await state.update_data(height=height)
        await update_user_setting(user_id, 'height', height)

        # Переходим к весу
        await state.set_state(RegistrationStates.waiting_for_weight)

        await message.answer(
            f"✅ Рост: {height} см\n\n"
            "⚖️ <b>Укажи вес в кг</b>\n\n"
            "Например: 70",
            parse_mode="HTML"
        )

    except ValueError:
        await message.answer(
            "❌ Неверный формат. Укажи рост числом (например: 175):"
        )


@router.message(RegistrationStates.waiting_for_weight)
async def process_weight(message: Message, state: FSMContext):
    """Обработка веса"""
    user_id = message.from_user.id

    try:
        weight = float(message.text.strip())

        if weight < 30 or weight > 300:
            await message.answer(
                "❌ Укажи корректный вес (от 30 до 300 кг):"
            )
            return

        # Сохраняем вес
        await state.update_data(weight=weight)
        await update_user_setting(user_id, 'weight', weight)

        # Переходим к выбору типов тренировок
        await state.set_state(RegistrationStates.selecting_main_types)
        await state.update_data(selected_types=[])

        await message.answer(
            f"✅ Вес: {weight} кг\n\n"
            "🏃 <b>Выбери основные типы тренировок</b>\n\n"
            "⚠️ <b>Важно:</b> Только выбранные типы будут отображаться "
            "при добавлении тренировки.\n\n"
            "Выбери один или несколько типов:",
            reply_markup=get_training_types_keyboard([]),
            parse_mode="HTML"
        )

    except ValueError:
        await message.answer(
            "❌ Неверный формат. Укажи вес числом (например: 70):"
        )


@router.callback_query(RegistrationStates.selecting_main_types, F.data.startswith("reg_toggle_type:"))
async def toggle_training_type(callback: CallbackQuery, state: FSMContext):
    """Переключение выбора типа тренировки"""
    training_type = callback.data.split(":")[1]

    # Получаем текущий список выбранных типов
    data = await state.get_data()
    selected_types = data.get('selected_types', [])

    # Переключаем тип
    if training_type in selected_types:
        selected_types.remove(training_type)
    else:
        selected_types.append(training_type)

    await state.update_data(selected_types=selected_types)

    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=get_training_types_keyboard(selected_types)
    )
    await callback.answer()


@router.callback_query(RegistrationStates.selecting_main_types, F.data == "reg_confirm_types")
async def confirm_training_types(callback: CallbackQuery, state: FSMContext):
    """Подтверждение выбора типов тренировок"""
    user_id = callback.from_user.id
    data = await state.get_data()
    selected_types = data.get('selected_types', [])

    if not selected_types:
        await callback.answer("❌ Выбери хотя бы один тип тренировки!", show_alert=True)
        return

    # Сохраняем типы тренировок в БД
    await update_user_setting(user_id, 'main_training_types', json.dumps(selected_types))

    # Автоопределение часового пояса на основе языка пользователя
    try:
        # Получаем языковой код пользователя из Telegram
        language_code = callback.from_user.language_code or 'ru'

        # Определение часового пояса по языковому коду
        timezone_map = {
            'ru': 'Europe/Moscow',
            'en': 'Europe/London',
            'de': 'Europe/Berlin',
            'fr': 'Europe/Paris',
            'es': 'Europe/Madrid',
            'it': 'Europe/Rome',
            'pt': 'Europe/Lisbon',
            'uk': 'Europe/Kiev',
            'be': 'Europe/Minsk',
            'kk': 'Asia/Almaty',
            'uz': 'Asia/Tashkent'
        }

        timezone = timezone_map.get(language_code, 'Europe/Moscow')
        logger.info(f"Автоопределён часовой пояс {timezone} для пользователя {user_id} (язык: {language_code})")
    except Exception as e:
        logger.error(f"Ошибка автоопределения часового пояса: {e}")
        timezone = 'Europe/Moscow'

    await update_user_setting(user_id, 'timezone', timezone)

    # Завершаем регистрацию
    await state.clear()

    # Получаем имя для персонализации
    name = data.get('name', 'друг')

    # Форматируем список выбранных типов для отображения
    type_names = {
        'кросс': '🏃 Кросс',
        'плавание': '🏊 Плавание',
        'велотренировка': '🚴 Велотренировка',
        'силовая': '💪 Силовая',
        'интервальная': '⚡ Интервальная',
        'другое': '🧘 Другое'
    }
    selected_names = [type_names.get(t, t) for t in selected_types]

    # Форматируем дату рождения
    birth_date_str = data.get('birth_date', '')
    if birth_date_str:
        birth_date_formatted = datetime.strptime(birth_date_str, "%Y-%m-%d").strftime("%d.%m.%Y")
    else:
        birth_date_formatted = 'не указана'

    # Форматируем пол
    gender_text = 'Мужской' if data.get('gender') == 'male' else 'Женский'

    completion_text = (
        f"🎉 <b>Отлично, {name}! Регистрация завершена!</b>\n\n"
        "📋 <b>Твой профиль:</b>\n"
        f"👤 Имя: {name}\n"
        f"🎂 Дата рождения: {birth_date_formatted}\n"
        f"⚧️ Пол: {gender_text}\n"
        f"📏 Рост: {data.get('height')} см\n"
        f"⚖️ Вес: {data.get('weight')} кг\n"
        f"🏃 Основные типы тренировок: {', '.join(selected_names)}\n"
        f"🌍 Часовой пояс: {timezone}\n\n"
        "⚠️ <b>Важно:</b> Только выбранные типы тренировок будут отображаться при добавлении тренировки.\n\n"
        "Теперь ты можешь начать добавлять тренировки!\n"
        "Настройки профиля всегда можно изменить в разделе ⚙️ Настройки."
    )

    await callback.message.edit_text(
        completion_text,
        parse_mode="HTML"
    )

    # Отправляем главное меню
    await callback.message.answer(
        "Выбери действие:",
        reply_markup=get_main_menu_keyboard()
    )

    await callback.answer()
