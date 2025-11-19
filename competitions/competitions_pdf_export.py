"""
Модуль для экспорта данных соревнований в PDF
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime, date, timedelta
from io import BytesIO
import logging
import os
import sys

from .competitions_queries import get_user_competitions_with_details
from .competitions_statistics import calculate_competitions_statistics
from .competitions_graphs import generate_competitions_graphs
from .competitions_utils import format_competition_distance, get_user_distance_unit
from utils.date_formatter import DateFormatter, get_user_date_format
from utils.unit_converter import km_to_miles

logger = logging.getLogger(__name__)


# Используем те же шрифты, что и для тренировок
def get_font_paths():
    """Получить пути к шрифтам DejaVu в зависимости от ОС"""

    # Сначала проверяем локальную папку fonts в проекте
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    local_fonts = os.path.join(project_root, 'fonts')

    if os.path.exists(local_fonts):
        dejavu_regular = os.path.join(local_fonts, 'DejaVuSans.ttf')
        dejavu_bold = os.path.join(local_fonts, 'DejaVuSans-Bold.ttf')

        if os.path.exists(dejavu_regular):
            logger.info(f"Используем локальные шрифты из: {local_fonts}")
            return {
                'regular': dejavu_regular,
                'bold': dejavu_bold if os.path.exists(dejavu_bold) else dejavu_regular
            }

    # Если нет локальных, ищем системные
    if sys.platform.startswith('win'):
        possible_paths = [
            r'C:\Windows\Fonts\DejaVuSans.ttf',
            r'C:\Windows\Fonts\dejavu-sans\DejaVuSans.ttf',
        ]
    elif sys.platform.startswith('darwin'):
        possible_paths = [
            '/Library/Fonts/DejaVuSans.ttf',
            '/System/Library/Fonts/Supplemental/DejaVuSans.ttf',
        ]
    else:  # Linux
        possible_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/dejavu/DejaVuSans.ttf',
        ]

    for path in possible_paths:
        if os.path.exists(path):
            bold_path = path.replace('DejaVuSans.ttf', 'DejaVuSans-Bold.ttf')
            logger.info(f"Используем системные шрифты: {path}")
            return {
                'regular': path,
                'bold': bold_path if os.path.exists(bold_path) else path
            }

    logger.warning("Шрифты DejaVu не найдены, будет использован шрифт по умолчанию")
    return None


# Регистрация шрифтов
font_paths = get_font_paths()
if font_paths:
    try:
        pdfmetrics.registerFont(TTFont('DejaVu', font_paths['regular']))
        pdfmetrics.registerFont(TTFont('DejaVu-Bold', font_paths['bold']))
        FONT_NAME = 'DejaVu'
        FONT_NAME_BOLD = 'DejaVu-Bold'
        logger.info("Шрифты DejaVu успешно зарегистрированы для PDF")
    except Exception as e:
        logger.error(f"Ошибка регистрации шрифтов: {e}")
        FONT_NAME = 'Helvetica'
        FONT_NAME_BOLD = 'Helvetica-Bold'
else:
    FONT_NAME = 'Helvetica'
    FONT_NAME_BOLD = 'Helvetica-Bold'


async def create_competitions_pdf(user_id: int, period_param: str) -> BytesIO:
    """
    Создает PDF документ с детальной информацией о соревнованиях

    Args:
        user_id: ID пользователя
        period_param: Параметр периода ("year", "all", "custom_YYYYMMDD_YYYYMMDD")

    Returns:
        BytesIO объект с PDF документом
    """
    # Получаем формат даты и единицы измерения пользователя
    user_format = await get_user_date_format(user_id)
    distance_unit = await get_user_distance_unit(user_id)

    # Определяем период и получаем данные
    if period_param == "year":
        start_date = date.today() - timedelta(days=365)
        end_date = date.today()
        period_name = "Последний год"
    elif period_param == "all":
        start_date = None
        end_date = None
        period_name = "Всё время"
    elif period_param.startswith("custom_"):
        # Формат: custom_YYYYMMDD_YYYYMMDD
        parts = period_param.split("_")
        if len(parts) == 3:
            start_date_str = parts[1]
            end_date_str = parts[2]
            start_date = date(int(start_date_str[:4]), int(start_date_str[4:6]), int(start_date_str[6:8]))
            end_date = date(int(end_date_str[:4]), int(end_date_str[4:6]), int(end_date_str[6:8]))
            period_name = DateFormatter.format_date_range(start_date, end_date, user_format)
        else:
            raise ValueError("Неверный формат произвольного периода")
    else:
        raise ValueError(f"Неверный параметр периода: {period_param}")

    # Получаем соревнования
    participants = await get_user_competitions_with_details(user_id, start_date, end_date)

    if not participants:
        raise ValueError("Нет данных за выбранный период")

    # Рассчитываем статистику
    stats = calculate_competitions_statistics(participants)

    buffer = BytesIO()

    # Создаем документ
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    # Получаем стили
    styles = getSampleStyleSheet()

    # Создаем кастомные стили
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=FONT_NAME_BOLD,
        fontSize=24,
        alignment=TA_CENTER,
        spaceAfter=30
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=FONT_NAME_BOLD,
        fontSize=16,
        spaceAfter=12,
        spaceBefore=12
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=11,
        spaceAfter=6
    )

    # Контент документа
    story = []

    # === СТРАНИЦА 1: ОБЛОЖКА И ОБЩАЯ СТАТИСТИКА ===
    story.append(Paragraph("Статистика соревнований", title_style))
    story.append(Paragraph(f"<i>{period_name}</i>", normal_style))
    story.append(Spacer(1, 1*cm))

    # Общая статистика в виде таблицы
    story.append(Paragraph("Общая статистика", heading_style))

    # Форматируем суммарную дистанцию с учетом единиц измерения
    total_distance = stats['total_distance']
    if distance_unit == 'мили':
        total_distance = km_to_miles(total_distance)
        distance_label = f"{total_distance:.1f} миль"
    else:
        distance_label = f"{total_distance:.1f} км"

    general_stats_data = [
        ['Показатель', 'Значение'],
        ['Всего соревнований', str(stats['total_competitions'])],
        ['Финишировано', str(stats['finished'])],
        ['Суммарный километраж', distance_label],
    ]

    if stats['registered'] > 0:
        general_stats_data.append(['Зарегистрировано', str(stats['registered'])])
    if stats['dns'] > 0:
        general_stats_data.append(['DNS (не стартовал)', str(stats['dns'])])
    if stats['dnf'] > 0:
        general_stats_data.append(['DNF (не финишировал)', str(stats['dnf'])])

    general_table = Table(general_stats_data, colWidths=[10*cm, 5*cm])
    general_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), FONT_NAME_BOLD),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    story.append(general_table)
    story.append(Spacer(1, 0.5*cm))

    # Личные рекорды
    if stats['personal_records']:
        story.append(Paragraph("Личные рекорды", heading_style))

        pr_data = [['Дистанция', 'Время', 'Темп', 'Соревнование', 'Дата']]
        for distance in sorted(stats['personal_records'].keys()):
            pr = stats['personal_records'][distance]
            formatted_date = DateFormatter.format_date(
                datetime.strptime(pr['date'], '%Y-%m-%d').date(),
                user_format
            ) if pr.get('date') else '-'

            # Форматируем дистанцию с учетом единиц измерения
            if distance_unit == 'мили':
                distance_miles = km_to_miles(distance)
                distance_str = f"{distance_miles:.1f} миль"
            else:
                distance_str = f"{distance} км"

            pr_data.append([
                distance_str,
                pr['time'],
                pr.get('pace', '-'),
                pr['competition'][:30],  # Ограничиваем длину
                formatted_date
            ])

        pr_table = Table(pr_data, colWidths=[2.5*cm, 2.5*cm, 2.5*cm, 6*cm, 2.5*cm])
        pr_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), FONT_NAME_BOLD),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))

        story.append(pr_table)
        story.append(Spacer(1, 0.5*cm))

    # Достижение целей
    if stats['finished'] > 0:
        total_with_goal = stats['goal_achievement']['achieved'] + stats['goal_achievement']['not_achieved']
        if total_with_goal > 0:
            story.append(Paragraph("Достижение целей", heading_style))
            achievement_rate = (stats['goal_achievement']['achieved'] / total_with_goal) * 100

            goal_text = f"Из {total_with_goal} соревнований с целевым временем:<br/>"
            goal_text += f"Выполнено: {stats['goal_achievement']['achieved']} ({achievement_rate:.0f}%)<br/>"
            goal_text += f"Не выполнено: {stats['goal_achievement']['not_achieved']}"

            story.append(Paragraph(goal_text, normal_style))
            story.append(Spacer(1, 0.5*cm))

    story.append(PageBreak())

    # === СТРАНИЦЫ С ГРАФИКАМИ ===
    try:
        story.append(Paragraph("Графики и визуализация", heading_style))
        story.append(Spacer(1, 0.5*cm))

        # Генерируем графики (возвращается список буферов)
        graph_buffers = await generate_competitions_graphs(participants, stats, period_name)

        # Добавляем каждый график на отдельную страницу
        for i, graph_buffer in enumerate(graph_buffers):
            img = Image(graph_buffer, width=17*cm, height=8.5*cm)
            story.append(img)
            if i < len(graph_buffers) - 1:  # Не добавляем PageBreak после последнего графика
                story.append(PageBreak())

        story.append(PageBreak())
    except Exception as e:
        logger.error(f"Ошибка при генерации графиков: {e}")
        story.append(Paragraph(f"<i>Графики недоступны</i>", normal_style))
        story.append(PageBreak())

    # === СТРАНИЦА 4+: ДЕТАЛЬНЫЙ СПИСОК СОРЕВНОВАНИЙ ===
    story.append(Paragraph("Детальный список соревнований", heading_style))
    story.append(Spacer(1, 0.5*cm))

    # Сортируем по дате (сначала новые)
    sorted_participants = sorted(participants, key=lambda x: x.get('date', ''), reverse=True)

    competitions_data = [['Дата', 'Название', 'Дистанция', 'Время', 'Темп', 'Место', 'Статус']]

    for p in sorted_participants:
        formatted_date = DateFormatter.format_date(
            datetime.strptime(p['date'], '%Y-%m-%d').date(),
            user_format
        ) if p.get('date') else '-'

        name = p.get('name', 'Без названия')[:40]  # Ограничиваем длину

        # Форматируем дистанцию с учетом единиц измерения
        if p.get('distance'):
            if distance_unit == 'мили':
                distance_miles = km_to_miles(p.get('distance'))
                distance = f"{distance_miles:.1f} миль"
            else:
                distance = f"{p.get('distance')} км"
        else:
            distance = '-'

        # Время и темп
        if p.get('status') == 'finished' and p.get('finish_time'):
            time_str = p['finish_time']
            # Рассчитываем темп
            from .competitions_statistics import calculate_pace
            pace = calculate_pace(p.get('distance', 0), p['finish_time'])
            pace_str = pace if pace else '-'
        else:
            time_str = '-'
            pace_str = '-'

        # Место
        place_overall = p.get('place_overall')
        place_category = p.get('place_age_category')
        if place_overall and place_category:
            place_str = f"{place_overall} / {place_category}"
        elif place_overall:
            place_str = str(place_overall)
        elif place_category:
            place_str = f"- / {place_category}"
        else:
            place_str = '-'

        # Статус
        status_map = {
            'finished': 'Финиш',
            'registered': 'Рег.',
            'dns': 'DNS',
            'dnf': 'DNF'
        }
        status_str = status_map.get(p.get('status'), p.get('status', '-'))

        competitions_data.append([
            formatted_date,
            name,
            distance,
            time_str,
            pace_str,
            place_str,
            status_str
        ])

    competitions_table = Table(
        competitions_data,
        colWidths=[1.4*cm, 4.5*cm, 1.4*cm, 1.4*cm, 1.4*cm, 2.8*cm, 1.3*cm]
    )
    competitions_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), FONT_NAME_BOLD),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # Чередующиеся цвета строк
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgreen]),
    ]))

    story.append(competitions_table)

    # Генерируем PDF
    doc.build(story)
    buffer.seek(0)

    logger.info(f"PDF экспорт соревнований успешно создан для пользователя {user_id}")
    return buffer
