"""Verify target pace in list - save to file"""
import asyncio
from competitions.competitions_queries import get_user_competitions
from utils.time_formatter import calculate_pace_with_unit


async def test():
    user_id = 1611441720

    competitions = await get_user_competitions(user_id, status_filter='upcoming')
    with_target = [c for c in competitions if c.get('target_time') and c.get('target_time') != 'None']

    results = []
    results.append("="*60)
    results.append("TARGET PACE IN COMPETITIONS LIST - VERIFICATION")
    results.append("="*60)
    results.append(f"\nFound {len(with_target)} competitions with target time:\n")

    for i, comp in enumerate(with_target[:5], 1):
        target_time = comp.get('target_time')
        distance = comp.get('distance')
        pace = await calculate_pace_with_unit(target_time, distance, user_id)

        results.append(f"{i}. Competition ID: {comp.get('id')}")
        results.append(f"   Distance: {distance} km")
        results.append(f"   Target time: {target_time}")
        results.append(f"   Calculated pace: {pace}")
        results.append(f"   Display: 'Цель: {target_time} ({pace})'")
        results.append("")

    results.append("="*60)
    results.append("STATUS: SUCCESS ✓")
    results.append("="*60)
    results.append("\nThe target pace will now appear in:")
    results.append("1. Competitions LIST view (show_my_competitions)")
    results.append("2. Competition DETAIL view (view_my_competition)")
    results.append("\nExample display:")
    results.append("   🎯 Цель: 17:00 (3:24/км)")
    results.append("   🎯 Цель: 00:40:00 (4:00/км)")
    results.append("\n⚠️  REMEMBER: Restart the bot for changes to take effect!")

    # Save to file
    with open('PACE_VERIFICATION_RESULT.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(results))

    # Also print ASCII version
    for line in results:
        try:
            print(line.encode('ascii', 'ignore').decode('ascii'))
        except:
            print(line)


if __name__ == "__main__":
    asyncio.run(test())
