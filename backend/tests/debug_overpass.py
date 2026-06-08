import httpx
import asyncio

async def test_overpass_query(city="Karachi"):
    url = "https://overpass-api.de/api/interpreter"
    # Simplified query to check if area resolution works
    query = f"""[out:json];
area["name"="{city}"]["admin_level"~"^(4|5|6|7|8)$"]->.a;
(
  node(area.a)["place"="suburb"];
);
out tags;"""
    
    headers = {
        "User-Agent": "AI-Lead-Generator/1.0 (contact@example.com)",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(url, data={"data": query}, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Content: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(test_overpass_query())
