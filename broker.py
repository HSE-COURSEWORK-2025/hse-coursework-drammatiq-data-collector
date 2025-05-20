# broker.py
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware.asyncio import AsyncIO
from settings import settings

# Настраиваем Redis как брокер
print(f"connecting to redis redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0")
# broker = RedisBroker(url=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0")
broker = RedisBroker(url=f"redis://redis:6379/0")
broker.add_middleware(AsyncIO())
dramatiq.set_broker(broker)
