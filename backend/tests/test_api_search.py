import httpx
import asyncio

async def test_search():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/search",
            json={"city": "karachi", "business_type": "restaurants", "count": 5},
            timeout=60
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

if __name__ == "__main__":
    asyncio.run(test_search())
