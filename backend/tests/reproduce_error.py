import httpx
import asyncio
import json

async def test_search():
    url = "http://localhost:8000/api/search"
    payload = {
        "city": "Karachi",
        "business_type": "restaurants",
        "count": 1
    }
    
    print(f"Calling {url}...")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            print(f"Status Code: {response.status_code}")
            print("Response Body:")
            print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_search())
