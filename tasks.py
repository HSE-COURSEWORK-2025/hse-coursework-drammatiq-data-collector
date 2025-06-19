import asyncio
import dramatiq
import logging
from broker import broker
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select
from db.db_session import get_session
from db.schemas import RawRecords
from dateutil import parser
from dataTransformation import get_data_transformer_by_datatype


dramatiq.set_broker(broker)


@dramatiq.actor(max_retries=3, retry_when=lambda retries, exc: True)
async def process_data_batch(batch: List[dict]):
    session: Session = await get_session().__anext__()
    try:
        await asyncio.sleep(2)

        new_records = []
        for data in batch:
            raw = data.get("rawData", {})
            user = data.get("userData", {})

            data_type = data.get("dataType", "")
            email = user.get("email", "")
            raw_time = raw.get("timestamp") or raw.get("time") or ""
            value = str(raw.get("value", ""))

            data_transformer = get_data_transformer_by_datatype(data_type)

            try:
                value = data_transformer.transform(value)
            except Exception as e:
                logging.error(f"could not process this value {value}: {e}")

            if not raw_time:
                logging.info(f"Нет поля time/timestamp в записи: {data}")
                continue

            try:
                time_obj = parser.parse(raw_time)
            except Exception:
                logging.info(f"Не удалось распарсить время у записи: {data}")
                logging.info(f"time field {raw_time}")
                continue

            if isinstance(value, str) and not value.strip():
                logging.info(
                    f"Пропускаем запись с пустым или whitespace-only value: {data}"
                )
                continue

            logging.info(
                f"saving this data: \
                         data_type: {data_type} \
                         time_obj: {time_obj} \
                         email: {email} \
                         value: {value} \
                            "
            )

            exists = (
                session.execute(
                    select(RawRecords.id).where(
                        RawRecords.email == email,
                        RawRecords.data_type == data_type,
                        RawRecords.time == time_obj,
                    )
                )
                .scalars()
                .first()
            )

            if exists:
                logging.info(f"Пропускаем дубликат: {email} / {data_type} @ {raw_time}")
                continue

            new_records.append(
                RawRecords(data_type=data_type, email=email, time=time_obj, value=value)
            )

        if new_records:
            session.add_all(new_records)
            session.commit()
            logging.info(f"Сохранено {len(new_records)} новых записей в БД.")
        else:
            logging.info("Новых записей для сохранения не найдено.")

    except Exception as e:
        session.rollback()
        logging.error(f"Ошибка при сохранении пачки: {e}")
        raise
    finally:
        session.close()
