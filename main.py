# consumer.py
import asyncio
import json
from aiokafka import AIOKafkaConsumer
from tasks import process_data_batch


KAFKA_BOOTSTRAP = "localhost:9092"
TOPIC = "raw_data_topic"
BATCH_SIZE = 50
POLL_TIMEOUT_MS = 5000  # 5 секунд — время ожидания, чтобы "дозаполнить" батч


async def consume():
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_deserializer=lambda v: json.loads(v.decode()),
        enable_auto_commit=False,  # чтобы не коммитить сразу после каждого сообщения
    )
    await consumer.start()
    print('consuming')
    try:
        while True:
            # Забираем до BATCH_SIZE записей за один syscall
            records = await consumer.getmany(
                timeout_ms=POLL_TIMEOUT_MS,
                max_records=BATCH_SIZE,
            )

            batch = []
            for tp, msgs in records.items():
                for msg in msgs:
                    batch.append(msg)

            if not batch:
                # Если за таймаут ничего не пришло — просто продолжаем
                continue

            # Отправляем все сообщения из батча в драматик
            process_data_batch.send(batch)

            # После успешной отправки — можем закоммитить смещения
            # (чтобы при перезапуске не реобрабатывать те же сообщения)
            last_offsets = {
                tp: batch_msgs[-1].offset + 1
                for tp, batch_msgs in records.items()
                if batch_msgs
            }
            await consumer.commit(offsets=last_offsets)

    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(consume())
