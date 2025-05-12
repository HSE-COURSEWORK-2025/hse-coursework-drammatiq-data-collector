# tasks.py
import dramatiq
from broker import broker
import time
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select
from db.db_session import get_session
from db.schemas import RawRecords

dramatiq.set_broker(broker)


@dramatiq.actor(max_retries=3, retry_when=lambda _: True)
async def process_data_batch(batch: List[dict]):
    """
    Actor для пакетной обработки и сохранения RawRecords в БД.
    В случае ошибки автоматически перезапустится до 3 раз.
    Принимает список словарей, проверяет уникальность по (email, data_type, time_str)
    и сохраняет все новые записи одной транзакцией.
    """
    session: Session = await get_session().__anext__()
    try:
        # Имитация долгой обработки (можно убрать или заменить на более подходящую логику)
        time.sleep(2)

        new_records = []
        for data in batch:
            data_type = data.get("data_type", "")
            email = data.get("email", "")
            time_str = data.get("time", "")
            value = data.get("value", "")

            # Парсим время
            try:
                time_obj = datetime.fromisoformat(time_str)
            except Exception:
                print(f"Не удалось распарсить время '{time_str}', пропускаем запись.")
                continue

            # Проверка на существование записи
            exists = session.execute(
                select(RawRecords.id).where(
                    RawRecords.email == email,
                    RawRecords.data_type == data_type,
                    RawRecords.time == time_obj,
                )
            ).scalar_one_or_none()

            if exists:
                print(f"Пропускаем дубликат: {email} / {data_type} @ {time_str}")
                continue

            # Если запись новая — создаём объект
            record = RawRecords(
                data_type=data_type, email=email, time=time_obj, value=value
            )
            new_records.append(record)

        if new_records:
            # Сохраняем все новые записи одной коммитом
            session.add_all(new_records)
            session.commit()
            print(f"Сохранено {len(new_records)} новых записей в БД.")
        else:
            print("Новых записей для сохранения не найдено.")

    except Exception as e:
        session.rollback()
        print(f"Ошибка при сохранении пачки: {e}")
        # Пробрасываем, чтобы Dramatiq сделал retry
        raise
    finally:
        session.close()
