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

    parsed = CalendarKeyboard.parse_callback_data(callback.data.replace("cal_birth_", "cal_"))
    selected_date = parsed.get("date")

    if not selected_date:
        await callback.answer("❌ Ошибка при выборе даты", show_alert=True)
        return

    from datetime import timedelta
    utc_now = datetime.utcnow()
    moscow_now = utc_now + timedelta(hours=3)
    today = moscow_now.date()

    if selected_date.date() > today:
        await callback.answer("❌ Дата рождения не может быть в будущем!", show_alert=True)
        return

    birth_date = selected_date.date()
    age = (today - birth_date).days // 365

    if age < 5 or age > 120:
        await callback.answer("❌ Пожалуйста, выберите корректную дату рождения (возраст от 5 до 120 лет).", show_alert=True)
        return

    user_id = callback.from_user.id
    birth_date_str = birth_date.strftime('%Y-%m-%d')
    await update_user_setting(user_id, 'birth_date', birth_date_str)

    date_format = await get_user_date_format(user_id)
    date_str = DateFormatter.format_date(birth_date, date_format)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        f"✅ Дата рождения сохранена: {date_str}\n"
        f"🎉 Ваш возраст: {age} лет"
    )

    await state.clear()

    await send_profile_menu(callback.message, user_id)

    await callback.answer()


async def handle_calendar_birth_date_navigation(callback: CallbackQuery, state: FSMContext, router):
    """Обработчик навигации по календарю для даты рождения"""
    from bot.calendar_keyboard import CalendarKeyboard

    logger.info(f"Обработчик cal_birth_ навигация: {callback.data}")

    if callback.data.startswith("cal_birth_1_select_"):
        return

    if callback.data == "cal_birth_empty":
        await callback.answer()
        return

    callback_data_normalized = callback.data.replace("cal_birth_", "cal_")
    logger.info(f"Нормализованный callback: {callback_data_normalized}")

    new_keyboard = CalendarKeyboard.handle_navigation(callback_data_normalized, prefix="cal", max_date=datetime.now())
    logger.info(f"Получена новая клавиатура: {new_keyboard is not None}")

    if new_keyboard:
        final_keyboard = CalendarKeyboard.replace_prefix_in_keyboard(new_keyboard, "cal", "cal_birth")
        logger.info(f"Финальная клавиатура после замены префикса: {final_keyboard is not None}")

        try:
            logger.info("Попытка обновить клавиатуру...")
            result = await callback.message.edit_reply_markup(reply_markup=final_keyboard)
            logger.info(f"Клавиатура успешно обновлена! Result type: {type(result)}")
        except Exception as e:
            error_text = str(e).lower()
            if "message is not modified" in error_text:
                logger.warning(f"⚠️ Telegram отклонил обновление - клавиатура не изменилась: {str(e)}")
            else:
                logger.error(f"❌ ОШИБКА при обновлении календаря даты рождения: {str(e)}", exc_info=True)
    else:
        logger.warning("new_keyboard is None!")

    await callback.answer()


def register_calendar_birth_handlers(router):
    """Регистрация обработчиков календаря даты рождения"""

    @router.callback_query(F.data.startswith("cal_birth_1_select_"))
    async def _handle_selection(callback: CallbackQuery, state: FSMContext):
        await handle_calendar_birth_date_selection(callback, state, router)

    @router.callback_query(F.data.startswith("cal_birth_"))
    async def _handle_navigation(callback: CallbackQuery, state: FSMContext):
        await handle_calendar_birth_date_navigation(callback, state, router)
