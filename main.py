# consumer.py
import asyncio
import logging
import json
from aiokafka import AIOKafkaConsumer
from aiokafka.structs import TopicPartition
from tasks import process_data_batch
from settings import settings
from redisClient import redis_client_async


async def consume():
    # 1) Подключаемся к Redis
    await redis_client_async.connect()
    logging.info("Connected to Redis")

    # 2) Создаём consumer без автоподписки
    consumer = AIOKafkaConsumer(
        bootstrap_servers=f"{settings.KAFKA_HOST}:{settings.KAFKA_PORT}",
        value_deserializer=lambda v: json.loads(v.decode()),
        enable_auto_commit=False,
        group_id=settings.KAFKA_GROUP_ID,
    )
    await consumer.start()
    logging.info("Kafka consumer started (manual assign mode)")

    try:
        # 3) Узнаём все партиции топика и назначаем
        partitions = consumer.partitions_for_topic(settings.TOPIC)
        tps = [TopicPartition(settings.TOPIC, p) for p in partitions]
        consumer.assign(tps)
        logging.info(f"Assigned to partitions: {tps}")

        # 4) Для каждой партиции либо seek на сохранённый оффсет, либо на начало
        no_offset = []
        for tp in tps:
            key = f'kafka:offset:{tp.topic}:{tp.partition}'
            offset_str = await redis_client_async.get(key)
            if offset_str is not None:
                off = int(offset_str)
                consumer.seek(tp, off)
                logging.info(f"[Startup] Seek {tp.topic}/{tp.partition} → offset {off}")
            else:
                no_offset.append(tp)

        # Если есть партиции без оффсета, перематываем их на начало
        if no_offset:
            # seek_to_beginning — это корутина
            await consumer.seek_to_beginning(*no_offset)
            for tp in no_offset:
                logging.info(f"[Startup] No offset for {tp.topic}/{tp.partition}, seek to beginning")

        # 5) Основной цикл
        while True:
            records = await consumer.getmany(
                timeout_ms=settings.POLL_TIMEOUT_MS,
                max_records=settings.BATCH_SIZE,
            )

            batch = []
            for tp, msgs in records.items():
                batch.extend(msgs)

            if not batch:
                continue

            # Логируем диапазоны оффсетов
            for tp, msgs in records.items():
                if msgs:
                    offs = [m.offset for m in msgs]
                    logging.info(
                        f"[Kafka] Received: topic={tp.topic}, "
                        f"part={tp.partition}, offsets={min(offs)}–{max(offs)}, count={len(offs)}"
                    )

            try:
                # Отправляем в Dramatiq
                process_data_batch.send([m.value for m in batch])

                # Коммитим в Kafka
                last_offsets = {
                    tp: msgs[-1].offset + 1
                    for tp, msgs in records.items() if msgs
                }
                await consumer.commit(offsets=last_offsets)
                logging.info(f"[Kafka] Committed: {last_offsets}")

                # И сохраняем в Redis
                for tp, off in last_offsets.items():
                    key = f'kafka:offset:{tp.topic}:{tp.partition}'
                    await redis_client_async.set(key, off)
                    logging.info(f"[Redis] Saved {key} = {off}")

            except Exception as e:
                logging.error(f"Error in processing/commit: {e}")

    finally:
        await consumer.stop()
        await redis_client_async.disconnect()
        logging.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(consume())
