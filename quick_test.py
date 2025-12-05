import asyncio
from datetime import datetime, timezone
from competitions.parser import RussiaRunningParser

async def main():
    print("Current UTC time:", datetime.now(timezone.utc))
    print("Current local time:", datetime.now())

    async with RussiaRunningParser() as parser:
        data = await parser.get_events(skip=0, take=5)
        events = data.get("list", [])
        print(f"\nFirst {len(events)} events:")
        for i, evt in enumerate(events, 1):
            print(f"{i}. {evt.get('beginDate')} - {evt.get('title')[:50]}")

asyncio.run(main())
