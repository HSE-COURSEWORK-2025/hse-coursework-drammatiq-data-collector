# consumer.py
import asyncio
import json
from aiokafka import AIOKafkaConsumer
from tasks import process_data_batch
from settings import settings


async def consume():
    consumer = AIOKafkaConsumer(
        settings.TOPIC,
        bootstrap_servers=f"{settings.KAFKA_HOST}:{settings.KAFKA_PORT}",
        value_deserializer=lambda v: json.loads(v.decode()),
        enable_auto_commit=False,  # чтобы не коммитить сразу после каждого сообщения
    )
    await consumer.start()
    print('consuming')
    try:
        while True:
            # Забираем до BATCH_SIZE записей за один syscall
            records = await consumer.getmany(
                timeout_ms=settings.POLL_TIMEOUT_MS,
                max_records=settings.BATCH_SIZE,
            )

            batch = []
            for tp, msgs in records.items():
                for msg in msgs:
                    batch.append(msg)

            if not batch:
                # Если за таймаут ничего не пришло — просто продолжаем
                continue

            # Отправляем все сообщения из батча в драматик
            try:
                process_data_batch.send(batch)

                # После успешной отправки — можем закоммитить смещения
                # (чтобы при перезапуске не реобрабатывать те же сообщения)
                last_offsets = {
                    tp: batch_msgs[-1].offset + 1
                    for tp, batch_msgs in records.items()
                    if batch_msgs
                }
                await consumer.commit(offsets=last_offsets)
            except Exception as e:
                print(f'error: {e}')
    
    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(consume())
