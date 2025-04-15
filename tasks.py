# broker.py
import dramatiq
from broker import broker
import time


dramatiq.set_broker(broker)


@dramatiq.actor(max_retries=3, retry_when=lambda _: True)
def process_data(data: dict):
    """
    Пример actor-а, который обрабатывает словарь.
    В случае ошибки автоматически перезапустится до 3 раз.
    """
    print(f"Start processing: {data}")
    # Какая-то "тяжёлая" работа
    time.sleep(2)
   
    print(f"Finished processing: {data}")
