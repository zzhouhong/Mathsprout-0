"""Quick test: find correct DeepSeek API base URL."""
import asyncio
from openai import AsyncOpenAI
from app.core.config import get_settings

settings = get_settings()
api_key = settings.ANTHROPIC_API_KEY

async def test(url: str, label: str):
    client = AsyncOpenAI(api_key=api_key, base_url=url)
    try:
        r = await client.models.list()
        models = [m.id for m in r.data]
        print(f"{label}: OK -> models: {models}")
    except Exception as e:
        print(f"{label}: FAILED -> {e}")

async def main():
    await test("https://api.deepseek.com", "Without /v1")
    await test("https://api.deepseek.com/v1", "With /v1")

asyncio.run(main())
