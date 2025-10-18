"""
Обработчики календаря для выбора даты рождения в настройках
"""

from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def handle_calendar_birth_date_selection(callback: CallbackQuery, state: FSMContext, router):
    """Обработчик выбора даты рождения из календаря"""
    from bot.calendar_keyboard import CalendarKeyboard
    from database.queries import update_user_setting
    from utils.date_formatter import DateFormatter, get_user_date_format
    from settings.settings_handlers_full import send_profile_menu

    logger.info(f"Обработчик cal_birth_1_select_: {callback.data}")

    # Парсим выбранную дату
    parsed = CalendarKeyboard.parse_callback_data(callback.data.replace("cal_birth_", "cal_"))
    selected_date = parsed.get("date")

    if not selected_date:
        await callback.answer("❌ Ошибка при выборе даты", show_alert=True)
        return

    # Проверяем, что дата не из будущего
    from datetime import timedelta
    utc_now = datetime.utcnow()
    moscow_now = utc_now + timedelta(hours=3)
    today = moscow_now.date()

    if selected_date.date() > today:
        await callback.answer("❌ Дата рождения не может быть в будущем!", show_alert=True)
        return

    # Проверяем адекватность возраста (от 5 до 120 лет)
    birth_date = selected_date.date()
    age = (today - birth_date).days // 365

    if age < 5 or age > 120:
        await callback.answer("❌ Пожалуйста, выберите корректную дату рождения (возраст от 5 до 120 лет).", show_alert=True)
        return

    user_id = callback.from_user.id
    birth_date_str = birth_date.strftime('%Y-%m-%d')
    await update_user_setting(user_id, 'birth_date', birth_date_str)

    # Получаем формат даты пользователя
    date_format = await get_user_date_format(user_id)
    date_str = DateFormatter.format_date(birth_date, date_format)

    # Удаляем сообщение с календарём
    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        f"✅ Дата рождения сохранена: {date_str}\n"
        f"🎉 Ваш возраст: {age} лет"
    )

    # Очищаем состояние
    await state.clear()

    # Возврат в меню профиля
    await send_profile_menu(callback.message, user_id)

    await callback.answer()


async def handle_calendar_birth_date_navigation(callback: CallbackQuery, state: FSMContext, router):
    """Обработчик навигации по календарю для даты рождения"""
    from bot.calendar_keyboard import CalendarKeyboard
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    logger.info(f"Обработчик cal_birth_ навигация: {callback.data}")

    # Исключаем обработку выбора даты (она обрабатывается в handle_calendar_birth_date_selection)
    if callback.data.startswith("cal_birth_1_select_"):
        return

    # Обрабатываем пустые ячейки
    if callback.data == "cal_birth_empty":
        await callback.answer()
        return

    # Это навигация по календарю
    callback_data_normalized = callback.data.replace("cal_birth_", "cal_")
    new_keyboard = CalendarKeyboard.handle_navigation(callback_data_normalized, prefix="cal")

    if new_keyboard:
        # Меняем префикс обратно на cal_birth для даты рождения
        new_keyboard_json = new_keyboard.model_dump()
        for row in new_keyboard_json.get('inline_keyboard', []):
            for button in row:
                if 'callback_data' in button and button['callback_data'].startswith('cal_'):
                    button['callback_data'] = button['callback_data'].replace('cal_', 'cal_birth_', 1)

        # Пересоздаем клавиатуру с новыми callback_data
        new_rows = []
        for row in new_keyboard_json['inline_keyboard']:
            new_row = []
            for btn in row:
                new_row.append(InlineKeyboardButton(
                    text=btn['text'],
                    callback_data=btn['callback_data']
                ))
            new_rows.append(new_row)

        final_keyboard = InlineKeyboardMarkup(inline_keyboard=new_rows)

        try:
            await callback.message.edit_reply_markup(reply_markup=final_keyboard)
        except Exception as e:
            logger.error(f"Ошибка при обновлении календаря даты рождения: {str(e)}")

    await callback.answer()


def register_calendar_birth_handlers(router):
    """Регистрация обработчиков календаря даты рождения"""

    @router.callback_query(F.data.startswith("cal_birth_1_select_"))
    async def _handle_selection(callback: CallbackQuery, state: FSMContext):
        await handle_calendar_birth_date_selection(callback, state, router)

    @router.callback_query(F.data.startswith("cal_birth_"))
    async def _handle_navigation(callback: CallbackQuery, state: FSMContext):
        await handle_calendar_birth_date_navigation(callback, state, router)
