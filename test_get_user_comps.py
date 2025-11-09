"""Test get_user_competitions function"""
import asyncio
from competitions.competitions_queries import get_user_competitions

async def test():
    user_id = 1611441720  # Real user ID from database
    comps = await get_user_competitions(user_id)

    print(f"Found {len(comps)} competitions for user {user_id}\n")

    for comp in comps:
        comp_id = comp['id']
        distance = comp.get('distance', 'N/A')
        target_time = comp.get('target_time', 'NOT_FOUND')

        # Print without emojis to avoid encoding issues
        print(f"Competition ID: {comp_id}, Distance: {distance}, Target Time: {target_time} (type: {type(target_time).__name__})")

        # Check all keys in the comp dict
        if comp_id == 95 or distance == 5.0:  # Looking for specific competition
            print(f"  All keys: {list(comp.keys())}")
            print()

if __name__ == "__main__":
    asyncio.run(test())
