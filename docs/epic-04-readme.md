# Epic 04 README

## Что реализовано

Epic 04 внедряет полноценный `RoutingEngine`:
- граф сегментов (`hub -> outbound segments`);
- поиск маршрутов с пересадками;
- ограничения по пересадкам/бюджету/длительности/типам транспорта;
- ранжирование `price` / `time` / `balanced`;
- возврат `top-N`;
- `score_breakdown` в ответе.

## Компоненты

1. Routing engine:
- [routing_engine.py](/home/viktor/PycharmProjects/transport-service/app/services/routing_engine.py)

2. Интеграция в application service:
- [route_application.py](/home/viktor/PycharmProjects/transport-service/app/services/route_application.py)

3. Обновленные API схемы:
- [routes_api.py](/home/viktor/PycharmProjects/transport-service/app/schemas/routes_api.py)

## Как работает

1. `DbRouteApplicationService.search` получает candidate segments от provider adapters.
2. Сегменты нормализуются в `SegmentDTO`.
3. `RoutingEngine.find_routes` строит маршруты по графу:
- валидирует временную совместимость пересадок;
- применяет ограничения;
- считает метрики и score.
4. Сервис сохраняет маршруты и сегменты в БД.
5. Клиент получает `RouteDTO[]` с `score_breakdown`.

## Guardrails

В движке применяются ограничения для защиты от комбинаторного взрыва:
- `max_depth`;
- `max_paths_to_explore`;
- `max_transfers`.

## Тесты Epic 04

- [test_routing_engine.py](/home/viktor/PycharmProjects/transport-service/tests/test_routing_engine.py)

Покрыты сценарии:
- fastest vs cheapest;
- budget и transfer constraints;
- фильтр `allowed_transport_types`;
- top-N.

## Связанные документы

- [epic-04-routing-engine-plan.md](/home/viktor/PycharmProjects/transport-service/docs/epic-04-routing-engine-plan.md)
- [epic-04-api-contract.md](/home/viktor/PycharmProjects/transport-service/docs/epic-04-api-contract.md)
- [epic-04-sequence-diagrams.md](/home/viktor/PycharmProjects/transport-service/docs/epic-04-sequence-diagrams.md)
