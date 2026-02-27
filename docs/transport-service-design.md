# Transport Service - Technical Design (v1)

## 1. Scope

`Transport Service` отвечает за:
- хранение видов транспорта;
- хранение маршрутов/сегментов по видам транспорта;
- расчет составного маршрута (multi-modal);
- хранение пользовательского транспортного запроса;
- хранение ссылки на оплату (`payment_url`) для полученного маршрута.

`Location Service` отвечает за:
- хранение локаций;
- валидацию `location_id`.

Расписания и финальные офферы приходят из внешних сервисов. На первом этапе используем заглушку провайдера.

## 2. Service structure (aligned with auth-service)

По аналогии с `auth-service`:
- `config.py` в корне на первом этапе;
- `main.py` регистрирует роутеры через префиксы gateway-формата;
- docs/openapi отдаются через сервисный префикс.

Целевая структура:
- `app/routes`
  - `transport_types.py`
  - `transport_catalog.py`
  - `transport_requests.py`
  - `route_planner.py`
  - `health.py`
- `app/schemas`
  - `transport_type.py`
  - `transport_catalog.py`
  - `transport_request.py`
  - `planner.py`
- `app/services`
  - `transport_type_service.py`
  - `transport_catalog_service.py`
  - `transport_request_service.py`
  - `route_planner_service.py`
  - `location_client.py`
  - `schedule_provider_client.py` (stub now, external later)
- `app/crud`
  - `transport_type_crud.py`
  - `transport_catalog_crud.py`
  - `transport_request_crud.py`
  - `transport_quote_crud.py`
- `app/db/models`
  - `transport_type.py`
  - `transport_catalog_route.py`
  - `transport_request.py`
  - `transport_quote.py`

## 3. Data model

Ниже объединены цели сервиса + базовая модель из вашего скриншота (с адаптацией под microservice и location-service).

### 3.1 transport_types
- `id` (int, PK)
- `code` (varchar, unique, not null) - `bus`, `train`, `flight`, `taxi`, `mixed`
- `name` (varchar, not null)
- `description` (text, nullable)
- `is_active` (bool, default true)
- `created_at` (timestamptz)
- `updated_at` (timestamptz)

### 3.2 transport_catalog_routes
Каталог базовых ребер графа маршрутов.
- `id` (int, PK)
- `transport_type_id` (int, FK -> transport_types.id, not null)
- `from_location_id` (int, not null)
- `to_location_id` (int, not null)
- `base_duration_minutes` (int, not null)
- `base_price_amount` (numeric(12,2), nullable)  
  (может быть `null`, если цену дает только внешний провайдер)
- `base_currency` (varchar(3), nullable)
- `provider` (varchar, nullable)
- `is_active` (bool, default true)
- `created_at` (timestamptz)
- `updated_at` (timestamptz)

Индексы/ограничения:
- index(`from_location_id`)
- index(`to_location_id`)
- index(`transport_type_id`)
- index(`from_location_id`, `to_location_id`, `is_active`)
- check(`base_duration_minutes > 0`)
- check(`from_location_id <> to_location_id`)

### 3.3 transport_requests
Пользовательская сущность на базе присланной модели.
- `id` (int, PK)
- `user_id` (int, not null)  
  (тип можно позже унифицировать с auth-service при необходимости)
- `type` (enum/string, not null)  
  (`single`, `composed`; либо `mixed` через transport_type)
- `transport_type_id` (int, nullable)  
  (`null` для multi-modal)
- `departure_datetime` (timestamptz, nullable)
- `arrival_datetime` (timestamptz, nullable)
- `departure_location_id` (int, not null)
- `arrival_location_id` (int, not null)
- `passenger_count` (int, not null)
- `comment` (varchar, nullable)
- `status` (enum/string, not null)  
  (`draft`, `planned`, `quoted`, `booked`, `cancelled`)
- `created_at` (timestamptz)
- `updated_at` (timestamptz)

Индексы/ограничения:
- index(`user_id`)
- index(`departure_location_id`)
- index(`arrival_location_id`)
- check(`passenger_count > 0`)
- check(`departure_location_id <> arrival_location_id`)

### 3.4 transport_quotes
Оффер от внешнего провайдера для конкретного `transport_request`.
- `id` (int, PK)
- `transport_request_id` (int, FK -> transport_requests.id, not null)
- `provider_name` (varchar, not null)
- `external_quote_id` (varchar, nullable)
- `price_amount` (numeric(12,2), not null)
- `currency` (varchar(3), not null)  
  (мультивалюта поддерживается на уровне записи)
- `payment_url` (text, not null)
- `expires_at` (timestamptz, nullable)
- `payload` (json, nullable)  
  (сырые детали ответа внешнего сервиса)
- `created_at` (timestamptz)
- `updated_at` (timestamptz)

Индексы:
- index(`transport_request_id`)
- index(`currency`)
- index(`provider_name`)

## 4. External integrations

### 4.1 Location Service

Минимальный контракт:
- `GET /locations/{location_id}` -> `200` или `404`.

Поведение:
- на `create/update` валидируем `departure_location_id`, `arrival_location_id`;
- перед планированием валидируем входные локации;
- при недоступности возвращаем `503`.

### 4.2 Schedule/Offer Provider (external, stub now)

На первом этапе:
- интерфейс `schedule_provider_client.py` + stub-реализация;
- stub возвращает тестовые `duration`, `price_amount`, `currency`, `payment_url`.

Далее:
- заменить stub на внешний HTTP/gRPC клиент без изменения бизнес-слоя.

### 4.3 Config additions

Добавить настройки:
- `location_service_base_url`
- `location_service_timeout_ms`
- `location_service_retries`
- `schedule_provider_base_url`
- `schedule_provider_timeout_ms`
- `schedule_provider_retries`
- `default_currency` (fallback, но не ограничение мультивалюты)

## 5. API contract (gateway mode)

Префикс без версионирования: `/api/transport`

Документация сервиса:
- `docs_url="/api/transport/docs"`
- `redoc_url="/api/transport/redoc"`
- `openapi_url="/api/transport/openapi.json"`

### 5.1 Transport types
- `POST /api/transport/types`
- `GET /api/transport/types`
- `GET /api/transport/types/{id}`
- `PATCH /api/transport/types/{id}`
- `DELETE /api/transport/types/{id}`

### 5.2 Transport catalog routes
- `POST /api/transport/catalog/routes`
- `GET /api/transport/catalog/routes`
- `GET /api/transport/catalog/routes/{id}`
- `PATCH /api/transport/catalog/routes/{id}`
- `DELETE /api/transport/catalog/routes/{id}`

### 5.3 Transport requests (user-level)
- `POST /api/transport/requests`
- `GET /api/transport/requests/{id}`
- `GET /api/transport/requests?user_id=...`
- `PATCH /api/transport/requests/{id}`

### 5.4 Route planning and quote
- `POST /api/transport/planner/compose`
  - строит составной маршрут (без лимита по числу трансферов);
  - опциональный фильтр `allowed_transport_type_ids`.
- `POST /api/transport/requests/{id}/quote`
  - вызывает provider(stub);
  - сохраняет `transport_quotes` с `payment_url`;
  - возвращает quote.

### 5.5 Health
- `GET /api/transport/health/live`
- `GET /api/transport/health/ready`

## 6. Planner algorithm

MVP:
- ориентированный граф: вершина = `location_id`, ребро = `transport_catalog_routes`;
- Dijkstra:
  - `fastest`: вес = `duration`;
  - `cheapest`: вес = `price_amount`;
  - `balanced`: нормализованная комбинация времени и цены;
- ограничения на число трансферов отсутствуют;
- защита от циклов и корректная работа на разреженном графе обязательны.

## 7. Implementation roadmap

### Phase 1
- модели + Alembic миграция: `transport_types`, `transport_catalog_routes`, `transport_requests`, `transport_quotes`;
- базовые CRUD endpoints;
- настройка gateway-style роутов `/api/transport/...`;
- `location_client` с timeout/retry;
- `schedule_provider_client` (stub) и сохранение `payment_url`.

### Phase 2
- planner режимы `fastest`, `cheapest`, `balanced`;
- quote endpoint через provider abstraction;
- структурированные ошибки интеграций.

### Phase 3
- observability (метрики, latency, error rates);
- кэш валидации локаций;
- контрактные тесты интеграций.

## 8. Testing

- Unit:
  - planner-алгоритм;
  - money/currency валидация;
  - quote mapping (`payment_url`, currency, expires).
- Integration:
  - CRUD + planner + quote endpoints;
  - мок/стаб внешнего provider;
  - сценарии `404 location`, `503 external service`.
- Migration:
  - `alembic upgrade head` в CI;
  - smoke downgrade на 1 ревизию.

## 9. Decisions fixed by current discussion

- API префикс: `/api/transport` (без version path).
- Архитектура: gateway-proxy + aggregated swagger.
- Расписания: через внешние сервисы, сейчас stub.
- Валюта: мультивалюта.
- Оплата: хранить `payment_url` в quote.
- Лимит трансферов: не ограничиваем.

## 10. Logging (critical points)

Логирование добавлено для критичных сценариев:
- вызовы `Location Service`: успех, `404`, неожиданный статус, retry/ошибки;
- построение маршрута: входные параметры, отсутствие пути, итоговый маршрут;
- работа API:
  - создание/обновление/деактивация catalog routes;
  - создание/обновление transport requests;
  - получение quote и сохранение `payment_url`;
  - ситуации `404`/`422`/`503`.

Формат логов:
- единый `StreamHandler` в stdout;
- уровень по умолчанию: `INFO`;
- конфигурация: `app/utils/logging.py`.

## 11. Current implementation status

Реализовано на текущий момент:
- gateway-маршруты под префиксом `/api/transport`;
- CRUD для:
  - `transport types`;
  - `transport catalog routes`;
  - `transport requests`;
- endpoint построения маршрута: `POST /api/transport/planner/compose`;
- endpoint получения оффера: `POST /api/transport/requests/{id}/quote`;
- stub-провайдер для quote (`currency`, `payment_url`, `expires_at`);
- health endpoints:
  - `GET /api/transport/health/live`;
  - `GET /api/transport/health/ready`;
- миграция схемы Alembic: `20260227_0001_transport_service_init`.
