# Transport Service

Микросервис транспорта в архитектуре gateway.

Базовый API-префикс сервиса: `/api/transport`

Swagger:
- `/api/transport/docs`
- `/api/transport/redoc`
- `/api/transport/openapi.json`

Подробное описание сервиса:
- [docs/transport-service-design.md](/home/viktor/PycharmProjects/transport-service/docs/transport-service-design.md)
- [docs/transport-service-requirements.md](/home/viktor/PycharmProjects/transport-service/docs/transport-service-requirements.md)
- [docs/transport-service-task-plan.md](/home/viktor/PycharmProjects/transport-service/docs/transport-service-task-plan.md)

## Что реализовано

- Epic 01: архитектурный каркас и API-контракты для `routes`;
- Epic 02: персистентность маршрутов в PostgreSQL (`segments`, `routes`, `search_history`);
- Epic 03: adapter layer провайдеров (`ProviderAdapter`, `FlightProviderAdapter`, registry);
- Epic 04: routing engine (граф, ограничения, ранжирование, `top-N`);
- Epic 05: API `/routes/*` (location validation, idempotency, batch chunking);
- Epic 06: Redis cache-aside для сегментов (`segment:{origin}:{dest}:{date}`, TTL 3600);
- Epic 07: batch orchestration (grouping, bounded concurrency, audit, trigger endpoint);
- Epic 08: observability/reliability (correlation-id, metrics, readiness checks, guardrails);
- `POST /api/transport/routes/search`;
- `POST /api/transport/routes/{route_id}/recalculate`;
- `POST /api/transport/routes/batch-recalculate`;
- единая модель ошибок (`code`, `message`, `details`, `trace_id`);
- проверка доступности сервиса (`health/live`, `health/ready`).

Все идентификаторы (`id`, `user_id`, `location_id`) используются в формате `int`.

## Локальный запуск

### 1. Подготовка окружения

```bash
make venv
```

или вручную:

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Рекомендуется взять шаблон:

```bash
cp .env.example .env
```

Затем заполнить значения в `.env`, например:

```env
APP_NAME=transport-service
DEBUG=true

DB_HOST=localhost
DB_PORT=5432
DB_NAME=mydb
DB_USER=user
DB_PASS=password123

location_service_base_url=http://localhost:8010
location_service_timeout_ms=1000
location_service_retries=2

schedule_provider_base_url=http://localhost:8020
schedule_provider_timeout_ms=1500
schedule_provider_retries=2

default_currency=USD
```

### 3. Применение миграций

```bash
alembic upgrade head
```

или:

```bash
make migrate
```

### 4. Запуск сервиса

```bash
make run-dev
```

или:

```bash
./venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Проверка

- health: `GET http://localhost:8000/api/transport/health/live`
- swagger: `http://localhost:8000/api/transport/docs`

## Тесты

```bash
python3 -m pytest -q
```
