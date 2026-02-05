"""
Обработчики для раздела помощи
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.types import ReplyKeyboardRemove

from help.help_keyboards import (
    get_help_main_menu,
    get_trainings_help_menu,
    get_coach_help_menu,
    get_faq_menu,
    get_back_to_help_button,
    get_back_to_section_button
)
from help.help_texts import *

router = Router()


@router.callback_query(F.data == "help:menu")
async def show_help_menu(callback: CallbackQuery):
    """Показать главное меню помощи"""
    await callback.message.edit_text(
        HELP_MAIN,
        reply_markup=get_help_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help:close")
async def close_help(callback: CallbackQuery):
    """Закрыть помощь"""
    await callback.message.delete()
    await callback.answer("Помощь закрыта")


# ===== НАЧАЛО РАБОТЫ =====

@router.callback_query(F.data == "help:start")
async def show_help_start(callback: CallbackQuery):
    """Начало работы"""
    await callback.message.edit_text(
        HELP_START,
        reply_markup=get_back_to_help_button(),
        parse_mode="HTML"
    )
    await callback.answer()


# ===== ТРЕНИРОВКИ =====

@router.callback_query(F.data == "help:trainings")
async def show_help_trainings(callback: CallbackQuery):
    """Меню помощи по тренировкам"""
    await callback.message.edit_text(
        HELP_TRAININGS,
        reply_markup=get_trainings_help_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help:training_run")
async def show_help_training_run(callback: CallbackQuery):
    """Помощь по кроссу"""
    await callback.message.edit_text(
        HELP_TRAINING_RUN,
        reply_markup=get_back_to_section_button("trainings"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help:training_swim")
async def show_help_training_swim(callback: CallbackQuery):
    """Помощь по плаванию"""
    await callback.message.edit_text(
        HELP_TRAINING_SWIM,
        reply_markup=get_back_to_section_button("trainings"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help:training_bike")
async def show_help_training_bike(callback: CallbackQuery):
    """Помощь по велотренировке"""
    await callback.message.edit_text(
        HELP_TRAINING_BIKE,
        reply_markup=get_back_to_section_button("trainings"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help:training_strength")
async def show_help_training_strength(callback: CallbackQuery):
    """Помощь по силовой"""
    await callback.message.edit_text(
        HELP_TRAINING_STRENGTH,
        reply_markup=get_back_to_section_button("trainings"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help:training_interval")
async def show_help_training_interval(callback: CallbackQuery):
    """Помощь по интервальной"""
    await callback.message.edit_text(
        HELP_TRAINING_INTERVAL,
        reply_markup=get_back_to_section_button("trainings"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help:view_trainings")
async def show_help_view_trainings(callback: CallbackQuery):
    """Помощь по просмотру тренировок"""
    await callback.message.edit_text(
        HELP_VIEW_TRAININGS,
        reply_markup=get_back_to_section_button("trainings"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help:delete_training")
async def show_help_delete_training(callback: CallbackQuery):
    """Помощь по удалению тренировок"""
    await callback.message.edit_text(
        HELP_DELETE_TRAINING,
        reply_markup=get_back_to_section_button("trainings"),
        parse_mode="HTML"
    )
    await callback.answer()


# ===== СОРЕВНОВАНИЯ =====

@router.callback_query(F.data == "help:competitions")
async def show_help_competitions(callback: CallbackQuery):
    """Помощь по соревнованиям"""
    await callback.message.edit_text(
        HELP_COMPETITIONS,
        reply_markup=get_back_to_help_button(),
        parse_mode="HTML"
    )
    await callback.answer()


# ===== ЗДОРОВЬЕ =====

@router.callback_query(F.data == "help:health")
async def show_help_health(callback: CallbackQuery):
    """Помощь по здоровью"""
    await callback.message.edit_text(
        HELP_HEALTH,
        reply_markup=get_back_to_help_button(),
        parse_mode="HTML"
    )
    await callback.answer()


# ===== РЕЙТИНГИ =====

@router.callback_query(F.data == "help:ratings")
async def show_help_ratings(callback: CallbackQuery):
    """Помощь по рейтингам"""
    await callback.message.edit_text(
        HELP_RATINGS,
        reply_markup=get_back_to_help_button(),
        parse_mode="HTML"
    )
    await callback.answer()


# ===== ТРЕНЕР =====

@router.callback_query(F.data == "help:coach")
async def show_help_coach(callback: CallbackQuery):
    """Меню помощи для тренера"""
    await callback.message.edit_text(
        "👨‍🏫 <b>КАБИНЕТ ТРЕНЕРА</b>\n\nВыберите раздел:",
        reply_markup=get_coach_help_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help:coach_become")
async def show_help_coach_become(callback: CallbackQuery):
    """Как стать тренером"""
    await callback.message.edit_text(
        HELP_COACH_BECOME,
        reply_markup=get_back_to_section_button("coach"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help:coach_students")
async def show_help_coach_students(callback: CallbackQuery):
    """Добавление учеников"""
    await callback.message.edit_text(
        HELP_COACH_STUDENTS,
        reply_markup=get_back_to_section_button("coach"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help:coach_assign")
async def show_help_coach_assign(callback: CallbackQuery):
    """Назначение тренировок"""
    await callback.message.edit_text(
        HELP_COACH_ASSIGN,
        reply_markup=get_back_to_section_button("coach"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help:coach_stats")
async def show_help_coach_stats(callback: CallbackQuery):
    """Просмотр статистики"""
    await callback.message.edit_text(
        HELP_COACH_STATS,
        reply_markup=get_back_to_section_button("coach"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help:coach_comments")
async def show_help_coach_comments(callback: CallbackQuery):
    """Комментарии"""
    await callback.message.edit_text(
        HELP_COACH_COMMENTS,
        reply_markup=get_back_to_section_button("coach"),
        parse_mode="HTML"
    )
    await callback.answer()


# ===== ЭКСПОРТ =====

@router.callback_query(F.data == "help:export")
async def show_help_export(callback: CallbackQuery):
    """Помощь по экспорту"""
    await callback.message.edit_text(
        HELP_EXPORT,
        reply_markup=get_back_to_help_button(),
        parse_mode="HTML"
    )
    await callback.answer()


# ===== TRAINING ASSISTANT =====

@router.callback_query(F.data == "help:assistant")
async def show_help_assistant(callback: CallbackQuery):
    """Помощь по Training Assistant"""
    await callback.message.edit_text(
        HELP_ASSISTANT,
        reply_markup=get_back_to_help_button(),
        parse_mode="HTML"
    )
    await callback.answer()


# ===== FAQ =====

@router.callback_query(F.data == "help:faq")
async def show_help_faq(callback: CallbackQuery):
    """FAQ меню"""
    await callback.message.edit_text(
        HELP_FAQ,
        reply_markup=get_faq_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help:faq_start")
async def show_help_faq_start(callback: CallbackQuery):
    """FAQ: Как начать"""
    await callback.message.edit_text(
        HELP_FAQ_START,
        reply_markup=get_back_to_section_button("faq"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help:faq_settings")
async def show_help_faq_settings(callback: CallbackQuery):
    """FAQ: Настройки"""
    await callback.message.edit_text(
        HELP_FAQ_SETTINGS,
        reply_markup=get_back_to_section_button("faq"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help:faq_units")
async def show_help_faq_units(callback: CallbackQuery):
    """FAQ: Единицы измерения"""
    await callback.message.edit_text(
        HELP_FAQ_UNITS,
        reply_markup=get_back_to_section_button("faq"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help:faq_dates")
async def show_help_faq_dates(callback: CallbackQuery):
    """FAQ: Формат даты"""
    await callback.message.edit_text(
        HELP_FAQ_DATES,
        reply_markup=get_back_to_section_button("faq"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help:faq_edit")
async def show_help_faq_edit(callback: CallbackQuery):
    """FAQ: Как изменить тренировку"""
    await callback.message.edit_text(
        HELP_FAQ_EDIT,
        reply_markup=get_back_to_section_button("faq"),
        parse_mode="HTML"
    )
    await callback.answer()
