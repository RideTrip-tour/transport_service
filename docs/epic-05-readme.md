# Epic 05 README

## Что реализовано

Epic 05 доводит публичный API `/routes/*` до целевого поведения:
- `search` с обязательной валидацией локаций через `location-service`;
- `recalculate` с idempotency policy;
- `batch-recalculate` с chunked чтением из БД;
- единая ошибка `ApiErrorResponse` для интеграционных сценариев.

## Основные изменения

1. API слой:
- [routes.py](/home/viktor/PycharmProjects/transport-service/app/routes/routes.py)
- добавлен `_validate_locations(...)`
- `Idempotency-Key` читается из header в `recalculate`.

2. Application слой:
- [route_application.py](/home/viktor/PycharmProjects/transport-service/app/services/route_application.py)
- idempotency cache для `recalculate`
- chunked `list_by_ids` в `batch_recalculate`.

3. Схемы:
- [routes_api.py](/home/viktor/PycharmProjects/transport-service/app/schemas/routes_api.py)
- `RouteRecalculateRequest.idempotency_key` (optional).

## Важные сценарии

1. Unknown location -> `422 VALIDATION_ERROR`.
2. `location-service` unavailable -> `503 DEPENDENCY_UNAVAILABLE`.
3. Повторный `recalculate` с тем же `Idempotency-Key` не увеличивает `route_version` повторно.
4. Batch с большим списком `route_ids` обрабатывается порциями для снижения нагрузки.

## Тесты Epic 05

- [test_routes_api.py](/home/viktor/PycharmProjects/transport-service/tests/test_routes_api.py)
  - location validation success/error;
  - idempotency behavior;
  - unified errors.
- [test_routes_batch_chunking.py](/home/viktor/PycharmProjects/transport-service/tests/test_routes_batch_chunking.py)
  - проверка chunking `100/100/50`.

## Связанные документы

- [epic-05-routes-api-plan.md](/home/viktor/PycharmProjects/transport-service/docs/epic-05-routes-api-plan.md)
- [epic-05-api-contract.md](/home/viktor/PycharmProjects/transport-service/docs/epic-05-api-contract.md)
- [epic-05-sequence-diagrams.md](/home/viktor/PycharmProjects/transport-service/docs/epic-05-sequence-diagrams.md)
