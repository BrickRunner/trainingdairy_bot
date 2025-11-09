"""
Comprehensive verification that target pace feature works correctly
Run this after restarting the bot
"""
import asyncio
from competitions.competitions_queries import get_user_competitions
from utils.time_formatter import calculate_pace_with_unit

async def verify():
    print("="*60)
    print("VERIFYING TARGET PACE FEATURE")
    print("="*60)

    user_id = 1611441720  # Real test user

    print("\n1. Checking database retrieval...")
    comps = await get_user_competitions(user_id)
    print(f"   Found {len(comps)} competitions for user {user_id}")

    # Count how many have target times
    with_target = [c for c in comps if c.get('target_time') and c.get('target_time') != 'None']
    print(f"   {len(with_target)} competitions have target times set")

    if not with_target:
        print("\n   WARNING: No competitions with target_time found!")
        print("   Please register for a competition with a target time first")
        return

    print(f"\n2. Testing pace calculation for competitions with target times...")

    for comp in with_target[:5]:  # Test first 5
        comp_id = comp['id']
        distance = comp.get('distance')
        target_time = comp.get('target_time')

        print(f"\n   Competition ID: {comp_id}")
        print(f"     Distance: {distance} km")
        print(f"     Target Time: {target_time}")

        # Test pace calculation
        pace = await calculate_pace_with_unit(target_time, distance, user_id)

        if pace:
            print(f"     Calculated Pace: {pace}")
            print(f"     Status: SUCCESS - Pace would be displayed as:")
            print(f"             'Целевой темп: {pace}'")
        else:
            print(f"     Status: FAILED - Pace calculation returned None")

    print("\n" + "="*60)
    print("VERIFICATION COMPLETE")
    print("="*60)

    print("\nNEXT STEPS:")
    print("1. Make sure you RESTART the bot (stop and start bot.py)")
    print("2. Open Telegram and go to 'Мои соревнования'")
    print("3. Click on a competition that has a target time set")
    print("4. You should now see 'Целевой темп: X:XX/км' in the details")

    print("\nCompetitions with target times you can test:")
    for comp in with_target[:3]:
        print(f"  - Competition ID {comp['id']}: {comp.get('distance')} km, target {comp.get('target_time')}")

if __name__ == "__main__":
    asyncio.run(verify())
