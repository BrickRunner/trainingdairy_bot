"""
Обработчики для работы с тренерским разделом
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from coach.coach_keyboards import (
    get_coach_main_menu,
    get_students_list_keyboard,
    get_student_detail_keyboard,
    get_confirm_remove_student_keyboard,
    get_add_coach_keyboard,
    get_student_coach_info_keyboard,
    get_confirm_remove_coach_keyboard
)
from coach.coach_queries import (
    is_user_coach,
    get_coach_link_code,
    get_coach_students,
    remove_student_from_coach,
    find_coach_by_code,
    add_student_to_coach,
    get_student_coach,
    remove_coach_from_student
)
from bot.fsm import CoachStates
from database.queries import get_user

logger = logging.getLogger(__name__)
router = Router()


# ========== ТРЕНЕРСКАЯ СТОРОНА ==========

@router.callback_query(F.data == "coach:menu")
async def show_coach_menu(callback: CallbackQuery):
    """Показать главное меню тренера"""
    user_id = callback.from_user.id

    # Проверяем что пользователь тренер
    if not await is_user_coach(user_id):
        await callback.answer("У вас нет доступа к этому разделу", show_alert=True)
        return

    await callback.message.edit_text(
        "👨‍🏫 <b>Раздел тренера</b>\n\n"
        "Здесь вы можете управлять своими учениками, "
        "просматривать их тренировки и прогресс.",
        reply_markup=get_coach_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "coach:students")
async def show_students_list(callback: CallbackQuery):
    """Показать список учеников"""
    user_id = callback.from_user.id

    students = await get_coach_students(user_id)

    if not students:
        await callback.message.edit_text(
            "👥 <b>Мои ученики</b>\n\n"
            "У вас пока нет учеников.\n\n"
            "Чтобы добавить ученика, отправьте ему свою ссылку:\n"
            "👉 Тренер → Ссылка для учеников",
            reply_markup=get_students_list_keyboard([])
        )
    else:
        text = f"👥 <b>Мои ученики</b> ({len(students)})\n\n"
        text += "Выберите ученика для просмотра:\n"

        await callback.message.edit_text(
            text,
            reply_markup=get_students_list_keyboard(students)
        )

    await callback.answer()


@router.callback_query(F.data.startswith("coach:student:"))
async def show_student_detail(callback: CallbackQuery):
    """Показать детали ученика"""
    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    # Проверяем что это ученик данного тренера
    students = await get_coach_students(coach_id)
    student = next((s for s in students if s['id'] == student_id), None)

    if not student:
        await callback.answer("Ученик не найден", show_alert=True)
        return

    user_info = await get_user(student_id)

    text = f"👤 <b>{student['name']}</b>\n\n"
    text += f"📱 Telegram: @{student['username']}\n"
    text += f"📅 Подключён: {student['connected_at'][:10]}\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_student_detail_keyboard(student_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("coach:student_trainings:"))
async def show_student_trainings(callback: CallbackQuery):
    """Показать тренировки ученика"""
    student_id = int(callback.data.split(":")[2])

    # TODO: Реализовать просмотр тренировок ученика
    await callback.answer("Просмотр тренировок в разработке", show_alert=True)


@router.callback_query(F.data.startswith("coach:student_stats:"))
async def show_student_stats(callback: CallbackQuery):
    """Показать статистику ученика"""
    student_id = int(callback.data.split(":")[2])

    # TODO: Реализовать просмотр статистики ученика
    await callback.answer("Статистика в разработке", show_alert=True)


@router.callback_query(F.data.startswith("coach:student_health:"))
async def show_student_health(callback: CallbackQuery):
    """Показать данные о здоровье ученика"""
    student_id = int(callback.data.split(":")[2])

    # TODO: Реализовать просмотр здоровья ученика
    await callback.answer("Просмотр здоровья в разработке", show_alert=True)


@router.callback_query(F.data.startswith("coach:remove_student:"))
async def confirm_remove_student(callback: CallbackQuery):
    """Подтверждение удаления ученика"""
    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    students = await get_coach_students(coach_id)
    student = next((s for s in students if s['id'] == student_id), None)

    if not student:
        await callback.answer("Ученик не найден", show_alert=True)
        return

    await callback.message.edit_text(
        f"Вы уверены, что хотите удалить ученика <b>{student['name']}</b>?\n\n"
        f"После удаления ученик больше не сможет видеть ваши рекомендации.",
        reply_markup=get_confirm_remove_student_keyboard(student_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("coach:confirm_remove:"))
async def remove_student(callback: CallbackQuery):
    """Удалить ученика"""
    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    await remove_student_from_coach(coach_id, student_id)

    await callback.message.edit_text(
        "✅ Ученик удалён",
        reply_markup=get_students_list_keyboard([])
    )
    await callback.answer()


@router.callback_query(F.data == "coach:link")
async def show_coach_link(callback: CallbackQuery):
    """Показать ссылку для подключения учеников"""
    user_id = callback.from_user.id

    link_code = await get_coach_link_code(user_id)

    if not link_code:
        await callback.answer("Ошибка: код не найден", show_alert=True)
        return

    bot_username = (await callback.bot.me()).username

    text = "🔗 <b>Ваша ссылка для учеников</b>\n\n"
    text += f"Отправьте эту ссылку своим ученикам:\n\n"
    text += f"<code>https://t.me/{bot_username}?start=coach_{link_code}</code>\n\n"
    text += f"Или код для ввода вручную:\n"
    text += f"<code>{link_code}</code>\n\n"
    text += "После перехода по ссылке ученик автоматически подключится к вам."

    await callback.message.edit_text(
        text,
        reply_markup=get_coach_main_menu()
    )
    await callback.answer()


# ========== УЧЕНИЧЕСКАЯ СТОРОНА ==========

@router.callback_query(F.data == "student:my_coach")
async def show_my_coach(callback: CallbackQuery):
    """Показать информацию о тренере"""
    user_id = callback.from_user.id

    coach = await get_student_coach(user_id)

    if not coach:
        text = "👨‍🏫 <b>Мой тренер</b>\n\n"
        text += "У вас пока нет тренера.\n\n"
        text += "Чтобы добавить тренера, попросите у него код "
        text += "или ссылку для подключения."

        await callback.message.edit_text(
            text,
            reply_markup=get_add_coach_keyboard()
        )
    else:
        text = f"👨‍🏫 <b>Мой тренер</b>\n\n"
        text += f"👤 Имя: {coach['name']}\n"
        text += f"📱 Telegram: @{coach['username']}\n\n"
        text += "Ваш тренер может просматривать ваши тренировки и статистику."

        await callback.message.edit_text(
            text,
            reply_markup=get_student_coach_info_keyboard()
        )

    await callback.answer()


@router.callback_query(F.data == "student:add_coach")
async def add_coach_prompt(callback: CallbackQuery, state: FSMContext):
    """Запросить код тренера"""
    await callback.message.edit_text(
        "✏️ <b>Добавление тренера</b>\n\n"
        "Введите код тренера, который он вам отправил:",
    )
    await state.set_state(CoachStates.waiting_for_coach_code)
    await callback.answer()


@router.message(CoachStates.waiting_for_coach_code)
async def process_coach_code(message: Message, state: FSMContext):
    """Обработать введённый код тренера"""
    code = message.text.strip().upper()

    # Ищем тренера по коду
    coach_id = await find_coach_by_code(code)

    if not coach_id:
        await message.answer(
            "❌ Код тренера не найден.\n\n"
            "Проверьте правильность кода и попробуйте снова."
        )
        return

    # Добавляем связь
    student_id = message.from_user.id
    success = await add_student_to_coach(coach_id, student_id)

    if success:
        coach = await get_user(coach_id)
        await message.answer(
            f"✅ Вы успешно подключились к тренеру!\n\n"
            f"Ваш тренер: {coach.get('username', 'Неизвестно')}\n\n"
            f"Теперь тренер может просматривать ваши тренировки и статистику."
        )

        # Уведомляем тренера
        try:
            student_name = message.from_user.full_name
            await message.bot.send_message(
                coach_id,
                f"🎉 Новый ученик!\n\n"
                f"К вам подключился: {student_name}"
            )
        except Exception as e:
            logger.error(f"Failed to notify coach: {e}")
    else:
        await message.answer(
            "⚠️ Вы уже подключены к этому тренеру."
        )

    await state.clear()


@router.callback_query(F.data == "student:remove_coach")
async def confirm_remove_coach(callback: CallbackQuery):
    """Подтверждение отключения от тренера"""
    await callback.message.edit_text(
        "Вы уверены, что хотите отключиться от тренера?\n\n"
        "После этого тренер больше не сможет видеть ваши данные.",
        reply_markup=get_confirm_remove_coach_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "student:confirm_remove_coach")
async def remove_coach(callback: CallbackQuery):
    """Отключиться от тренера"""
    user_id = callback.from_user.id

    await remove_coach_from_student(user_id)

    await callback.message.edit_text(
        "✅ Вы отключились от тренера",
        reply_markup=get_add_coach_keyboard()
    )
    await callback.answer()
