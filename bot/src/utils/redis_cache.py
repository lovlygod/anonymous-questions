import redis
import json
import os
from typing import Optional, Any


class RedisCache:
    def __init__(self):
        # Используем переменную окружения для подключения к Redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        
    async def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None
    
    async def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Установить значение в кэш с временем жизни (в секундах)"""
        try:
            self.redis_client.setex(key, expire, json.dumps(value))
            return True
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Удалить значение из кэша"""
        try:
            self.redis_client.delete(key)
            return True
        except Exception:
            return False
    
    async def exists(self, key: str) -> bool:
        """Проверить, существует ли ключ в кэше"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception:
            return False