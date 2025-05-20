import asyncio
import dramatiq
from broker import broker
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select
from db.db_session import get_session
from db.schemas import RawRecords
from dateutil import parser


dramatiq.set_broker(broker)

@dramatiq.actor(max_retries=3, retry_when=lambda retries, exc: True)
async def process_data_batch(batch: List[dict]):
    session: Session = await get_session().__anext__()
    try:
        # имитация долгой работы не блокируя loop
        await asyncio.sleep(2)

        new_records = []
        for data in batch:
            # раскладываем вложенные словари
            raw  = data.get("rawData", {})
            user = data.get("userData", {})

            data_type = data.get("dataType", "")
            email     = user.get("email", "")
            raw_time = raw.get("timestamp") or raw.get("time") or ""
            value     = raw.get("value", "")

            if not raw_time:
                # логируем и пропускаем
                print(f"Нет поля time/timestamp в записи: {data}")
                continue

            # Парсим время
            try:
                time_obj = parser.parse(raw_time)
            except Exception:
                print(f"Не удалось распарсить время у записи: {data}")
                print(f'time field {raw_time}')
                continue

            # Проверяем дубликат
            exists = session.execute(
                select(RawRecords.id).where(
                    RawRecords.email    == email,
                    RawRecords.data_type== data_type,
                    RawRecords.time     == time_obj
                )
            ).scalar_one_or_none()

            if exists:
                print(f"Пропускаем дубликат: {email} / {data_type} @ {raw_time}")
                continue

            # Готовим новую запись
            new_records.append(RawRecords(
                data_type=data_type,
                email=email,
                time=time_obj,
                value=value
            ))

        if new_records:
            session.add_all(new_records)
            session.commit()
            print(f"Сохранено {len(new_records)} новых записей в БД.")
        else:
            print("Новых записей для сохранения не найдено.")

    except Exception as e:
        session.rollback()
        print(f"Ошибка при сохранении пачки: {e}")
        raise
    finally:
        session.close()
