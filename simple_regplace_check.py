import asyncio
import aiohttp
import json

async def check():
    url = "https://api.reg.place/v1/events"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                status = response.status

                with open('regplace_result.txt', 'w', encoding='utf-8') as f:
                    f.write(f"Status: {status}\n\n")

                    if status == 200:
                        data = await response.json()
                        f.write(f"Type: {type(data).__name__}\n")
                        f.write(f"Length: {len(data) if isinstance(data, (list, dict)) else 'N/A'}\n\n")

                        if isinstance(data, list) and data:
                            f.write("First item:\n")
                            f.write(json.dumps(data[0], indent=2, ensure_ascii=False))
                        elif isinstance(data, dict):
                            f.write("Keys:\n")
                            f.write(str(list(data.keys())))
                            f.write("\n\nFull data:\n")
                            f.write(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
                    else:
                        text = await response.text()
                        f.write(f"Error: {text[:500]}")

                return "Done"
    except Exception as e:
        with open('regplace_result.txt', 'w', encoding='utf-8') as f:
            f.write(f"Exception: {str(e)}")
        return f"Error: {e}"

result = asyncio.run(check())
print(result)
