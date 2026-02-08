"""
Модуль для экспорта тренировочных планов в PDF
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from io import BytesIO
import logging
import os
import sys

logger = logging.getLogger(__name__)

def get_font_paths():
    """Получить пути к шрифтам DejaVu в зависимости от ОС"""

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    local_fonts = os.path.join(project_root, 'fonts')

    if os.path.exists(local_fonts):
        dejavu_regular = os.path.join(local_fonts, 'DejaVuSans.ttf')
        dejavu_bold = os.path.join(local_fonts, 'DejaVuSans-Bold.ttf')

        if os.path.exists(dejavu_regular):
            return {
                'regular': dejavu_regular,
                'bold': dejavu_bold if os.path.exists(dejavu_bold) else dejavu_regular
            }

    if sys.platform.startswith('win'):
        possible_paths = [
            r'C:\Windows\Fonts\DejaVuSans.ttf',
            r'C:\Windows\Fonts\dejavu-sans\DejaVuSans.ttf',
            os.path.expanduser(r'~\AppData\Local\Microsoft\Windows\Fonts\DejaVuSans.ttf'),
        ]
    else:
        possible_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/dejavu/DejaVuSans.ttf',
            '/System/Library/Fonts/Supplemental/DejaVuSans.ttf',
        ]

    for path in possible_paths:
        if os.path.exists(path):
            font_dir = os.path.dirname(path)
            bold_path = os.path.join(font_dir, 'DejaVuSans-Bold.ttf')
            return {
                'regular': path,
                'bold': bold_path if os.path.exists(bold_path) else path
            }

    return None

font_paths = get_font_paths()
FONT_NAME = 'DejaVuSans'
FONT_NAME_BOLD = 'DejaVuSans-Bold'

if font_paths:
    try:
        pdfmetrics.registerFont(TTFont(FONT_NAME, font_paths['regular']))
        if os.path.exists(font_paths['bold']):
            pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, font_paths['bold']))
        else:
            FONT_NAME_BOLD = FONT_NAME
        logger.info(f"✅ Шрифты DejaVu загружены для Training Assistant PDF")
    except Exception as e:
        logger.warning(f"❌ Не удалось загрузить шрифты DejaVu: {e}")
        FONT_NAME = 'Helvetica'
        FONT_NAME_BOLD = 'Helvetica-Bold'
else:
    logger.warning("❌ Шрифты DejaVu не найдены! PDF будет без кириллицы.")
    FONT_NAME = 'Helvetica'
    FONT_NAME_BOLD = 'Helvetica-Bold'


async def create_training_plan_pdf(plan_data: dict, sport_type: str, plan_duration: str, available_days: list) -> BytesIO:
    """
    Создает PDF с тренировочным планом

    Args:
        plan_data: Данные плана от AI (dict с ключами plan, explanation, weekly_volume, etc.)
        sport_type: Вид спорта (run, swim, bike, triathlon)
        plan_duration: Длительность плана (week, month)
        available_days: Доступные дни для тренировок

    Returns:
        BytesIO объект с PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=FONT_NAME_BOLD,
        fontSize=18,
        textColor=colors.HexColor('#1a73e8'),
        spaceAfter=20,
        alignment=TA_CENTER
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=FONT_NAME_BOLD,
        fontSize=14,
        textColor=colors.HexColor('#1a73e8'),
        spaceAfter=10,
        spaceBefore=15
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=10,
        leading=14
    )

    bold_style = ParagraphStyle(
        'CustomBold',
        parent=styles['Normal'],
        fontName=FONT_NAME_BOLD,
        fontSize=10,
        leading=14
    )

    story = []

    sport_names = {
        'run': 'Бег',
        'swim': 'Плавание',
        'bike': 'Велоспорт',
        'triathlon': 'Триатлон'
    }
    sport_name = sport_names.get(sport_type, sport_type.capitalize())

    duration_names = {
        'week': 'неделю',
        'month': 'месяц'
    }
    duration_name = duration_names.get(plan_duration, plan_duration)

    story.append(Paragraph(f"Тренировочный план: {sport_name}", title_style))
    story.append(Paragraph(f"Период: {duration_name}", normal_style))
    story.append(Paragraph(f"Дата создания: {datetime.now().strftime('%d.%m.%Y')}", normal_style))
    story.append(Spacer(1, 0.5*cm))

    if plan_data.get('weekly_volume') or plan_data.get('key_workouts'):
        story.append(Paragraph("Общая информация", heading_style))

        if plan_data.get('weekly_volume'):
            story.append(Paragraph(f"<b>Недельный объем:</b> {plan_data['weekly_volume']}", normal_style))
            story.append(Spacer(1, 0.2*cm))

        if plan_data.get('key_workouts'):
            key_workouts = ", ".join(plan_data['key_workouts'][:5])
            story.append(Paragraph(f"<b>Ключевые тренировки:</b> {key_workouts}", normal_style))
            story.append(Spacer(1, 0.2*cm))

        story.append(Spacer(1, 0.5*cm))

    if plan_data.get('plan'):
        story.append(Paragraph("План тренировок", heading_style))
        story.append(Spacer(1, 0.3*cm))

        for i, workout in enumerate(plan_data['plan'], 1):
            story.append(Paragraph(f"<b>{i}. {workout.get('day', 'День ' + str(i))}</b>", bold_style))
            story.append(Spacer(1, 0.1*cm))

            workout_data = [
                ['Тип тренировки:', workout.get('workout_type', 'N/A')],
                ['Объем:', workout.get('volume', 'N/A')],
                ['Интенсивность:', workout.get('intensity', 'N/A')],
            ]

            if workout.get('target_pace'):
                workout_data.append(['Целевой темп:', workout.get('target_pace')])

            if workout.get('description'):
                workout_data.append(['Описание:', workout.get('description')])

            if workout.get('purpose'):
                workout_data.append(['Цель:', workout.get('purpose')])

            workout_table = Table(workout_data, colWidths=[4*cm, 12*cm])
            workout_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))

            story.append(workout_table)
            story.append(Spacer(1, 0.5*cm))

    if plan_data.get('explanation'):
        story.append(Paragraph("Важные рекомендации", heading_style))
        explanation_text = plan_data['explanation'].replace('\n', '<br/>')
        story.append(Paragraph(explanation_text, normal_style))
        story.append(Spacer(1, 0.3*cm))

    if plan_data.get('recovery_tips'):
        story.append(Paragraph("Восстановление", heading_style))
        recovery_text = plan_data['recovery_tips'].replace('\n', '<br/>')
        story.append(Paragraph(recovery_text, normal_style))
        story.append(Spacer(1, 0.3*cm))

    story.append(Spacer(1, 1*cm))
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=normal_style,
        fontSize=8,
        textColor=colors.HexColor('#666666'),
        leading=10
    )
    story.append(Paragraph(
        "<i>⚠️ Рекомендации носят исключительно информационный характер и не заменяют "
        "консультацию с врачом или профессиональным тренером. Перед началом тренировок "
        "проконсультируйтесь со специалистами.</i>",
        disclaimer_style
    ))

    doc.build(story)
    buffer.seek(0)

    return buffer
