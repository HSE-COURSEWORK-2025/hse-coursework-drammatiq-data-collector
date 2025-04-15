# broker.py
import dramatiq
from dramatiq.brokers.redis import RedisBroker

# Настраиваем Redis как брокер
broker = RedisBroker(url="redis://localhost:6379/0")
dramatiq.set_broker(broker)
