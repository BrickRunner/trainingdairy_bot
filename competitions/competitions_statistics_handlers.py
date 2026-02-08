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
from .competitions_graphs import generate_competitions_graphs
from utils.date_formatter import DateFormatter, get_user_date_format
from bot.calendar_keyboard import CalendarKeyboard
from database.queries import get_user_settings

logger = logging.getLogger(__name__)
router = Router()


def get_back_to_export_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой возврата в меню экспорта"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="◀️ Назад в меню экспорта", callback_data="back_to_export_menu")
    )
    return builder.as_markup()


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


async def show_statistics_for_period(callback: CallbackQuery, period: str = 'all', state: FSMContext = None):
    """Показать статистику соревнований с графиками за определенный период

    Args:
        callback: Callback query
        period: Период ('month', 'halfyear', 'year', 'all')
        state: FSM контекст для сохранения ID сообщений
    """
    user_id = callback.from_user.id

    await callback.answer("⏳ Рассчитываю статистику...")

    if state:
        data = await state.get_data()
        old_message_ids = data.get('statistics_message_ids', [])
        for msg_id in old_message_ids:
            try:
                await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
            except Exception:
                pass
        await state.update_data(statistics_message_ids=[])

    try:
        from datetime import datetime, timedelta

        today = datetime.now().date()
        if period == 'month':
            start_date = today.replace(day=1)
            period_text = "за текущий месяц"
        elif period == 'halfyear':
            start_date = today - timedelta(days=180)
            period_text = "за последние полгода"
        elif period == 'year':
            start_date = today.replace(month=1, day=1)
            period_text = "за текущий год"
        else:  
            start_date = None
            period_text = "весь период"

        end_date = today

        all_participants = await get_user_competitions_with_details(user_id)

        if start_date:
            participants = [
                p for p in all_participants
                if datetime.strptime(p['date'], '%Y-%m-%d').date() >= start_date
            ]
        else:
            participants = all_participants

        if not participants:
            try:
                await callback.message.edit_text(
                    f"📊 У вас нет соревнований {period_text}\n\n"
                    "Выберите другой период или добавьте соревнования!",
                    reply_markup=get_statistics_menu(period)
                )
            except Exception:
                pass

            menu_msg = await callback.message.answer(
                "🏆 <b>СОРЕВНОВАНИЯ</b>\n\n"
                "Выберите раздел:",
                parse_mode="HTML",
                reply_markup=get_competitions_main_menu()
            )

            if state:
                await state.update_data(statistics_message_ids=[menu_msg.message_id])
            return

        stats = calculate_competitions_statistics(participants)

        settings = await get_user_settings(user_id)
        distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

        message_text = format_statistics_message(stats, distance_unit)
        message_text = f"📊 <b>СТАТИСТИКА {period_text.upper()}</b>\n\n" + message_text.split('\n\n', 1)[1]

        try:
            await callback.message.edit_text(
                message_text,
                reply_markup=get_statistics_menu(period),
                parse_mode="HTML"
            )
        except Exception:
            pass

        new_message_ids = []
        try:
            settings = await get_user_settings(user_id)
            distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

            graph_buffers = await generate_competitions_graphs(
                participants,
                stats,
                period_text,
                distance_unit
            )

            for i, buf in enumerate(graph_buffers):
                caption = f"📊 Графики статистики соревнований {period_text}" if i == 0 else None
                sent_msg = await callback.message.answer_photo(
                    photo=BufferedInputFile(buf.read(), filename=f"competitions_stats_{i+1}.png"),
                    caption=caption
                )
                new_message_ids.append(sent_msg.message_id)
                buf.close()

        except Exception as graph_error:
            logger.error(f"Ошибка при генерации графиков: {graph_error}")

        menu_msg = await callback.message.answer(
            "🏆 <b>СОРЕВНОВАНИЯ</b>\n\n"
            "Выберите раздел:",
            parse_mode="HTML",
            reply_markup=get_competitions_main_menu()
        )
        new_message_ids.append(menu_msg.message_id)

        if state:
            await state.update_data(statistics_message_ids=new_message_ids)

    except Exception as e:
        logger.error(f"Ошибка при расчёте статистики: {e}")
        try:
            await callback.message.edit_text(
                "❌ Произошла ошибка при расчёте статистики\n\n"
                "Попробуйте позже",
                reply_markup=get_statistics_menu(period)
            )
        except Exception:
            pass

        menu_msg = await callback.message.answer(
            "🏆 <b>СОРЕВНОВАНИЯ</b>\n\n"
            "Выберите раздел:",
            parse_mode="HTML",
            reply_markup=get_competitions_main_menu()
        )

        if state:
            await state.update_data(statistics_message_ids=[menu_msg.message_id])


@router.callback_query(F.data == "comp:stats:show")
async def show_statistics(callback: CallbackQuery):
    """Показать меню выбора периода для статистики соревнований (месяц, полгода, год)"""
    await callback.message.edit_text(
        "📊 <b>СТАТИСТИКА СОРЕВНОВАНИЙ</b>\n\n"
        "Выберите период для просмотра статистики:\n\n"
        "📅 <b>Месяц</b> - текущий месяц\n"
        "📅 <b>Полгода</b> - последние 6 месяцев\n"
        "📅 <b>Год</b> - текущий год",
        reply_markup=get_statistics_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "comp:stats:month")
async def show_statistics_month(callback: CallbackQuery, state: FSMContext):
    """Показать статистику за месяц"""
    await show_statistics_for_period(callback, 'month', state)


@router.callback_query(F.data == "comp:stats:halfyear")
async def show_statistics_halfyear(callback: CallbackQuery, state: FSMContext):
    """Показать статистику за полгода"""
    await show_statistics_for_period(callback, 'halfyear', state)


@router.callback_query(F.data == "comp:stats:year")
async def show_statistics_year(callback: CallbackQuery, state: FSMContext):
    """Показать статистику за год"""
    await show_statistics_for_period(callback, 'year', state)


@router.callback_query(F.data == "comp:export:halfyear")
async def export_halfyear(callback: CallbackQuery):
    """Экспорт соревнований за последние полгода"""
    user_id = callback.from_user.id

    await callback.answer("⏳ Генерирую PDF...", show_alert=True)

    try:
        pdf_buffer = await create_competitions_pdf(user_id, "halfyear")

        filename = f"competitions_halfyear_{date.today().strftime('%Y%m%d')}.pdf"

        document = BufferedInputFile(pdf_buffer.read(), filename=filename)

        await callback.message.answer_document(
            document=document,
            caption="📄 Экспорт соревнований за последние полгода"
        )

        from bot.keyboards import get_export_type_keyboard
        await callback.message.answer(
            "📥 <b>Экспорт в PDF</b>\n\n"
            "Выберите, что вы хотите экспортировать:",
            parse_mode="HTML",
            reply_markup=get_export_type_keyboard()
        )

    except ValueError as e:
        logger.error(f"Ошибка при экспорте PDF: {e}")
        await callback.answer()
        await callback.message.edit_text(
            f"❌ {str(e)}\n\n"
            "🏃 <b>Экспорт соревнований в PDF</b>\n\n"
            "Попробуйте выбрать другой период:",
            parse_mode="HTML",
            reply_markup=get_export_period_menu()
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка при экспорте PDF: {e}")
        await callback.answer()
        await callback.message.edit_text(
            "❌ Произошла ошибка при создании PDF\n\n"
            "Попробуйте позже",
            reply_markup=get_back_to_export_menu_keyboard()
        )


@router.callback_query(F.data == "comp:export:year")
async def export_year(callback: CallbackQuery):
    """Экспорт соревнований за последний год"""
    user_id = callback.from_user.id

    await callback.answer("⏳ Генерирую PDF...", show_alert=True)

    try:
        pdf_buffer = await create_competitions_pdf(user_id, "year")

        filename = f"competitions_year_{date.today().strftime('%Y%m%d')}.pdf"

        document = BufferedInputFile(pdf_buffer.read(), filename=filename)

        await callback.message.answer_document(
            document=document,
            caption="📄 Экспорт соревнований за последний год"
        )

        from bot.keyboards import get_export_type_keyboard
        await callback.message.answer(
            "📥 <b>Экспорт в PDF</b>\n\n"
            "Выберите, что вы хотите экспортировать:",
            parse_mode="HTML",
            reply_markup=get_export_type_keyboard()
        )

    except ValueError as e:
        logger.error(f"Ошибка при экспорте PDF: {e}")
        await callback.answer()
        await callback.message.edit_text(
            f"❌ {str(e)}\n\n"
            "🏃 <b>Экспорт соревнований в PDF</b>\n\n"
            "Попробуйте выбрать другой период:",
            parse_mode="HTML",
            reply_markup=get_export_period_menu()
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка при экспорте PDF: {e}")
        await callback.answer()
        await callback.message.edit_text(
            "❌ Произошла ошибка при создании PDF\n\n"
            "Попробуйте позже",
            reply_markup=get_back_to_export_menu_keyboard()
        )


@router.callback_query(F.data == "comp:export:custom")
async def export_custom(callback: CallbackQuery, state: FSMContext):
    """Начать выбор произвольного периода для экспорта"""
    user_id = callback.from_user.id
    date_format_desc = await get_date_format_description(user_id)

    calendar_keyboard = CalendarKeyboard.create_calendar(
        calendar_format=1,
        current_date=datetime.now(),
        callback_prefix="comp_export_start",
        max_date=datetime.now(),
        show_cancel=True,
        cancel_callback="comp:export:cancel"
    )

    await callback.message.edit_text(
        f"📅 <b>Произвольный период</b>\n\n"
        f"Выберите дату начала из календаря или введите вручную в формате {date_format_desc}",
        reply_markup=calendar_keyboard,
        parse_mode="HTML"
    )

    await state.set_state(CompetitionsExportStates.waiting_for_start_date)
    await callback.answer()


@router.callback_query(F.data.startswith("comp_export_start_"))
async def process_export_start_calendar(callback: CallbackQuery, state: FSMContext):
    """Обработка навигации и выбора даты начала экспорта в календаре"""
    callback_data = callback.data
    logger.info(f"=== COMP EXPORT START CALENDAR CALLBACK: {callback_data} ===")

    if "_select_" in callback_data:
        parsed = CalendarKeyboard.parse_callback_data(callback_data, prefix="comp_export_start")
        try:
            if not parsed or not parsed.get("date"):
                raise ValueError("Не удалось распарсить дату")
            selected_date = parsed["date"].date()

            logger.info(f"Selected start date: {selected_date}")

            await state.update_data(export_start_date=selected_date)

            user_id = callback.from_user.id
            date_format_desc = await get_date_format_description(user_id)
            formatted_start = await format_date_for_user(selected_date, user_id)

            calendar_keyboard = CalendarKeyboard.create_calendar(
                calendar_format=1,
                current_date=datetime.now(),
                callback_prefix="comp_export_end",
                max_date=datetime.now(),
                show_cancel=True,
                cancel_callback="comp:export:cancel"
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

    new_keyboard = CalendarKeyboard.handle_navigation(callback_data, prefix="comp_export_start", max_date=datetime.now(), show_cancel=True, cancel_callback="comp:export:cancel")

    if new_keyboard:
        try:
            await callback.message.edit_reply_markup(reply_markup=new_keyboard)
        except Exception as e:
            logger.error(f"Error updating keyboard: {e}")
    await callback.answer()


@router.callback_query(F.data == "comp:export:cancel")
async def cancel_export_inline(callback: CallbackQuery, state: FSMContext):
    """Отмена процесса экспорта (inline кнопка)"""
    await state.clear()
    from bot.keyboards import get_export_type_keyboard

    await callback.message.edit_text(
        "📥 <b>Экспорт в PDF</b>\n\n"
        "Выберите, что вы хотите экспортировать:",
        parse_mode="HTML",
        reply_markup=get_export_type_keyboard()
    )
    await callback.answer("Экспорт отменен")


@router.callback_query(F.data.startswith("comp_export_end_"))
async def process_export_end_calendar(callback: CallbackQuery, state: FSMContext):
    """Обработка навигации и выбора даты окончания экспорта в календаре"""
    callback_data = callback.data
    logger.info(f"=== COMP EXPORT END CALENDAR CALLBACK: {callback_data} ===")

    if "_select_" in callback_data:
        parsed = CalendarKeyboard.parse_callback_data(callback_data, prefix="comp_export_end")
        try:
            if not parsed or not parsed.get("date"):
                raise ValueError("Не удалось распарсить дату")
            selected_date = parsed["date"].date()

            logger.info(f"Selected end date: {selected_date}")

            data = await state.get_data()
            start_date = data.get('export_start_date')
            user_id = callback.from_user.id

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

            await state.clear()

            await callback.answer("⏳ Генерирую PDF...", show_alert=True)

            try:
                period_param = f"custom_{start_date.strftime('%Y%m%d')}_{selected_date.strftime('%Y%m%d')}"

                pdf_buffer = await create_competitions_pdf(user_id, period_param)

                filename = f"competitions_custom_{start_date.strftime('%Y%m%d')}_{selected_date.strftime('%Y%m%d')}.pdf"

                document = BufferedInputFile(pdf_buffer.read(), filename=filename)

                formatted_start = await format_date_for_user(start_date, user_id)
                formatted_end = await format_date_for_user(selected_date, user_id)

                from aiogram.types import ReplyKeyboardRemove
                await callback.message.answer_document(
                    document=document,
                    caption=f"📄 Экспорт соревнований за период {formatted_start} - {formatted_end}",
                    reply_markup=ReplyKeyboardRemove()
                )

                logger.info(f"PDF экспорт соревнований успешно создан для пользователя {user_id}, период: {start_date} - {selected_date}")

                from bot.keyboards import get_export_type_keyboard
                await callback.message.answer(
                    "📥 <b>Экспорт в PDF</b>\n\n"
                    "Выберите, что вы хотите экспортировать:",
                    parse_mode="HTML",
                    reply_markup=get_export_type_keyboard()
                )

            except ValueError as e:
                logger.error(f"Ошибка при экспорте PDF: {e}")
                await callback.message.answer(
                    f"❌ {str(e)}\n\n"
                    "🏃 <b>Экспорт соревнований в PDF</b>\n\n"
                    "Попробуйте выбрать другой период или добавьте больше соревнований:",
                    parse_mode="HTML",
                    reply_markup=get_export_period_menu()
                )
            return

        except (IndexError, ValueError) as e:
            logger.error(f"Error parsing date from callback: {e}")
            await callback.answer("Ошибка при выборе даты")
            return

    new_keyboard = CalendarKeyboard.handle_navigation(callback_data, prefix="comp_export_end", max_date=datetime.now(), show_cancel=True, cancel_callback="comp:export:cancel")

    if new_keyboard:
        try:
            await callback.message.edit_reply_markup(reply_markup=new_keyboard)
        except Exception as e:
            logger.error(f"Error updating keyboard: {e}")
    await callback.answer()



@router.message(CompetitionsExportStates.waiting_for_start_date)
async def process_export_start_date_manual(message: Message, state: FSMContext):
    """Обработка ручного ввода даты начала периода экспорта"""
    user_id = message.from_user.id

    try:
        start_date = await parse_user_date(message.text, user_id)

        if start_date > date.today():
            await message.answer(
                "❌ Дата начала не может быть в будущем!\n\n"
                "Введите корректную дату:"
            )
            return

        await state.update_data(export_start_date=start_date)

        date_format_desc = await get_date_format_description(user_id)
        formatted_start = await format_date_for_user(start_date, user_id)

        calendar_keyboard = CalendarKeyboard.create_calendar(
            calendar_format=1,
            current_date=datetime.now(),
            callback_prefix="comp_export_end",
            max_date=datetime.now(),
            show_cancel=True,
            cancel_callback="comp:export:cancel"
        )

        await message.answer(
            f"✅ Дата начала: {formatted_start}\n\n"
            f"📅 Теперь выберите дату окончания из календаря или введите вручную в формате {date_format_desc}",
            parse_mode="HTML",
            reply_markup=calendar_keyboard
        )

        await state.set_state(CompetitionsExportStates.waiting_for_end_date)

    except ValueError:
        date_format_desc = await get_date_format_description(user_id)
        await message.answer(
            f"❌ Неверный формат даты!\n\n"
            f"Введите дату в формате {date_format_desc}"
        )


@router.message(CompetitionsExportStates.waiting_for_end_date)
async def process_export_end_date_manual(message: Message, state: FSMContext):
    """Обработка ручного ввода даты окончания периода экспорта и генерация PDF"""
    user_id = message.from_user.id

    try:
        end_date = await parse_user_date(message.text, user_id)

        if end_date > date.today():
            await message.answer(
                "❌ Дата окончания не может быть в будущем!\n\n"
                "Введите корректную дату:"
            )
            return

        data = await state.get_data()
        start_date = data.get('export_start_date')

        if end_date < start_date:
            formatted_start = await format_date_for_user(start_date, user_id)
            await message.answer(
                f"❌ Дата окончания не может быть раньше даты начала ({formatted_start})!\n\n"
                "Введите корректную дату:"
            )
            return

        await state.clear()

        try:
            period_param = f"custom_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"

            pdf_buffer = await create_competitions_pdf(user_id, period_param)

            filename = f"competitions_custom_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"

            document = BufferedInputFile(pdf_buffer.read(), filename=filename)

            formatted_start = await format_date_for_user(start_date, user_id)
            formatted_end = await format_date_for_user(end_date, user_id)

            await message.answer_document(
                document=document,
                caption=f"📄 Экспорт соревнований за период {formatted_start} - {formatted_end}"
            )

            logger.info(f"PDF экспорт соревнований успешно создан для пользователя {user_id}, период: {start_date} - {end_date}")

            from bot.keyboards import get_export_type_keyboard
            await message.answer(
                "📥 <b>Экспорт в PDF</b>\n\n"
                "Выберите, что вы хотите экспортировать:",
                parse_mode="HTML",
                reply_markup=get_export_type_keyboard()
            )

        except ValueError as e:
            logger.error(f"Ошибка при экспорте PDF: {e}")
            await message.answer(
                f"❌ {str(e)}\n\n"
                "🏃 <b>Экспорт соревнований в PDF</b>\n\n"
                "Попробуйте выбрать другой период или добавьте больше соревнований:",
                parse_mode="HTML",
                reply_markup=get_export_period_menu()
            )

    except ValueError:
        date_format_desc = await get_date_format_description(user_id)
        await message.answer(
            f"❌ Неверный формат даты!\n\n"
            f"Введите дату в формате {date_format_desc}"
        )

