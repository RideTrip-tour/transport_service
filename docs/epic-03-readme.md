# Epic 03 README

## Что реализовано

Epic 03 внедряет adapter layer для внешних провайдеров сегментов:
- интерфейс `ProviderAdapter`;
- `FlightProviderAdapter` с retry/backoff и concurrency limit;
- каркас `Train/Bus/Ferry` адаптеров;
- `ProviderRegistry` (registry/factory);
- интеграция adapter layer в `DbRouteApplicationService.search`.

## Компоненты

1. Базовые типы и интерфейс:
- [base.py](/home/viktor/PycharmProjects/transport-service/app/services/providers/base.py)
- [types.py](/home/viktor/PycharmProjects/transport-service/app/services/providers/types.py)

2. Адаптеры:
- [flight_adapter.py](/home/viktor/PycharmProjects/transport-service/app/services/providers/flight_adapter.py)
- [train_adapter.py](/home/viktor/PycharmProjects/transport-service/app/services/providers/train_adapter.py)
- [bus_adapter.py](/home/viktor/PycharmProjects/transport-service/app/services/providers/bus_adapter.py)
- [ferry_adapter.py](/home/viktor/PycharmProjects/transport-service/app/services/providers/ferry_adapter.py)

3. Registry:
- [registry.py](/home/viktor/PycharmProjects/transport-service/app/services/providers/registry.py)

4. Интеграция в application service:
- [route_application.py](/home/viktor/PycharmProjects/transport-service/app/services/route_application.py)

## Как работает

1. `DbRouteApplicationService.search` формирует `SegmentSearchQuery`.
2. `ProviderRegistry` выбирает адаптеры по `preferences.transport_types`.
3. Каждый адаптер возвращает `ProviderSegment[]` в унифицированном формате.
4. Сервис ранжирует сегменты, сохраняет их в `segments` и формирует `routes`.
5. История поиска сохраняется в `search_history`.

## Политики устойчивости

1. Retry + exponential backoff реализованы в `FlightProviderAdapter`.
2. Ограничение конкурентности реализовано через `asyncio.Semaphore` в базовом адаптере.
3. При пустых ответах `FlightProviderAdapter` возвращает fallback-сегменты.
4. При ошибках provider-layer сервис использует fallback и продолжает обработку поиска.

## Тесты Epic 03

- [test_provider_adapters.py](/home/viktor/PycharmProjects/transport-service/tests/test_provider_adapters.py)
- [test_route_application_provider_integration.py](/home/viktor/PycharmProjects/transport-service/tests/test_route_application_provider_integration.py)

## Связанные документы

- [epic-03-provider-adapters-plan.md](/home/viktor/PycharmProjects/transport-service/docs/epic-03-provider-adapters-plan.md)
- [epic-03-api-contract.md](/home/viktor/PycharmProjects/transport-service/docs/epic-03-api-contract.md)
- [epic-03-sequence-diagrams.md](/home/viktor/PycharmProjects/transport-service/docs/epic-03-sequence-diagrams.md)
