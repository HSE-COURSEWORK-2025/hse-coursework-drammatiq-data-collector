"""Общие настройки для приложения."""

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
    

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="ignore",  # игнорировать лишние переменные в .env
    )


settings = Settings()
print(f"connecting to redis redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0")
print(f"connecting to kafka {settings.KAFKA_HOST}:{settings.KAFKA_PORT}")
