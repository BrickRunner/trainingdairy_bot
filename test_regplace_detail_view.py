"""
Тест отображения детальной информации для соревнований reg.place
"""
import asyncio
import logging
from competitions.regplace_parser import fetch_competitions

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_detail_view():
    """Проверяем что соревнования reg.place корректно отображаются в детальном виде"""

    print("=" * 80)
    print("ТЕСТ ДЕТАЛЬНОГО ОТОБРАЖЕНИЯ СОРЕВНОВАНИЙ REG.PLACE")
    print("=" * 80)

    # Получаем несколько соревнований
    comps = await fetch_competitions(
        city=None,
        sport=None,
        limit=5,
        period_months=12
    )

    if not comps:
        print("❌ Не удалось получить соревнования от reg.place")
        return

    print(f"\n✓ Получено {len(comps)} соревнований")
    print("-" * 80)

    for i, comp in enumerate(comps, 1):
        print(f"\n{i}. {comp.get('title', 'Без названия')}")
        print(f"   ID: {comp.get('id')}")
        print(f"   URL: {comp.get('url')}")
        print(f"   Service: {comp.get('service')}")
        print(f"   City: {comp.get('city')}")
        print(f"   Place: {comp.get('place')}")
        print(f"   Sport code: {comp.get('sport_code')}")
        print(f"   Begin date: {comp.get('begin_date')}")
        print(f"   End date: {comp.get('end_date')}")
        print(f"   Date: {comp.get('date')}")

        # Проверяем дистанции
        distances = comp.get('distances', [])
        print(f"   Количество дистанций: {len(distances)}")

        if distances:
            print("   Дистанции:")
            for j, dist in enumerate(distances[:5], 1):
                dist_km = dist.get('distance', 0)
                dist_name = dist.get('name', 'Без названия')
                print(f"     {j}. {dist_name} ({dist_km} км)")
        else:
            print("   ⚠️  Нет дистанций")

        # Проверяем обязательные поля для детального отображения
        required_fields = ['id', 'title', 'service', 'place', 'begin_date', 'end_date', 'sport_code']
        missing_fields = [field for field in required_fields if not comp.get(field)]

        if missing_fields:
            print(f"   ❌ ОШИБКА: Отсутствуют обязательные поля: {missing_fields}")
        else:
            print(f"   ✓ Все обязательные поля присутствуют")

    print("\n" + "=" * 80)
    print("ТЕСТ ЗАВЕРШЕН")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_detail_view())
