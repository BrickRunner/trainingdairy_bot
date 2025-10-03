"""
Обработчики команд и сообщений бота
"""

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime
import re

from bot.fsm import AddTrainingStates
from bot.keyboards import (
    get_main_menu_keyboard,
    get_training_types_keyboard,
    get_cancel_keyboard,
    get_skip_keyboard,
    get_fatigue_keyboard
)
from database.queries import add_user, add_training, get_user

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # Добавляем пользователя в БД, если его нет
    await add_user(user_id, username)
    
    welcome_text = (
        f"👋 Привет, {username}!\n\n"
        "Добро пожаловать в **Trainingdiary_bot** — твой личный дневник тренировок! 🏃‍♂️\n\n"
        "Что я умею:\n"
        "➕ Добавлять тренировки\n"
        "📊 Показывать статистику\n"
        "📈 Строить графики прогресса\n"
        "🏆 Отслеживать достижения\n\n"
        "Выбери действие из меню ниже 👇"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "📖 **Справка по боту**\n\n"
        "**Команды:**\n"
        "/start - Начать работу с ботом\n"
        "/add_training - Добавить тренировку\n"
        "/stats - Посмотреть статистику\n"
        "/help - Показать эту справку\n\n"
        "**Кнопки меню:**\n"
        "➕ Добавить тренировку - Записать новую тренировку\n"
        "📊 Статистика - Посмотреть свою статистику\n"
        "📈 Графики - Визуализация прогресса\n"
        "🏆 Достижения - Ваши достижения и награды\n\n"
        "Для добавления тренировки следуйте инструкциям бота. "
        "Вы всегда можете отменить действие, нажав кнопку ❌ Отменить"
    )
    
    await message.answer(help_text, parse_mode="Markdown")


@router.message(F.text == "➕ Добавить тренировку")
@router.message(Command("add_training"))
async def start_add_training(message: Message, state: FSMContext):
    """Начало процесса добавления тренировки"""
    await message.answer(
        "🏋️ **Добавление тренировки**\n\n"
        "Выберите тип тренировки:",
        reply_markup=get_training_types_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(AddTrainingStates.waiting_for_type)


@router.callback_query(F.data.startswith("training_type:"))
async def process_training_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа тренировки"""
    training_type = callback.data.split(":")[1]
    
    await state.update_data(training_type=training_type)
    
    await callback.message.edit_text(
        f"✅ Выбран тип: **{training_type.capitalize()}**",
        parse_mode="Markdown"
    )
    
    await callback.message.answer(
        "📅 Введите дату тренировки\n\n"
        "Формат: ДД.ММ.ГГГГ (например, 15.01.2024)\n"
        "Или напишите 'сегодня' для текущей даты",
        reply_markup=get_cancel_keyboard()
    )
    
    await state.set_state(AddTrainingStates.waiting_for_date)
    await callback.answer()


@router.message(AddTrainingStates.waiting_for_date)
async def process_date(message: Message, state: FSMContext):
    """Обработка даты тренировки"""
    if message.text == "❌ Отменить":
        await cancel_handler(message, state)
        return
    
    # Парсинг даты
    if message.text.lower() == "сегодня":
        date = datetime.now().date()
    else:
        # Проверка формата ДД.ММ.ГГГГ
        date_pattern = r'^\d{2}\.\d{2}\.\d{4}$'
        if not re.match(date_pattern, message.text):
            await message.answer(
                "❌ Неверный формат даты!\n\n"
                "Используйте формат: ДД.ММ.ГГГГ (например, 15.01.2024)\n"
                "Или напишите 'сегодня'"
            )
            return
        
        try:
            date = datetime.strptime(message.text, "%d.%m.%Y").date()
        except ValueError:
            await message.answer(
                "❌ Некорректная дата!\n\n"
                "Проверьте правильность введенной даты"
            )
            return
    
    await state.update_data(date=date)
    
    await message.answer(
        f"✅ Дата: {date.strftime('%d.%m.%Y')}\n\n"
        "⏱️ Введите продолжительность тренировки в минутах\n\n"
        "Например: 60"
    )
    
    await state.set_state(AddTrainingStates.waiting_for_duration)


@router.message(AddTrainingStates.waiting_for_duration)
async def process_duration(message: Message, state: FSMContext):
    """Обработка продолжительности тренировки"""
    if message.text == "❌ Отменить":
        await cancel_handler(message, state)
        return
    
    try:
        duration = int(message.text)
        if duration <= 0:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Введите положительное целое число (минуты)\n"
            "Например: 60"
        )
        return
    
    await state.update_data(duration=duration)
    
    await message.answer(
        f"✅ Продолжительность: {duration} мин\n\n"
        "🏃 Введите дистанцию в километрах\n\n"
        "Например: 10 или 10.5"
    )
    
    await state.set_state(AddTrainingStates.waiting_for_distance)


@router.message(AddTrainingStates.waiting_for_distance)
async def process_distance(message: Message, state: FSMContext):
    """Обработка дистанции"""
    if message.text == "❌ Отменить":
        await cancel_handler(message, state)
        return
    
    try:
        distance = float(message.text.replace(',', '.'))
        if distance <= 0:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Введите положительное число (километры)\n"
            "Например: 10 или 10.5"
        )
        return
    
    await state.update_data(distance=distance)
    
    await message.answer(
        f"✅ Дистанция: {distance} км\n\n"
        "❤️ Введите средний пульс (уд/мин)\n\n"
        "Например: 145"
    )
    
    await state.set_state(AddTrainingStates.waiting_for_pulse)


@router.message(AddTrainingStates.waiting_for_pulse)
async def process_pulse(message: Message, state: FSMContext):
    """Обработка пульса"""
    if message.text == "❌ Отменить":
        await cancel_handler(message, state)
        return
    
    try:
        pulse = int(message.text)
        if pulse <= 0 or pulse > 250:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Введите корректное значение пульса (30-250 уд/мин)\n"
            "Например: 145"
        )
        return
    
    await state.update_data(pulse=pulse)
    
    await message.answer(
        f"✅ Средний пульс: {pulse} уд/мин\n\n"
        "📝 Введите описание тренировки\n\n"
        "Например: Разминка - 3000м, ОРУ + СБУ + 3 ускорения\n\n"
        "Или нажмите ⏭️ Пропустить",
        reply_markup=get_skip_keyboard()
    )
    
    await state.set_state(AddTrainingStates.waiting_for_description)


@router.message(AddTrainingStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    """Обработка описания тренировки"""
    if message.text == "❌ Отменить":
        await cancel_handler(message, state)
        return
    
    description = None if message.text == "⏭️ Пропустить" else message.text
    await state.update_data(description=description)
    
    await message.answer(
        "🎯 Введите результаты тренировки\n\n"
        "Например: 3 х 200м / 200м - (28.0-29.0-28.4)\n\n"
        "Или нажмите ⏭️ Пропустить"
    )
    
    await state.set_state(AddTrainingStates.waiting_for_results)


@router.message(AddTrainingStates.waiting_for_results)
async def process_results(message: Message, state: FSMContext):
    """Обработка результатов"""
    if message.text == "❌ Отменить":
        await cancel_handler(message, state)
        return
    
    results = None if message.text == "⏭️ Пропустить" else message.text
    await state.update_data(results=results)
    
    await message.answer(
        "💬 Добавьте комментарий к тренировке\n\n"
        "Например: Хорошая форма, легко пробежал\n\n"
        "Или нажмите ⏭️ Пропустить"
    )
    
    await state.set_state(AddTrainingStates.waiting_for_comment)


@router.message(AddTrainingStates.waiting_for_comment)
async def process_comment(message: Message, state: FSMContext):
    """Обработка комментария"""
    if message.text == "❌ Отменить":
        await cancel_handler(message, state)
        return
    
    comment = None if message.text == "⏭️ Пропустить" else message.text
    await state.update_data(comment=comment)
    
    await message.answer(
        "😴 Оцените уровень усталости после тренировки\n\n"
        "Выберите от 1 (совсем не устал) до 10 (очень устал):",
        reply_markup=get_fatigue_keyboard()
    )
    
    await state.set_state(AddTrainingStates.waiting_for_fatigue)


@router.callback_query(F.data.startswith("fatigue:"))
async def process_fatigue(callback: CallbackQuery, state: FSMContext):
    """Обработка уровня усталости и сохранение тренировки"""
    fatigue_level = int(callback.data.split(":")[1])
    
    # Получаем все данные из состояния
    data = await state.get_data()
    data['fatigue_level'] = fatigue_level
    data['user_id'] = callback.from_user.id
    
    # Сохраняем тренировку в БД
    await add_training(data)
    
    # Формируем итоговое сообщение
    summary = (
        "✅ **Тренировка успешно добавлена!**\n\n"
        f"📅 Дата: {data['date'].strftime('%d.%m.%Y')}\n"
        f"🏃 Тип: {data['training_type'].capitalize()}\n"
        f"⏱️ Продолжительность: {data['duration']} мин\n"
        f"📏 Дистанция: {data['distance']} км\n"
        f"❤️ Средний пульс: {data['pulse']} уд/мин\n"
    )
    
    if data.get('description'):
        summary += f"📝 Описание: {data['description']}\n"
    if data.get('results'):
        summary += f"🎯 Результаты: {data['results']}\n"
    if data.get('comment'):
        summary += f"💬 Комментарий: {data['comment']}\n"
    
    summary += f"😴 Усталость: {fatigue_level}/10"
    
    await callback.message.edit_text(summary, parse_mode="Markdown")
    await callback.message.answer(
        "Что делаем дальше?",
        reply_markup=get_main_menu_keyboard()
    )
    
    # Очищаем состояние
    await state.clear()
    await callback.answer("Тренировка сохранена! ✅")


@router.message(F.text == "❌ Отменить")
@router.callback_query(F.data == "cancel")
async def cancel_handler(message: Message | CallbackQuery, state: FSMContext):
    """Отмена текущей операции"""
    current_state = await state.get_state()
    
    if current_state is None:
        if isinstance(message, Message):
            await message.answer(
                "Нечего отменять 🤷‍♂️",
                reply_markup=get_main_menu_keyboard()
            )
        return
    
    await state.clear()
    
    if isinstance(message, CallbackQuery):
        await message.message.edit_text("❌ Действие отменено")
        await message.message.answer(
            "Вы в главном меню",
            reply_markup=get_main_menu_keyboard()
        )
        await message.answer()
    else:
        await message.answer(
            "❌ Действие отменено\n\nВы в главном меню",
            reply_markup=get_main_menu_keyboard()
        )


@router.message(F.text == "📊 Статистика")
async def show_stats(message: Message):
    """Показать статистику (заглушка)"""
    await message.answer(
        "📊 Статистика будет доступна позже!\n\n"
        "Здесь вы сможете увидеть:\n"
        "• Общее количество тренировок\n"
        "• Суммарную дистанцию\n"
        "• Среднюю продолжительность\n"
        "• И многое другое!"
    )


@router.message(F.text == "📈 Графики")
async def show_graphs(message: Message):
    """Показать графики (заглушка)"""
    await message.answer("📈 Графики будут доступны позже!")


@router.message(F.text == "🏆 Достижения")
async def show_achievements(message: Message):
    """Показать достижения (заглушка)"""
    await message.answer("🏆 Достижения будут доступны позже!")


@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message):
    """Показать настройки (заглушка)"""
    await message.answer("⚙️ Настройки будут доступны позже!")


@router.message(F.text == "ℹ️ Помощь")
async def show_help(message: Message):
    """Показать помощь"""
    await cmd_help(message)
