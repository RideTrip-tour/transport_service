# Transport Service

Микросервис транспорта в архитектуре gateway.

Базовый API-префикс сервиса: `/api/transport`

Swagger:
- `/api/transport/docs`
- `/api/transport/redoc`
- `/api/transport/openapi.json`

Подробное описание сервиса:
- [docs/transport-service-design.md](/home/viktor/PycharmProjects/transport-service/docs/transport-service-design.md)

## Что реализовано

- хранение видов транспорта;
- хранение маршрутов каталога между локациями;
- хранение пользовательских транспортных запросов;
- построение составного маршрута (`planner/compose`);
- получение quote через stub-провайдер с `payment_url`;
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

Можно создать `.env` в корне проекта, например:

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
