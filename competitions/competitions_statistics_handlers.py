"""
Обработчики для статистики и экспорта соревнований
"""

import logging
from datetime import datetime, date
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.fsm.context import FSMContext

from .competitions_fsm import CompetitionsExportStates
from .competitions_keyboards import (
    get_statistics_menu,
    get_export_period_menu,
    get_cancel_keyboard,
    get_competitions_main_menu
)
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from .competitions_queries import get_user_competitions_with_details
from .competitions_statistics import calculate_competitions_statistics, format_statistics_message
from .competitions_pdf_export import create_competitions_pdf
from utils.date_formatter import DateFormatter, get_user_date_format
from bot.calendar_keyboard import CalendarKeyboard

logger = logging.getLogger(__name__)
router = Router()


def get_back_to_export_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой возврата в меню экспорта"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="◀️ Назад в меню экспорта", callback_data="back_to_export_menu")
    )
    return builder.as_markup()


# Helper функции для форматирования дат
async def format_date_for_user(date_obj: date, user_id: int) -> str:
    """Форматировать дату согласно настройкам пользователя"""
    user_format = await get_user_date_format(user_id)
    return DateFormatter.format_date(date_obj, user_format)


async def get_date_format_description(user_id: int) -> str:
    """Получить описание формата даты для пользователя"""
    user_format = await get_user_date_format(user_id)
    return DateFormatter.get_format_description(user_format)


async def parse_user_date(date_str: str, user_id: int) -> date:
    """Распарсить дату согласно настройкам пользователя"""
    user_format = await get_user_date_format(user_id)
    return DateFormatter.parse_date(date_str, user_format)


@router.callback_query(F.data == "comp:stats:show")
async def show_statistics(callback: CallbackQuery):
    """Показать статистику соревнований"""
    user_id = callback.from_user.id

    await callback.answer("⏳ Рассчитываю статистику...")

    try:
        # Получаем все соревнования пользователя
        participants = await get_user_competitions_with_details(user_id)

        if not participants:
            try:
                await callback.message.edit_text(
                    "📊 У вас пока нет соревнований\n\n"
                    "Добавьте свои первые соревнования!",
                    reply_markup=get_statistics_menu()
                )
            except Exception:
                # Если сообщение не изменилось - просто игнорируем
                pass
            return

        # Рассчитываем статистику
        stats = calculate_competitions_statistics(participants)

        # Форматируем сообщение
        message_text = format_statistics_message(stats)

        try:
            await callback.message.edit_text(
                message_text,
                reply_markup=get_statistics_menu(),
                parse_mode="HTML"
            )
        except Exception:
            # Если сообщение не изменилось - просто игнорируем
            pass

    except Exception as e:
        logger.error(f"Ошибка при расчёте статистики: {e}")
        try:
            await callback.message.edit_text(
                "❌ Произошла ошибка при расчёте статистики\n\n"
                "Попробуйте позже",
                reply_markup=get_statistics_menu()
            )
        except Exception:
            # Если сообщение не изменилось - просто игнорируем
            pass


@router.callback_query(F.data == "comp:export:year")
async def export_year(callback: CallbackQuery):
    """Экспорт соревнований за последний год"""
    user_id = callback.from_user.id

    await callback.message.edit_text(
        "⏳ Генерирую PDF за последний год...\n\n"
        "Пожалуйста, подождите..."
    )

    try:
        # Генерируем PDF
        pdf_buffer = await create_competitions_pdf(user_id, "year")

        # Формируем имя файла
        filename = f"competitions_year_{date.today().strftime('%Y%m%d')}.pdf"

        # Отправляем PDF
        document = BufferedInputFile(pdf_buffer.read(), filename=filename)

        await callback.message.answer_document(
            document=document,
            caption="📄 Экспорт соревнований за последний год"
        )

        # Автоматически возвращаемся в меню экспорта
        from bot.keyboards import get_export_type_keyboard
        await callback.message.answer(
            "📥 <b>Экспорт в PDF</b>\n\n"
            "Выберите, что вы хотите экспортировать:",
            parse_mode="HTML",
            reply_markup=get_export_type_keyboard()
        )

    except ValueError as e:
        logger.error(f"Ошибка при экспорте PDF: {e}")
        # Возвращаем в меню выбора периода
        await callback.message.edit_text(
            f"❌ {str(e)}\n\n"
            "🏃 <b>Экспорт соревнований в PDF</b>\n\n"
            "Попробуйте выбрать другой период:",
            parse_mode="HTML",
            reply_markup=get_export_period_menu()
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка при экспорте PDF: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при создании PDF\n\n"
            "Попробуйте позже",
            reply_markup=get_back_to_export_menu_keyboard()
        )

    await callback.answer()


@router.callback_query(F.data == "comp:export:all")
async def export_all(callback: CallbackQuery):
    """Экспорт всех соревнований"""
    user_id = callback.from_user.id

    await callback.message.edit_text(
        "⏳ Генерирую PDF за всё время...\n\n"
        "Пожалуйста, подождите..."
    )

    try:
        # Генерируем PDF
        pdf_buffer = await create_competitions_pdf(user_id, "all")

        # Формируем имя файла
        filename = f"competitions_all_{date.today().strftime('%Y%m%d')}.pdf"

        # Отправляем PDF
        document = BufferedInputFile(pdf_buffer.read(), filename=filename)

        await callback.message.answer_document(
            document=document,
            caption="📄 Экспорт всех соревнований"
        )

        # Автоматически возвращаемся в меню экспорта
        from bot.keyboards import get_export_type_keyboard
        await callback.message.answer(
            "📥 <b>Экспорт в PDF</b>\n\n"
            "Выберите, что вы хотите экспортировать:",
            parse_mode="HTML",
            reply_markup=get_export_type_keyboard()
        )

    except ValueError as e:
        logger.error(f"Ошибка при экспорте PDF: {e}")
        # Возвращаем в меню выбора периода
        await callback.message.edit_text(
            f"❌ {str(e)}\n\n"
            "🏃 <b>Экспорт соревнований в PDF</b>\n\n"
            "Попробуйте выбрать другой период:",
            parse_mode="HTML",
            reply_markup=get_export_period_menu()
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка при экспорте PDF: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при создании PDF\n\n"
            "Попробуйте позже",
            reply_markup=get_back_to_export_menu_keyboard()
        )

    await callback.answer()


@router.callback_query(F.data == "comp:export:custom")
async def export_custom(callback: CallbackQuery, state: FSMContext):
    """Начать выбор произвольного периода для экспорта"""
    user_id = callback.from_user.id
    date_format_desc = await get_date_format_description(user_id)

    # Создаем клавиатуру с кнопкой отмены
    from aiogram.types import KeyboardButton
    from aiogram.utils.keyboard import ReplyKeyboardBuilder
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Отмена"))
    cancel_keyboard = builder.as_markup(resize_keyboard=True)

    # Отправляем календарь
    calendar_keyboard = CalendarKeyboard.create_calendar(
        calendar_format=1,
        current_date=datetime.now(),
        callback_prefix="comp_export_start",
        max_date=datetime.now()
    )

    await callback.message.edit_text(
        f"📅 <b>Произвольный период</b>\n\n"
        f"Выберите дату начала из календаря или введите вручную в формате {date_format_desc}",
        reply_markup=calendar_keyboard,
        parse_mode="HTML"
    )

    await callback.message.answer(
        ".",
        reply_markup=cancel_keyboard
    )

    await state.set_state(CompetitionsExportStates.waiting_for_start_date)
    await callback.answer()


# Обработчики календаря для начальной даты
@router.callback_query(F.data.startswith("comp_export_start_"))
async def process_export_start_calendar(callback: CallbackQuery, state: FSMContext):
    """Обработка навигации и выбора даты начала экспорта в календаре"""
    callback_data = callback.data
    logger.info(f"=== COMP EXPORT START CALENDAR CALLBACK: {callback_data} ===")

    # Проверка на выбор даты
    if "_select_" in callback_data:
        # Парсим выбранную дату используя parse_callback_data
        parsed = CalendarKeyboard.parse_callback_data(callback_data, prefix="comp_export_start")
        try:
            if not parsed or not parsed.get("date"):
                raise ValueError("Не удалось распарсить дату")
            selected_date = parsed["date"].date()

            logger.info(f"Selected start date: {selected_date}")

            # Сохраняем дату начала
            await state.update_data(export_start_date=selected_date)

            # Запрашиваем дату окончания
            user_id = callback.from_user.id
            date_format_desc = await get_date_format_description(user_id)
            formatted_start = await format_date_for_user(selected_date, user_id)

            # Создаем клавиатуру с кнопкой отмены
            from aiogram.utils.keyboard import ReplyKeyboardBuilder
            from aiogram.types import KeyboardButton
            builder = ReplyKeyboardBuilder()
            builder.row(KeyboardButton(text="❌ Отмена"))
            cancel_keyboard = builder.as_markup(resize_keyboard=True)

            await callback.message.answer(
                ".",
                reply_markup=cancel_keyboard
            )

            # Отправляем календарь для даты окончания
            calendar_keyboard = CalendarKeyboard.create_calendar(
                calendar_format=1,
                current_date=datetime.now(),
                callback_prefix="comp_export_end",
                max_date=datetime.now()
            )

            await callback.message.answer(
                f"✅ Дата начала: {formatted_start}\n\n"
                f"📅 Теперь выберите дату окончания периода\n\n"
                f"<i>📝 Или введите дату вручную в формате {date_format_desc}</i>",
                parse_mode="HTML",
                reply_markup=calendar_keyboard
            )

            await state.set_state(CompetitionsExportStates.waiting_for_end_date)
            await callback.answer()
            return

        except (IndexError, ValueError) as e:
            logger.error(f"Error parsing date from callback: {e}")
            await callback.answer("Ошибка при выборе даты")
            return

    # Обработка навигации
    new_keyboard = CalendarKeyboard.handle_navigation(callback_data, prefix="comp_export_start", max_date=datetime.now())

    if new_keyboard:
        try:
            await callback.message.edit_reply_markup(reply_markup=new_keyboard)
        except Exception as e:
            logger.error(f"Error updating keyboard: {e}")
    await callback.answer()


# Обработчики календаря для конечной даты
@router.callback_query(F.data.startswith("comp_export_end_"))
async def process_export_end_calendar(callback: CallbackQuery, state: FSMContext):
    """Обработка навигации и выбора даты окончания экспорта в календаре"""
    callback_data = callback.data
    logger.info(f"=== COMP EXPORT END CALENDAR CALLBACK: {callback_data} ===")

    # Проверка на выбор даты
    if "_select_" in callback_data:
        # Парсим выбранную дату используя parse_callback_data
        parsed = CalendarKeyboard.parse_callback_data(callback_data, prefix="comp_export_end")
        try:
            if not parsed or not parsed.get("date"):
                raise ValueError("Не удалось распарсить дату")
            selected_date = parsed["date"].date()

            logger.info(f"Selected end date: {selected_date}")

            # Получаем дату начала
            data = await state.get_data()
            start_date = data.get('export_start_date')
            user_id = callback.from_user.id

            # Проверяем, что start_date существует и дата окончания не раньше даты начала
            if not start_date:
                await callback.answer("Ошибка: не найдена дата начала. Попробуйте снова.")
                await state.clear()
                return

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
                # Формируем параметр периода в формате custom_YYYYMMDD_YYYYMMDD
                period_param = f"custom_{start_date.strftime('%Y%m%d')}_{selected_date.strftime('%Y%m%d')}"

                # Генерируем PDF
                pdf_buffer = await create_competitions_pdf(user_id, period_param)

                # Формируем имя файла
                filename = f"competitions_custom_{start_date.strftime('%Y%m%d')}_{selected_date.strftime('%Y%m%d')}.pdf"

                # Отправляем PDF
                document = BufferedInputFile(pdf_buffer.read(), filename=filename)

                formatted_start = await format_date_for_user(start_date, user_id)
                formatted_end = await format_date_for_user(selected_date, user_id)

                await callback.message.answer_document(
                    document=document,
                    caption=f"📄 Экспорт соревнований за период {formatted_start} - {formatted_end}"
                )

                logger.info(f"PDF экспорт соревнований успешно создан для пользователя {user_id}, период: {start_date} - {selected_date}")

                # Возвращаем в меню
                await callback.message.answer(
                    "✅ PDF успешно создан!\n\n"
                    "Выберите действие:",
                    reply_markup=get_back_to_export_menu_keyboard()
                )

            except ValueError as e:
                logger.error(f"Ошибка при экспорте PDF: {e}")
                # Возвращаем в меню выбора периода
                await callback.message.answer(
                    f"❌ {str(e)}\n\n"
                    "🏃 <b>Экспорт соревнований в PDF</b>\n\n"
                    "Попробуйте выбрать другой период или добавьте больше соревнований:",
                    parse_mode="HTML",
                    reply_markup=get_export_period_menu()
                )

            await callback.answer()
            return

        except (IndexError, ValueError) as e:
            logger.error(f"Error parsing date from callback: {e}")
            await callback.answer("Ошибка при выборе даты")
            return

    # Обработка навигации
    new_keyboard = CalendarKeyboard.handle_navigation(callback_data, prefix="comp_export_end", max_date=datetime.now())

    if new_keyboard:
        try:
            await callback.message.edit_reply_markup(reply_markup=new_keyboard)
        except Exception as e:
            logger.error(f"Error updating keyboard: {e}")
    await callback.answer()


@router.message(F.text == "❌ Отмена", CompetitionsExportStates.waiting_for_start_date)
@router.message(F.text == "❌ Отмена", CompetitionsExportStates.waiting_for_end_date)
async def cancel_export(message: Message, state: FSMContext):
    """Отмена процесса экспорта"""
    await state.clear()
    from aiogram.types import ReplyKeyboardRemove
    await message.answer(
        "Экспорт отменен",
        reply_markup=ReplyKeyboardRemove()
    )
