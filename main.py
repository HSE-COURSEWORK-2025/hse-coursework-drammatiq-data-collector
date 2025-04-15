# consumer.py
import asyncio
import json
from aiokafka import AIOKafkaConsumer
from tasks import process_data

KAFKA_BOOTSTRAP = "localhost:9092"
TOPIC = "your_topic"


async def consume():
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_deserializer=lambda v: json.loads(v.decode()),
    )
    # Запускаем consumer
    await consumer.start()
    try:
        async for msg in consumer:
            # msg.value — распарсенный JSON
            print(f"Received from Kafka: {msg.value}")
            # Отправляем в Dramatiq
            process_data.send(msg.value)
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(consume())
