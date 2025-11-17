"""
Модуль для экспорта данных здоровья в PDF
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
import re

from .health_queries import get_health_metrics_range, get_latest_health_metrics
from .health_graphs import generate_health_graphs
from .sleep_analysis import SleepAnalyzer, format_sleep_analysis_message
from utils.date_formatter import DateFormatter, get_user_date_format
from database.queries import get_user_settings

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
            logger.info(f"Используем системные шрифты из: {path}")
            return {
                'regular': path,
                'bold': bold_path if os.path.exists(bold_path) else path
            }

    return None

# Регистрируем шрифты
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
        logger.info(f"✅ Шрифты DejaVu успешно загружены для health PDF")
    except Exception as e:
        logger.warning(f"❌ Не удалось загрузить шрифты DejaVu: {e}")
        FONT_NAME = 'Helvetica'
        FONT_NAME_BOLD = 'Helvetica-Bold'
else:
    logger.warning("❌ Шрифты DejaVu не найдены для health PDF!")
    FONT_NAME = 'Helvetica'
    FONT_NAME_BOLD = 'Helvetica-Bold'


def format_sleep_duration(duration: float) -> str:
    """Форматирует длительность сна в читаемый вид"""
    total_minutes = round(duration * 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if minutes > 0:
        return f"{hours} ч {minutes} мин"
    else:
        return f"{hours} ч"


async def create_health_pdf(user_id: int, period_param: str) -> BytesIO:
    """
    Создает PDF документ с детальной информацией о здоровье

    Args:
        user_id: ID пользователя
        period_param: Параметр периода ("week", "month", "180", "365", "custom_YYYYMMDD_YYYYMMDD")

    Returns:
        BytesIO объект с PDF документом
    """
    # Получаем формат даты пользователя
    user_format = await get_user_date_format(user_id)

    # Получаем метрики за период
    if period_param == "week":
        from .health_queries import get_current_week_metrics
        metrics = await get_current_week_metrics(user_id)
        period_name = "Эта неделя"
    elif period_param == "month":
        from .health_queries import get_current_month_metrics
        metrics = await get_current_month_metrics(user_id)
        period_name = "Этот месяц"
    elif period_param.startswith("custom_"):
        # Обработка произвольного периода
        # Формат: custom_YYYYMMDD_YYYYMMDD
        parts = period_param.split("_")
        if len(parts) == 3:
            start_date_str = parts[1]
            end_date_str = parts[2]
            start_date = date(int(start_date_str[:4]), int(start_date_str[4:6]), int(start_date_str[6:8]))
            end_date = date(int(end_date_str[:4]), int(end_date_str[4:6]), int(end_date_str[6:8]))

            metrics = await get_health_metrics_range(user_id, start_date, end_date)
            period_name = DateFormatter.format_date_range(start_date, end_date, user_format)
        else:
            raise ValueError("Неверный формат произвольного периода")
    else:
        days = int(period_param)
        metrics = await get_latest_health_metrics(user_id, days)
        if days == 180:
            period_name = "Полгода"
        elif days == 365:
            period_name = "Год"
        else:
            period_name = f"Последние {days} дней"

    if not metrics:
        raise ValueError("Нет данных за выбранный период")

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

    small_style = ParagraphStyle(
        'CustomSmall',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=9,
        textColor=colors.grey
    )

    # Элементы документа
    story = []

    # === ТИТУЛЬНАЯ СТРАНИЦА ===
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph("Дневник здоровья и метрик", title_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"Период: {period_name}", heading_style))
    story.append(Spacer(1, 0.5*cm))

    # Форматируем даты периода
    if metrics:
        first_date = datetime.strptime(metrics[0]['date'], '%Y-%m-%d').date()
        last_date = datetime.strptime(metrics[-1]['date'], '%Y-%m-%d').date()
        formatted_first = DateFormatter.format_date(first_date, user_format)
        formatted_last = DateFormatter.format_date(last_date, user_format)
        story.append(Paragraph(f"{formatted_first} - {formatted_last}", normal_style))

    story.append(Spacer(1, 1*cm))

    # === ОБЩАЯ СТАТИСТИКА ===
    pulse_values = [m['morning_pulse'] for m in metrics if m.get('morning_pulse')]
    weight_values = [m['weight'] for m in metrics if m.get('weight')]
    sleep_values = [m['sleep_duration'] for m in metrics if m.get('sleep_duration')]

    stats_data = [
        ["Записей данных:", str(len(metrics))],
    ]

    if pulse_values:
        avg_pulse = sum(pulse_values) / len(pulse_values)
        stats_data.append(["Средний утренний пульс:", f"{avg_pulse:.0f} уд/мин"])
        stats_data.append(["Диапазон пульса:", f"{min(pulse_values)} - {max(pulse_values)} уд/мин"])

    if weight_values:
        current_weight = weight_values[-1]
        first_weight = weight_values[0]
        weight_change = current_weight - first_weight
        stats_data.append(["Текущий вес:", f"{current_weight:.1f} кг"])
        if abs(weight_change) > 0.1:
            stats_data.append(["Изменение веса:", f"{weight_change:+.1f} кг"])

    if sleep_values:
        avg_sleep = sum(sleep_values) / len(sleep_values)
        stats_data.append(["Средняя длительность сна:", format_sleep_duration(avg_sleep)])
        stats_data.append(["Диапазон сна:", f"{format_sleep_duration(min(sleep_values))} - {format_sleep_duration(max(sleep_values))}"])

    stats_table = Table(stats_data, colWidths=[10*cm, 7*cm])
    stats_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('FONTNAME', (1, 0), (1, -1), FONT_NAME_BOLD),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(stats_table)

    story.append(Spacer(1, 2*cm))
    # Форматируем дату генерации согласно настройкам пользователя
    generated_date = DateFormatter.format_date(datetime.now().date(), user_format)
    generated_time = datetime.now().strftime('%H:%M')
    story.append(Paragraph(f"Сгенерировано: {generated_date} {generated_time}", small_style))

    story.append(PageBreak())

    # === ГРАФИКИ ===
    try:
        story.append(Paragraph("Графики метрик здоровья", heading_style))
        story.append(Spacer(1, 0.5*cm))

        # Получаем целевой вес из настроек пользователя
        settings = await get_user_settings(user_id)
        weight_goal = settings.get('weight_goal') if settings else None

        # Генерируем график с учётом формата даты
        graph_buffer = await generate_health_graphs(metrics, period_name, weight_goal, user_format)

        # Добавляем график как изображение
        img = Image(graph_buffer, width=17*cm, height=14*cm)
        story.append(img)
        story.append(PageBreak())
    except Exception as e:
        logger.error(f"Ошибка при создании графиков для PDF: {str(e)}", exc_info=True)

    # === ДЕТАЛЬНАЯ ТАБЛИЦА ДАННЫХ ===
    story.append(Paragraph("Детальные данные", heading_style))
    story.append(Spacer(1, 0.5*cm))

    table_data = [["Дата", "Пульс", "Вес", "Сон", "Качество сна"]]

    for metric in reversed(metrics):  # Сначала новые
        metric_date_obj = datetime.strptime(metric['date'], '%Y-%m-%d').date()
        metric_date = DateFormatter.format_date(metric_date_obj, user_format)
        pulse = f"{metric['morning_pulse']}" if metric.get('morning_pulse') else "-"
        weight = f"{metric['weight']:.1f} кг" if metric.get('weight') else "-"
        sleep = format_sleep_duration(metric['sleep_duration']) if metric.get('sleep_duration') else "-"
        quality = f"{metric['sleep_quality']}/5" if metric.get('sleep_quality') else "-"

        table_data.append([metric_date, pulse, weight, sleep, quality])

    detail_table = Table(table_data, colWidths=[3*cm, 2.5*cm, 3*cm, 3.5*cm, 3.5*cm])
    detail_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), FONT_NAME_BOLD),
        ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(detail_table)

    # === АНАЛИЗ СНА (если есть данные) ===
    if sleep_values and len(sleep_values) >= 3:
        story.append(PageBreak())
        story.append(Paragraph("Анализ сна", heading_style))
        story.append(Spacer(1, 0.5*cm))

        # Выполняем анализ сна
        analyzer = SleepAnalyzer(metrics)
        analysis = analyzer.get_full_analysis()

        if analysis['status'] == 'ok':
            # Общая оценка
            score = analysis['overall_score']
            story.append(Paragraph(f"Общая оценка: {score['score']}/100 ({score['category']})", normal_style))
            story.append(Spacer(1, 0.3*cm))

            # Длительность
            duration = analysis['duration_analysis']
            duration_data = [
                ["Среднее:", f"{duration['average']} ч"],
                ["Диапазон:", f"{duration['min']} - {duration['max']} ч"],
                ["Статус:", duration['status']],
                ["Достаточный сон:", f"{duration['sufficient_nights_pct']}% ночей"],
            ]

            if duration['sleep_debt_hours'] > 0:
                duration_data.append(["Дефицит сна:", f"{duration['sleep_debt_hours']} ч"])

            duration_table = Table(duration_data, colWidths=[10*cm, 7*cm])
            duration_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('FONTNAME', (1, 0), (1, -1), FONT_NAME_BOLD),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(duration_table)

            # Стабильность
            story.append(Spacer(1, 0.5*cm))
            consistency = analysis['consistency_analysis']
            story.append(Paragraph(f"Стабильность режима: {consistency['status']} (±{consistency['std_dev']} ч)", normal_style))

            # Рекомендации
            story.append(Spacer(1, 0.5*cm))
            story.append(Paragraph("Рекомендации:", heading_style))

            for rec in analysis['recommendations']:
                # Убираем HTML теги для PDF
                clean_rec = rec.replace('<b>', '').replace('</b>', '')
                # Убираем emoji (они отображаются как пустые квадраты в DejaVu Sans)
                clean_rec = re.sub(r'[^\w\s\-.,;:!?()/\u0400-\u04FF%+]', '', clean_rec)
                story.append(Paragraph(f"• {clean_rec}", normal_style))

    # Генерируем PDF
    doc.build(story)
    buffer.seek(0)

    return buffer
