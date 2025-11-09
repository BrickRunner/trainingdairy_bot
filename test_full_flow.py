"""Test the full flow from DB to display"""
import asyncio
from competitions.competitions_queries import get_user_competitions
from utils.time_formatter import calculate_pace_with_unit

async def test():
    user_id = 1611441720

    comps = await get_user_competitions(user_id)

    # Find competitions with target_time
    for comp in comps:
        target_time = comp.get('target_time')
        distance = comp.get('distance')

        if target_time and target_time not in ['None', '']:
            print(f"\nCompetition ID: {comp['id']}")
            print(f"  Distance: {distance} km")
            print(f"  Target Time: {target_time}")

            # Test the calculation
            pace = await calculate_pace_with_unit(target_time, distance, user_id)
            print(f"  Calculated Pace: {pace}")

            # Simulate what the handler does
            if target_time is None or target_time == 'None' or target_time == '':
                target_pace_str = ''
                print(f"  Would display: NO PACE (target_time check failed)")
            else:
                target_pace_str = f"Target Pace: {pace}\n" if pace else ''
                print(f"  Would display: '{target_pace_str}'")

if __name__ == "__main__":
    asyncio.run(test())
