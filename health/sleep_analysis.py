"""
Глубокий анализ сна (как в Polar, Garmin, Coros)
"""

from typing import List, Dict, Optional
from datetime import date, timedelta
import statistics
import logging

logger = logging.getLogger(__name__)


class SleepAnalyzer:
    """Класс для анализа данных сна"""

    RECOMMENDED_SLEEP_MIN = 7.0
    RECOMMENDED_SLEEP_MAX = 9.0
    OPTIMAL_SLEEP = 8.0

    def __init__(self, metrics: List[Dict]):
        """
        Инициализация анализатора

        Args:
            metrics: Список метрик здоровья
        """
        self.metrics = metrics
        self.sleep_data = self._extract_sleep_data()

    def _extract_sleep_data(self) -> List[Dict]:
        """Извлекает данные о сне из метрик"""
        sleep_data = []
        for metric in self.metrics:
            if metric.get('sleep_duration'):
                sleep_data.append({
                    'date': metric['date'],
                    'duration': metric['sleep_duration'],
                    'quality': metric.get('sleep_quality'),
                    'pulse': metric.get('morning_pulse'),
                    'stress': metric.get('stress_level'),
                    'energy': metric.get('energy_level')
                })
        return sleep_data

    def get_full_analysis(self) -> Dict:
        """
        Возвращает полный анализ сна

        Returns:
            Словарь с различными метриками и рекомендациями
        """
        if not self.sleep_data:
            return {
                'status': 'no_data',
                'message': 'Недостаточно данных для анализа'
            }

        analysis = {
            'status': 'ok',
            'period_days': len(self.sleep_data),
            'overall_score': self._calculate_overall_score(),
            'duration_analysis': self._analyze_duration(),
            'quality_analysis': self._analyze_quality(),
            'consistency_analysis': self._analyze_consistency(),
            'recovery_analysis': self._analyze_recovery(),
            'trends': self._analyze_trends(),
            'recommendations': self._generate_recommendations()
        }

        return analysis

    def _calculate_overall_score(self) -> Dict:
        """Рассчитывает общий балл качества сна (0-100)"""
        scores = []

        duration_score = self._score_duration()
        scores.append(duration_score)

        quality_score = self._score_quality()
        if quality_score is not None:
            scores.append(quality_score)

        consistency_score = self._score_consistency()
        scores.append(consistency_score)

        overall = sum(scores) / len(scores) if scores else 0

        if overall >= 85:
            category = 'Отличный'
            emoji = '🌟'
        elif overall >= 70:
            category = 'Хороший'
            emoji = '✅'
        elif overall >= 50:
            category = 'Удовлетворительный'
            emoji = '⚠️'
        else:
            category = 'Требует внимания'
            emoji = '❌'

        return {
            'score': round(overall, 1),
            'category': category,
            'emoji': emoji
        }

    def _score_duration(self) -> float:
        """Балл за длительность сна (0-100)"""
        durations = [s['duration'] for s in self.sleep_data]
        avg_duration = statistics.mean(durations)

        if self.RECOMMENDED_SLEEP_MIN <= avg_duration <= self.RECOMMENDED_SLEEP_MAX:
            score = 100
        elif avg_duration < self.RECOMMENDED_SLEEP_MIN:
            diff = self.RECOMMENDED_SLEEP_MIN - avg_duration
            score = max(0, 100 - (diff * 20))
        else:
            diff = avg_duration - self.RECOMMENDED_SLEEP_MAX
            score = max(60, 100 - (diff * 10))

        return score

    def _score_quality(self) -> Optional[float]:
        """Балл за качество сна (0-100)"""
        qualities = [s['quality'] for s in self.sleep_data if s.get('quality')]
        if not qualities:
            return None

        avg_quality = statistics.mean(qualities)
        score = (avg_quality / 5) * 100
        return score

    def _score_consistency(self) -> float:
        """Балл за стабильность сна (0-100)"""
        durations = [s['duration'] for s in self.sleep_data]
        if len(durations) < 2:
            return 100

        std_dev = statistics.stdev(durations)
        score = max(0, 100 - (std_dev * 50))
        return score

    def _analyze_duration(self) -> Dict:
        """Анализ длительности сна"""
        durations = [s['duration'] for s in self.sleep_data]

        avg = statistics.mean(durations)
        min_duration = min(durations)
        max_duration = max(durations)

        sufficient_nights = sum(
            1 for d in durations
            if self.RECOMMENDED_SLEEP_MIN <= d <= self.RECOMMENDED_SLEEP_MAX
        )
        sufficient_percentage = (sufficient_nights / len(durations)) * 100

        sleep_debt = (self.OPTIMAL_SLEEP - avg) * len(durations)

        status = 'В норме'
        if avg < self.RECOMMENDED_SLEEP_MIN:
            status = 'Недостаточно'
        elif avg > self.RECOMMENDED_SLEEP_MAX:
            status = 'Избыточно'

        return {
            'average': round(avg, 1),
            'min': round(min_duration, 1),
            'max': round(max_duration, 1),
            'status': status,
            'sufficient_nights_pct': round(sufficient_percentage, 1),
            'sleep_debt_hours': round(sleep_debt, 1)
        }

    def _analyze_quality(self) -> Optional[Dict]:
        """Анализ качества сна"""
        qualities = [s['quality'] for s in self.sleep_data if s.get('quality')]
        if not qualities:
            return None

        avg = statistics.mean(qualities)

        distribution = {
            'poor': sum(1 for q in qualities if q <= 2),
            'fair': sum(1 for q in qualities if q == 3),
            'good': sum(1 for q in qualities if q >= 4)
        }

        if len(qualities) >= 3:
            recent = statistics.mean(qualities[-3:])
            earlier = statistics.mean(qualities[:3])
            trend = 'Улучшается' if recent > earlier else 'Ухудшается' if recent < earlier else 'Стабильно'
        else:
            trend = 'Недостаточно данных'

        return {
            'average': round(avg, 1),
            'distribution': distribution,
            'trend': trend
        }

    def _analyze_consistency(self) -> Dict:
        """Анализ стабильности режима сна"""
        durations = [s['duration'] for s in self.sleep_data]

        if len(durations) < 2:
            return {
                'status': 'Недостаточно данных',
                'std_dev': 0
            }

        std_dev = statistics.stdev(durations)

        if std_dev < 0.5:
            status = 'Отличная'
            emoji = '🌟'
        elif std_dev < 1.0:
            status = 'Хорошая'
            emoji = '✅'
        elif std_dev < 1.5:
            status = 'Умеренная'
            emoji = '⚠️'
        else:
            status = 'Нестабильная'
            emoji = '❌'

        return {
            'status': status,
            'emoji': emoji,
            'std_dev': round(std_dev, 2)
        }

    def _analyze_recovery(self) -> Optional[Dict]:
        """Анализ восстановления (на основе пульса и энергии)"""
        recovery_data = []

        for sleep in self.sleep_data:
            if sleep.get('pulse') and sleep.get('energy'):
                recovery_data.append({
                    'duration': sleep['duration'],
                    'pulse': sleep['pulse'],
                    'energy': sleep['energy']
                })

        if not recovery_data:
            return None

        good_recovery_nights = sum(
            1 for r in recovery_data
            if r['energy'] >= 4 and r['duration'] >= self.RECOMMENDED_SLEEP_MIN
        )

        recovery_score = (good_recovery_nights / len(recovery_data)) * 100

        return {
            'recovery_score': round(recovery_score, 1),
            'good_recovery_nights': good_recovery_nights,
            'total_nights': len(recovery_data)
        }

    def _analyze_trends(self) -> Dict:
        """Анализ трендов"""
        durations = [s['duration'] for s in self.sleep_data]

        if len(durations) < 4:
            return {'status': 'Недостаточно данных'}

        mid = len(durations) // 2
        first_half_avg = statistics.mean(durations[:mid])
        second_half_avg = statistics.mean(durations[mid:])

        diff = second_half_avg - first_half_avg

        if abs(diff) < 0.3:
            trend = 'Стабильно'
            emoji = '➡️'
        elif diff > 0:
            trend = 'Увеличивается'
            emoji = '📈'
        else:
            trend = 'Уменьшается'
            emoji = '📉'

        return {
            'trend': trend,
            'emoji': emoji,
            'change_hours': round(diff, 1)
        }

    def _generate_recommendations(self) -> List[str]:
        """Генерирует рекомендации на основе анализа"""
        recommendations = []

        duration_analysis = self._analyze_duration()
        consistency = self._analyze_consistency()

        if duration_analysis['average'] < self.RECOMMENDED_SLEEP_MIN:
            deficit = self.RECOMMENDED_SLEEP_MIN - duration_analysis['average']
            recommendations.append(
                f"⏰ Увеличьте длительность сна на {deficit:.1f} ч. "
                f"Старайтесь спать не менее {self.RECOMMENDED_SLEEP_MIN} часов."
            )
        elif duration_analysis['average'] > self.RECOMMENDED_SLEEP_MAX:
            recommendations.append(
                "⚠️ Вы спите слишком много. Это может указывать на проблемы со здоровьем или качеством сна."
            )

        if consistency['std_dev'] > 1.0:
            recommendations.append(
                "🕐 Установите постоянный режим сна. "
                "Ложитесь и просыпайтесь в одно и то же время каждый день."
            )

        quality = self._analyze_quality()
        if quality and quality['average'] < 3.5:
            recommendations.append(
                "💤 Улучшите условия для сна: "
                "темная комната, комфортная температура, отсутствие шума."
            )

        recovery = self._analyze_recovery()
        if recovery and recovery['recovery_score'] < 60:
            recommendations.append(
                "🔋 Обратите внимание на факторы стресса и нагрузки. "
                "Возможно, требуется больше времени на восстановление."
            )

        if duration_analysis['sufficient_nights_pct'] < 70:
            recommendations.append(
                "📊 Только {:.0f}% ночей вы спите достаточно. "
                "Стремитесь к 90%+.".format(duration_analysis['sufficient_nights_pct'])
            )

        if not recommendations:
            recommendations.append(
                "✅ Отличная работа! Ваш режим сна в норме. Продолжайте в том же духе!"
            )

        return recommendations


def format_sleep_analysis_message(analysis: Dict) -> str:
    """
    Форматирует анализ сна в читаемое сообщение

    Args:
        analysis: Результат анализа от SleepAnalyzer

    Returns:
        Отформатированное текстовое сообщение
    """
    if analysis['status'] == 'no_data':
        return "❌ Недостаточно данных для анализа сна."

    msg_parts = []

    msg_parts.append("😴 <b>ГЛУБОКИЙ АНАЛИЗ СНА</b>")
    msg_parts.append(f"Период: {analysis['period_days']} дней\n")

    score = analysis['overall_score']
    msg_parts.append(
        f"{score['emoji']} <b>Общая оценка: {score['score']}/100</b>\n"
        f"Категория: {score['category']}\n"
    )

    duration = analysis['duration_analysis']
    msg_parts.append(
        f"⏱ <b>ДЛИТЕЛЬНОСТЬ СНА</b>\n"
        f"Среднее: {duration['average']} ч ({duration['status']})\n"
        f"Диапазон: {duration['min']} - {duration['max']} ч\n"
        f"Достаточный сон: {duration['sufficient_nights_pct']}% ночей\n"
    )

    if duration['sleep_debt_hours'] > 0:
        msg_parts.append(f"⚠️ Дефицит сна: {duration['sleep_debt_hours']} ч\n")
    elif duration['sleep_debt_hours'] < -5:
        msg_parts.append(f"⚠️ Избыток сна: {abs(duration['sleep_debt_hours'])} ч\n")

    quality = analysis.get('quality_analysis')
    if quality:
        msg_parts.append(
            f"💫 <b>КАЧЕСТВО СНА</b>\n"
            f"Средняя оценка: {quality['average']}/5\n"
            f"Плохие ночи: {quality['distribution']['poor']}\n"
            f"Нормальные: {quality['distribution']['fair']}\n"
            f"Хорошие: {quality['distribution']['good']}\n"
            f"Тренд: {quality['trend']}\n"
        )

    consistency = analysis['consistency_analysis']
    msg_parts.append(
        f"📊 <b>СТАБИЛЬНОСТЬ РЕЖИМА</b>\n"
        f"{consistency['emoji']} {consistency['status']}\n"
        f"Отклонение: ±{consistency['std_dev']} ч\n"
    )

    recovery = analysis.get('recovery_analysis')
    if recovery:
        msg_parts.append(
            f"🔋 <b>ВОССТАНОВЛЕНИЕ</b>\n"
            f"Качественное восстановление: {recovery['recovery_score']:.0f}%\n"
            f"({recovery['good_recovery_nights']}/{recovery['total_nights']} ночей)\n"
        )

    trends = analysis['trends']
    if trends.get('trend'):
        msg_parts.append(
            f"📈 <b>ТРЕНД</b>\n"
            f"{trends['emoji']} {trends['trend']}"
        )
        if trends.get('change_hours'):
            msg_parts.append(f" ({trends['change_hours']:+.1f} ч)")
        msg_parts.append("\n")

    recommendations = analysis['recommendations']
    if recommendations:
        msg_parts.append("\n<b>💡 РЕКОМЕНДАЦИИ:</b>")
        if len(recommendations) == 1:
            msg_parts.append(f"\n{recommendations[0]}")
        else:
            for i, rec in enumerate(recommendations, 1):
                msg_parts.append(f"\n{i}. {rec}")

    return "\n".join(msg_parts)
