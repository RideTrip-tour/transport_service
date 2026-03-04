# Epic 01 README

## Что реализовано

Epic 01 формирует контрактный слой сервиса:
- новые endpoint `routes`:
  - `POST /api/transport/routes/search`
  - `POST /api/transport/routes/{route_id}/recalculate`
  - `POST /api/transport/routes/batch-recalculate`
- единый формат ошибок:
  - `code`
  - `message`
  - `details`
  - `trace_id`
- базовые application-интерфейсы для search/recalculate/batch.

## Как устроено по слоям

1. API слой:
- файл: [routes.py](/home/viktor/PycharmProjects/transport-service/app/routes/routes.py)
- принимает HTTP-запросы;
- валидирует payload через Pydantic схемы;
- вызывает application-сервис;
- возвращает контрактные DTO.

2. Контрактные схемы:
- файл: [routes_api.py](/home/viktor/PycharmProjects/transport-service/app/schemas/routes_api.py)
- содержит request/response модели для всех `routes` endpoint;
- задает ключевые ограничения (`top_n`, `route_ids`, `origin != destination`, и т.д.).

3. Application слой:
- файл: [route_application.py](/home/viktor/PycharmProjects/transport-service/app/services/route_application.py)
- определяет интерфейсы:
  - `RouteSearchService`
  - `RouteRecalculationService`
  - `BatchRecalculationService`
- текущая реализация: `InMemoryRouteApplicationService` (контрактный stub).

4. Domain слой:
- файл: [models.py](/home/viktor/PycharmProjects/transport-service/app/domain/models.py)
- фиксирует доменные сущности:
  - `Segment`
  - `Route`
  - `SearchHistoryEntry`
  - `ProviderQuote`.

5. Error handling:
- файлы: [errors.py](/home/viktor/PycharmProjects/transport-service/app/errors.py), [api_error.py](/home/viktor/PycharmProjects/transport-service/app/schemas/api_error.py), [main.py](/home/viktor/PycharmProjects/transport-service/main.py)
- `AppError` и наследники описывают бизнес-ошибки;
- глобальный exception handler в `main.py` приводит их к единому JSON-формату.

## Поток взаимодействий

1. `search`:
- клиент отправляет `RouteSearchRequest`;
- FastAPI валидирует схему;
- роут вызывает `route_service.search(...)`;
- сервис формирует `RouteDTO[]` (в текущей версии in-memory/stub);
- API возвращает `RouteSearchResponse`.

2. `recalculate`:
- клиент отправляет `route_id` + `RouteRecalculateRequest`;
- роут вызывает `route_service.recalculate(...)`;
- если маршрут не найден, сервис бросает `NotFoundAppError`;
- global handler возвращает `404` с `ApiErrorResponse`;
- если найден, возвращается обновленная версия маршрута.

3. `batch-recalculate`:
- клиент отправляет список `route_ids`;
- роут вызывает `route_service.batch_recalculate(...)`;
- сервис обрабатывает каждый `route_id` отдельно;
- в ответе формируется агрегат (`total/updated/failed`) и статусы по элементам.

## Что с чем взаимодействует

1. `main.py` подключает:
- `routes_router` (новый контрактный API);
- `health_router`.

2. `routes.py` зависит от:
- `routes_api.py` (DTO);
- `route_application.py` (application-логика);
- `api_error.py` (модель ошибок для OpenAPI).

3. `route_application.py` зависит от:
- `routes_api.py` (типизированные вход/выход);
- `errors.py` (доменные ошибки).

4. `main.py` зависит от:
- `errors.py` и `api_error.py` для глобального error contract.

## Текущее состояние и границы Epic 01

1. Epic 01 закрывает контракты и архитектурный каркас.
2. Источник данных пока in-memory (осознанно для контрактного этапа).
3. Интеграции с БД/Redis/provider/routing engine будут реализованы в следующих эпиках.

## Связанные документы

- [epic-01-api-contract.md](/home/viktor/PycharmProjects/transport-service/docs/epic-01-api-contract.md)
- [epic-01-sequence-diagrams.md](/home/viktor/PycharmProjects/transport-service/docs/epic-01-sequence-diagrams.md)
- [epic-01-architecture-and-contracts-plan.md](/home/viktor/PycharmProjects/transport-service/docs/epic-01-architecture-and-contracts-plan.md)
