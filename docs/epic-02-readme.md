# Epic 02 README

## Что реализовано

Epic 02 переводит хранение маршрутов из in-memory в PostgreSQL:
- новые таблицы `segments`, `routes`, `search_history`;
- миграция с hard replace legacy `transport_*`;
- CRUD-слой для новых сущностей;
- DB-backed `DbRouteApplicationService`;
- API `/routes/*` работает через `AsyncSession`.

## Основные компоненты

1. Модели:
- [segment.py](/home/viktor/PycharmProjects/transport-service/app/db/models/segment.py)
- [route.py](/home/viktor/PycharmProjects/transport-service/app/db/models/route.py)
- [search_history.py](/home/viktor/PycharmProjects/transport-service/app/db/models/search_history.py)

2. CRUD:
- [segment_crud.py](/home/viktor/PycharmProjects/transport-service/app/crud/segment_crud.py)
- [route_crud.py](/home/viktor/PycharmProjects/transport-service/app/crud/route_crud.py)
- [search_history_crud.py](/home/viktor/PycharmProjects/transport-service/app/crud/search_history_crud.py)

3. Сервис:
- [route_application.py](/home/viktor/PycharmProjects/transport-service/app/services/route_application.py)

4. Роуты и DI:
- [routes.py](/home/viktor/PycharmProjects/transport-service/app/routes/routes.py)
- [database.py](/home/viktor/PycharmProjects/transport-service/app/db/database.py)

5. Миграции:
- [20260303_0002_epic02_data_schema.py](/home/viktor/PycharmProjects/transport-service/alembic/versions/20260303_0002_epic02_data_schema.py)

## Как работает

### Search
1. `RouteSearchRequest` приходит в `routes.py`.
2. Сервис генерирует stub-сегмент(ы), сохраняет в `segments`.
3. Создает `routes` с `segments_snapshot` (full `SegmentDTO`).
4. Пишет `search_history` с nullable `user_id`.
5. Возвращает `RouteSearchResponse`.

### Recalculate
1. Сервис читает route по `id`.
2. Если нет записи -> `NotFoundAppError`.
3. Если запись есть -> инкремент `route_version`, обновление `recalculated_at`.
4. Возвращает обновленный `RouteDTO`.

### Batch recalculate
1. Сервис читает маршруты по списку `route_ids`.
2. Для найденных маршрутов повышает версию.
3. Для отсутствующих формирует `not_found`.
4. Возвращает агрегированный отчет.

## Ограничения текущего этапа

1. Провайдер интеграции пока stub (Epic 03/04).
2. `user_id` в `search_history` сохраняется как `null`.
3. Храним полный snapshot сегментов в `routes.segments_snapshot`.

## Связанные документы

- [epic-02-data-and-migrations-plan.md](/home/viktor/PycharmProjects/transport-service/docs/epic-02-data-and-migrations-plan.md)
- [epic-02-api-contract.md](/home/viktor/PycharmProjects/transport-service/docs/epic-02-api-contract.md)
- [epic-02-sequence-diagrams.md](/home/viktor/PycharmProjects/transport-service/docs/epic-02-sequence-diagrams.md)
