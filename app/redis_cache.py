from redis.asyncio import Redis
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
from config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD


async def init_redis() -> Redis:
    redis_client=Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
    try :await redis_client.ping()
    except Exception as e:
        print(f"Redis is not connected {e}")
    return redis_client

async def close_redis(redis: Redis):
    await redis.close()
    
@asynccontextmanager
async def get_redis() -> AsyncGenerator[Redis, None]:
    """
    Dependency для FastAPI
    Возвращает AsyncGenerator[Redis, None] вместо Redis
    """
    redis = await init_redis()
    try:
        yield redis
    finally:
        await close_redis(redis)

async def redis_dependency() -> Redis:
    async with get_redis() as redis:
        return redis  # Здесь можно использовать await