import redis.asyncio as redis
r = redis.Redis()
await r.ping()