# HSE Coursework: Dramatiq Data Collector (Сервис обработки данных)

## Описание

Этот репозиторий содержит сервис для асинхронной обработки и агрегации пользовательских данных. Сервис читает сырые данные из Kafka, обрабатывает их с помощью воркеров Dramatiq, сохраняет в базу данных.

## Основные возможности
- Чтение сырых данных пользователя, полученных от [сервиса сбора данных](https://github.com/HSE-COURSEWORK-2025/hse-coursework-backend-data-collection-service) через очередь Kafka
- Асинхронная обработка данных с помощью Dramatiq
- Сохранение обработанных данных в PostgreSQL
- Гибкая трансформация данных по типу


## Структура проекта

- `main.py` — Kafka consumer, отправляющий данные на обработку
- `tasks.py` — Dramatiq actor для обработки и сохранения данных
- `broker.py` — настройка брокера Dramatiq (Redis)
- `dataTransformation.py` — трансформации данных по типу
- `db/` — работа с базой данных (engine, session, модели)
- `redisClient.py` — асинхронный клиент Redis
- `settings.py` — глобальные настройки приложения
- `deployment/` — манифесты Kubernetes (Deployment, Service)
- `requirements.txt` — зависимости Python
- `Dockerfile.consumer`, `Dockerfile.dramatiq` — сборка Docker-образов для consumer и worker
- `deploy.sh`, `stop.sh` — скрипты для деплоя и остановки

## Быстрый старт (локально)

1. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Создайте файл `.env` с параметрами подключения**
3. **Запустите Dramatiq worker:**
   ```bash
   dramatiq tasks
   ```
4. **Запустите consumer:**
   ```bash
   python3 main.py
   ```
5. **(Опционально) Запустите Kafka, Redis и PostgreSQL локально:**
   ```bash
   docker-compose -f kafka-local-docker-compose.yaml up -d
   ```

## Переменные окружения

- `KAFKA_HOST`, `KAFKA_PORT` — адрес и порт Kafka
- `REDIS_HOST`, `REDIS_PORT` — параметры Redis
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` — параметры PostgreSQL
- `TOPIC`, `BATCH_SIZE`, `POLL_TIMEOUT_MS` — параметры обработки
- `KAFKA_GROUP_ID` — идентификатор consumer group

Пример `.env`:
```
KAFKA_HOST=my-cluster-kafka-bootstrap
KAFKA_PORT=9092
REDIS_HOST=redis
REDIS_PORT=6379
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=records
TOPIC=raw_data_topic
BATCH_SIZE=50
POLL_TIMEOUT_MS=5000
KAFKA_GROUP_ID=raw-data-consumer-group
```

## Сборка и запуск в Docker

```bash
docker build -f Dockerfile.consumer -t awesomecosmonaut/data-collection-consumer-app .
docker build -f Dockerfile.dramatiq -t awesomecosmonaut/data-collection-dramatiq-app .
docker run --env-file .env awesomecosmonaut/data-collection-consumer-app
# или
docker run --env-file .env awesomecosmonaut/data-collection-dramatiq-app
```

## Деплой в Kubernetes

1. Соберите и отправьте образы:
   ```bash
   ./deploy.sh
   ```
2. Остановить сервис:
   ```bash
   ./stop.sh
   ```
3. Манифесты находятся в папке `deployment/` (Deployment, Service)

## Метрики и документация
- Логирование событий обработки и ошибок
- Метрики можно добавить через Prometheus-экспортер при необходимости
