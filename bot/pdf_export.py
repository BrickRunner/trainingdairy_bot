"""
Модуль для экспорта тренировок в PDF
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from io import BytesIO
import logging
import os
import sys

from .pdf_graphs import create_pdf_graphs, generate_weekly_stats
from database.queries import get_user_settings
from utils.unit_converter import format_distance, format_pace, format_swimming_distance

logger = logging.getLogger(__name__)

# Определяем пути к шрифтам в зависимости от ОС
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
        # Windows
        possible_paths = [
            r'C:\Windows\Fonts\DejaVuSans.ttf',
            r'C:\Windows\Fonts\dejavu-sans\DejaVuSans.ttf',
            # Добавляем путь к пользовательским шрифтам
            os.path.expanduser(r'~\AppData\Local\Microsoft\Windows\Fonts\DejaVuSans.ttf'),
        ]
    else:
        # Linux/Mac
        possible_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/dejavu/DejaVuSans.ttf',
            '/System/Library/Fonts/Supplemental/DejaVuSans.ttf',
        ]
    
    # Проверяем какой путь существует
    for path in possible_paths:
        if os.path.exists(path):
            # Получаем директорию со шрифтами
            font_dir = os.path.dirname(path)
            bold_path = os.path.join(font_dir, 'DejaVuSans-Bold.ttf')
            logger.info(f"Используем системные шрифты из: {path}")
            return {
                'regular': path,
                'bold': bold_path if os.path.exists(bold_path) else path
            }
    
    return None

# Пытаемся зарегистрировать русский шрифт DejaVu
font_paths = get_font_paths()
FONT_NAME = 'DejaVuSans'
FONT_NAME_BOLD = 'DejaVuSans-Bold'

if font_paths:
    try:
        pdfmetrics.registerFont(TTFont(FONT_NAME, font_paths['regular']))
        if os.path.exists(font_paths['bold']):
            pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, font_paths['bold']))
        else:
            FONT_NAME_BOLD = FONT_NAME  # Используем обычный вместо жирного
        logger.info(f"✅ Шрифты DejaVu успешно загружены")
    except Exception as e:
        logger.warning(f"❌ Не удалось загрузить шрифты DejaVu: {e}")
        # Используем стандартные шрифты (без кириллицы)
        FONT_NAME = 'Helvetica'
        FONT_NAME_BOLD = 'Helvetica-Bold'
else:
    logger.warning(
        "❌ Шрифты DejaVu не найдены!\n"
        "   Для поддержки русского языка в PDF:\n"
        "   1. Создайте папку 'fonts' в корне проекта\n"
        "   2. Скачайте шрифты DejaVu с https://dejavu-fonts.github.io/\n"
        "   3. Скопируйте DejaVuSans.ttf и DejaVuSans-Bold.ttf в папку 'fonts'\n"
        "   Подробнее: см. УСТАНОВКА_ШРИФТОВ.txt"
    )
    FONT_NAME = 'Helvetica'
    FONT_NAME_BOLD = 'Helvetica-Bold'


async def create_training_pdf(trainings: list, period_text: str, stats: dict, user_id: int) -> BytesIO:
    """
    Создает PDF документ с детальной информацией о тренировках
    
    Args:
        trainings: Список тренировок из БД
        period_text: Текстовое описание периода (например, "01.04.2025 - 01.10.2025")
        stats: Словарь со статистикой
        user_id: ID пользователя для получения настроек единиц измерения
        
    Returns:
        BytesIO объект с PDF документом
    """
    # Получаем настройки пользователя для единиц измерения
    user_settings = await get_user_settings(user_id)
    distance_unit = user_settings.get('distance_unit', 'км') if user_settings else 'км'
    
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
    
    # Создаем кастомные стили с поддержкой русского языка
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
    story.append(Paragraph("Дневник тренировок", title_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"Период: {period_text}", heading_style))
    story.append(Spacer(1, 1*cm))
    
    # Общая статистика на титульной
    stats_data = [
        ["Всего тренировок:", f"{stats['total_count']}"],
        ["Общий километраж:", format_distance(stats['total_distance'], distance_unit)],
        ["Средняя усталость:", f"{stats['avg_fatigue']}/10" if stats['avg_fatigue'] > 0 else "Не указана"]
    ]
    
    stats_table = Table(stats_data, colWidths=[8*cm, 6*cm])
    stats_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('FONTNAME', (1, 0), (1, -1), FONT_NAME_BOLD),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(stats_table)
    
    # Типы тренировок
    if stats.get('types_count'):
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph("Распределение по типам:", heading_style))
        
        types_data = []
        for t_type, count in stats['types_count'].items():
            percentage = (count / stats['total_count']) * 100
            types_data.append([t_type.capitalize(), f"{count} ({percentage:.1f}%)"])
        
        types_table = Table(types_data, colWidths=[8*cm, 6*cm])
        types_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTNAME', (1, 0), (1, -1), FONT_NAME_BOLD),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(types_table)
    
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph(f"Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}", small_style))
    
    story.append(PageBreak())
    
    # === ГРАФИКИ ===
    try:
        # Получаем даты из period_text или используем первую и последнюю тренировку
        start_date = trainings[0]['date'] if trainings else None
        end_date = trainings[-1]['date'] if trainings else None
        
        if start_date and end_date:
            graphs_buffer = create_pdf_graphs(trainings, start_date, end_date)
            
            # Добавляем графики как изображение (3 графика в ряд)
            img = Image(graphs_buffer, width=17*cm, height=5.7*cm)
            story.append(Paragraph("Графики и анализ", heading_style))
            story.append(Spacer(1, 0.5*cm))
            story.append(img)
            story.append(PageBreak())
    except Exception as e:
        logger.error(f"Ошибка при создании графиков для PDF: {str(e)}", exc_info=True)
        # Продолжаем без графиков
    
    # === СТАТИСТИКА ПО НЕДЕЛЯМ ===
    if len(trainings) > 0:
        weekly_stats = generate_weekly_stats(trainings)
        
        if len(weekly_stats) > 0:
            story.append(Paragraph("Статистика по неделям", heading_style))
            story.append(Spacer(1, 0.5*cm))
            
            # Создаем таблицу со статистикой по неделям
            weekly_data = [["Неделя", "Тренировок", "Километраж"]]
            
            for week in weekly_stats:
                weekly_data.append([
                    week['week_label'],
                    str(week['count']),
                    format_distance(week['distance'], distance_unit)
                ])
            
            weekly_table = Table(weekly_data, colWidths=[9*cm, 4*cm, 4*cm])
            weekly_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), FONT_NAME_BOLD),  # Заголовок жирный
                ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                # Чередующиеся цвета строк
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')])
            ]))
            story.append(weekly_table)
            story.append(PageBreak())
    
    # === ДЕТАЛЬНЫЙ СПИСОК ТРЕНИРОВОК ===
    story.append(Paragraph("Детальный список тренировок", heading_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Эмодзи для типов (текстовые аналоги для PDF)
    type_markers = {
        'кросс': '[БЕГ]',
        'плавание': '[ПЛАВ]',
        'велотренировка': '[ВЕЛ]',
        'силовая': '[СИЛ]',
        'интервальная': '[ИНТ]'
    }
    
    for idx, training in enumerate(trainings, 1):
        # Заголовок тренировки
        date_str = datetime.strptime(training['date'], '%Y-%m-%d').strftime('%d.%m.%Y')
        t_type = training['type']
        marker = type_markers.get(t_type, '[ТРН]')
        
        training_title = f"{idx}. {marker} {t_type.upper()} • {date_str}"
        story.append(Paragraph(training_title, heading_style))
        
        # Основные параметры
        details = []
        
        # Время тренировки
        if training.get('time'):
            details.append(["Продолжительность:", training['time']])
        
        # Специфичные параметры в зависимости от типа
        if t_type == 'интервальная':
            if training.get('calculated_volume'):
                details.append(["Объем:", format_distance(training['calculated_volume'], distance_unit)])
            if training.get('intervals'):
                # Для интервальной показываем средний темп отрезков
                from utils.interval_calculator import calculate_average_interval_pace
                avg_pace = calculate_average_interval_pace(training['intervals'])
                if avg_pace:
                    details.append(["Средний темп отрезков:", avg_pace])
        
        elif t_type == 'силовая':
            # Для силовой ничего дополнительно не добавляем в основную таблицу
            pass
        
        else:
            # Для кросса, плавания, велотренировки
            if training.get('distance'):
                if t_type == 'плавание':
                    details.append(["Дистанция:", format_swimming_distance(training['distance'], distance_unit)])
                else:
                    details.append(["Дистанция:", format_distance(training['distance'], distance_unit)])
            
            if training.get('avg_pace'):
                pace_unit = training.get('pace_unit', '')
                if t_type == 'велотренировка':
                    details.append(["Средняя скорость:", f"{training['avg_pace']} {pace_unit}"])
                else:
                    details.append(["Средний темп:", f"{training['avg_pace']} {pace_unit}"])
        
        # Пульс (для всех типов)
        if training.get('avg_pulse'):
            details.append(["Средний пульс:", f"{training['avg_pulse']} уд/мин"])
        if training.get('max_pulse'):
            details.append(["Макс. пульс:", f"{training['max_pulse']} уд/мин"])
        
        # Усталость
        if training.get('fatigue_level'):
            details.append(["Усталость:", f"{training['fatigue_level']}/10"])
        
        # Создаем таблицу с деталями
        if details:
            details_table = Table(details, colWidths=[6*cm, 11*cm])
            details_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (1, 0), (1, -1), FONT_NAME_BOLD),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(details_table)
        
        # Интервалы (для интервальной тренировки)
        if t_type == 'интервальная' and training.get('intervals'):
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph("Описание тренировки:", normal_style))
            intervals_text = training['intervals'].replace('\n', '<br/>')
            story.append(Paragraph(intervals_text, small_style))
        
        # Упражнения (для силовой)
        if t_type == 'силовая' and training.get('exercises'):
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph("Упражнения:", normal_style))
            exercises_text = training['exercises'].replace('\n', '<br/>')
            story.append(Paragraph(exercises_text, small_style))
        
        # Комментарий
        if training.get('comment'):
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph("Комментарий:", normal_style))
            comment_text = training['comment'].replace('\n', '<br/>')
            story.append(Paragraph(f"<i>{comment_text}</i>", small_style))
        
        story.append(Spacer(1, 0.8*cm))
        
        # Разделитель между тренировками
        if idx < len(trainings):
            story.append(Paragraph("─" * 80, small_style))
            story.append(Spacer(1, 0.5*cm))
    
    # Строим PDF
    doc.build(story)
    buffer.seek(0)
    
    logger.info(f"PDF создан успешно: {len(trainings)} тренировок, период: {period_text}")
    return buffer