import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agri_backend.settings')

# 配置 Django
import django
django.setup()


import json
from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool
from django.conf import settings

class AsyncRedisClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            pool = ConnectionPool(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=getattr(settings, 'REDIS_DB', 0),
                decode_responses=True,
                max_connections=200,
            )
            cls._instance._client = Redis(connection_pool=pool)
        return cls._instance
    
    async def hset(self, key, data, expire=None):
        result = await self._client.hset(key, mapping=data)
        if expire:
            await self._client.expire(key, expire)
        return result
    
    async def hgetall(self, key):
        return await self._client.hgetall(key)
    
    async def lpush(self, key, data, maxlen=None, expire=None):
        await self._client.lpush(key, json.dumps(data))
        if maxlen:
            await self._client.ltrim(key, 0, maxlen - 1)
        if expire:
            await self._client.expire(key, expire)
    
    async def lrange(self, key, start=0, end=-1):
        result = await self._client.lrange(key, start, end)
        return [json.loads(item) for item in result] if result else []

async_redis_client = AsyncRedisClient()