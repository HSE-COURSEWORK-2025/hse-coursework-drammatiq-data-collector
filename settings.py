"""Общие настройки для приложения."""

import logging
import time
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Dict


class Settings(BaseSettings):
    """Конфиг с переменными окружения."""

    KAFKA_HOST: str | None = "my-cluster-kafka-bootstrap"
    KAFKA_PORT: str | None = "9092"
    TOPIC: str | None = "raw_data_topic"
    BATCH_SIZE: int | None = 50
    POLL_TIMEOUT_MS: int | None = 5000

    REDIS_HOST: str | None = "redis"
    REDIS_PORT: str | None = "6379"
    KAFKA_GROUP_ID: str | None = "raw-data-consumer-group"

    LOG_UVICORN_FORMAT: str = "%(asctime)s %(levelname)s uvicorn: %(message)s"
    LOG_ACCESS_FORMAT: str = "%(asctime)s %(levelname)s access: %(message)s"
    LOG_DEFAULT_FORMAT: str = "%(asctime)s %(levelname)s %(name)s: %(message)s"


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="ignore",  # игнорировать лишние переменные в .env
    )


settings = Settings()

def setup_logging():
    logging.basicConfig(
        level='INFO',
        format=settings.LOG_DEFAULT_FORMAT,
    )
    # uvicorn
    handler_default = logging.StreamHandler()
    handler_default.setFormatter(logging.Formatter(settings.LOG_UVICORN_FORMAT))
    logging.getLogger("uvicorn").handlers = [handler_default]
    # uvicorn access
    handler_access = logging.StreamHandler()
    handler_access.setFormatter(logging.Formatter(settings.LOG_ACCESS_FORMAT))
    logging.getLogger("uvicorn.access").handlers = [handler_access]


setup_logging()
logging.info(f"connecting to redis redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0")
logging.info(f"connecting to kafka {settings.KAFKA_HOST}:{settings.KAFKA_PORT}")
