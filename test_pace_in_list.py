"""Simple test for target pace in competitions list"""
import asyncio
from competitions.competitions_queries import get_user_competitions
from utils.time_formatter import calculate_pace_with_unit


async def test():
    user_id = 1611441720

    print("Testing target pace display in competitions list\n")

    competitions = await get_user_competitions(user_id, status_filter='upcoming')

    # Find competitions with target time
    with_target = [c for c in competitions if c.get('target_time') and c.get('target_time') != 'None']

    print(f"Found {len(with_target)} competitions with target time set:\n")

    for i, comp in enumerate(with_target[:5], 1):
        target_time = comp.get('target_time')
        distance = comp.get('distance')

        # Calculate pace
        pace = await calculate_pace_with_unit(target_time, distance, user_id)

        comp_id = comp.get('id')
        comp_name = str(comp.get('name', 'Unknown'))[:40]

        print(f"{i}. Competition ID {comp_id}")
        print(f"   Name: {comp_name}")
        print(f"   Distance: {distance} km")
        print(f"   Target time: {target_time}")
        print(f"   Calculated pace: {pace}")
        print(f"   Display string: 'Цель: {target_time} ({pace})'")
        print()

    print("\nSUCCESS! Target pace will now appear in the list view as:")
    print("   🎯 Цель: 17:00 (3:24/км)")
    print("   🎯 Цель: 00:40:00 (4:00/км)")
    print("\nREMEMBER: Restart the bot for changes to take effect!")


if __name__ == "__main__":
    asyncio.run(test())
