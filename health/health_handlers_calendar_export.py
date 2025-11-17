"""
Обработчики календарей для экспорта здоровья в PDF
"""
import logging
from datetime import date, datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext

from health.health_fsm import HealthExportStates
from health.health_keyboards import get_health_menu_keyboard
from health.health_queries import check_today_metrics_filled
from utils.date_formatter import DateFormatter, get_user_date_format

logger = logging.getLogger(__name__)
router = Router()


# Helper функции для форматирования дат
async def format_date_for_user(date_obj: date, user_id: int) -> str:
    """Форматировать дату согласно настройкам пользователя"""
    user_format = await get_user_date_format(user_id)
    return DateFormatter.format_date(date_obj, user_format)


async def get_date_format_description(user_id: int) -> str:
    """Получить описание формата даты для пользователя"""
    user_format = await get_user_date_format(user_id)
    return DateFormatter.get_format_description(user_format)


@router.callback_query(F.data.startswith("health_export_start_"))
async def process_export_start_calendar(callback: CallbackQuery, state: FSMContext):
    """Обработка навигации и выбора даты начала экспорта в календаре"""
    from bot.calendar_keyboard import CalendarKeyboard
    from aiogram.utils.keyboard import ReplyKeyboardBuilder
    from aiogram.types import KeyboardButton

    callback_data = callback.data
    logger.info(f"=== EXPORT START CALENDAR CALLBACK: {callback_data} ===")

    # Проверка на выбор даты
    if "_select_" in callback_data:
        # Парсим выбранную дату
        parts = callback_data.split("_")
        try:
            year = int(parts[4])
            month = int(parts[5])
            day = int(parts[6])
            selected_date = date(year, month, day)

            logger.info(f"Selected start date: {selected_date}")

            # Сохраняем дату начала
            await state.update_data(export_start_date=selected_date)

            # Запрашиваем дату окончания
            user_id = callback.from_user.id
            date_format_desc = await get_date_format_description(user_id)
            formatted_start = await format_date_for_user(selected_date, user_id)

            # Создаем клавиатуру с кнопкой отмены
            builder = ReplyKeyboardBuilder()
            builder.row(KeyboardButton(text="❌ Отмена"))
            cancel_keyboard = builder.as_markup(resize_keyboard=True)

            await callback.message.answer(
                f"✅ Дата начала: {formatted_start}\n\n"
                f"📅 Теперь введите дату окончания периода\n\n"
                f"<i>📝 Или введите дату вручную в формате {date_format_desc}</i>",
                parse_mode="HTML",
                reply_markup=cancel_keyboard
            )

            # Отправляем календарь для даты окончания
            calendar_keyboard = CalendarKeyboard.create_calendar(
                calendar_format=1,
                current_date=datetime.now(),
                callback_prefix="health_export_end",
                max_date=datetime.now()
            )

            await callback.message.answer(
                "📅 Календарь:",
                reply_markup=calendar_keyboard
            )

            await state.set_state(HealthExportStates.waiting_for_end_date)
            await callback.answer()
            return

        except (IndexError, ValueError) as e:
            logger.error(f"Error parsing date from callback: {e}")
            await callback.answer("Ошибка при выборе даты")
            return

    # Обработка навигации
    new_keyboard = CalendarKeyboard.handle_navigation(callback_data, prefix="health_export_start", max_date=datetime.now())

    if new_keyboard:
        try:
            await callback.message.edit_reply_markup(reply_markup=new_keyboard)
        except Exception as e:
            logger.error(f"Error updating keyboard: {e}")
    await callback.answer()


@router.callback_query(F.data.startswith("health_export_end_"))
async def process_export_end_calendar(callback: CallbackQuery, state: FSMContext):
    """Обработка навигации и выбора даты окончания экспорта в календаре"""
    from bot.calendar_keyboard import CalendarKeyboard

    callback_data = callback.data
    logger.info(f"=== EXPORT END CALENDAR CALLBACK: {callback_data} ===")

    # Проверка на выбор даты
    if "_select_" in callback_data:
        # Парсим выбранную дату
        parts = callback_data.split("_")
        try:
            year = int(parts[4])
            month = int(parts[5])
            day = int(parts[6])
            selected_date = date(year, month, day)

            logger.info(f"Selected end date: {selected_date}")

            # Получаем дату начала
            data = await state.get_data()
            start_date = data.get('export_start_date')
            user_id = callback.from_user.id

            # Проверяем, что дата окончания не раньше даты начала
            if selected_date < start_date:
                formatted_start = await format_date_for_user(start_date, user_id)
                await callback.answer(
                    f"❌ Дата окончания не может быть раньше даты начала ({formatted_start})!",
                    show_alert=True
                )
                return

            # Очищаем состояние
            await state.clear()

            # Показываем сообщение о генерации
            await callback.message.answer(
                "⏳ Генерирую PDF...",
                reply_markup={"remove_keyboard": True}
            )

            try:
                # Импортируем функцию экспорта
                from health.health_pdf_export import create_health_pdf

                # Генерируем PDF
                pdf_buffer = await create_health_pdf(user_id, "custom", start_date, selected_date)

                # Формируем имя файла
                filename = f"health_custom_{start_date.strftime('%Y%m%d')}_{selected_date.strftime('%Y%m%d')}.pdf"

                # Отправляем PDF
                document = BufferedInputFile(pdf_buffer.read(), filename=filename)

                formatted_start = await format_date_for_user(start_date, user_id)
                formatted_end = await format_date_for_user(selected_date, user_id)

                await callback.message.answer_document(
                    document=document,
                    caption=f"📄 Экспорт данных здоровья за период {formatted_start} - {formatted_end}"
                )

                logger.info(f"PDF экспорт здоровья успешно создан для пользователя {user_id}, период: {start_date} - {selected_date}")

                # Возвращаем в меню
                filled = await check_today_metrics_filled(user_id)
                status_text = "📋 <b>Статус на сегодня:</b>\n"
                status_text += f"{'✅' if filled['morning_pulse'] else '❌'} Утренний пульс\n"
                status_text += f"{'✅' if filled['weight'] else '❌'} Вес\n"
                status_text += f"{'✅' if filled['sleep_duration'] else '❌'} Сон\n"

                await callback.message.answer(
                    f"❤️ <b>Здоровье и метрики</b>\n\n"
                    f"{status_text}\n"
                    f"Выберите действие:",
                    reply_markup=get_health_menu_keyboard(),
                    parse_mode="HTML"
                )

            except ValueError as e:
                logger.error(f"Ошибка при экспорте PDF: {e}")
                await callback.message.answer(
                    f"❌ {str(e)}\n\n"
                    "Попробуйте выбрать другой период или внесите больше данных."
                )

            await callback.answer()
            return

        except (IndexError, ValueError) as e:
            logger.error(f"Error parsing date from callback: {e}")
            await callback.answer("Ошибка при выборе даты")
            return

    # Обработка навигации
    new_keyboard = CalendarKeyboard.handle_navigation(callback_data, prefix="health_export_end", max_date=datetime.now())

    if new_keyboard:
        try:
            await callback.message.edit_reply_markup(reply_markup=new_keyboard)
        except Exception as e:
            logger.error(f"Error updating keyboard: {e}")
    await callback.answer()
