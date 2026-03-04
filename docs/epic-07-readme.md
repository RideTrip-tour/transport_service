# Epic 07 README

## Что реализовано

Epic 07 расширяет batch-пересчет:
- orchestration pipeline `prepare -> execute -> persist -> report`;
- группировка маршрутов по направлению/дате;
- bounded concurrency + retry при cache warm-up;
- статусы `updated`, `unchanged`, `failed`, `not_found`;
- audit таблица и `batch_id` в ответе;
- endpoint для внешнего trigger.

## Компоненты

1. Application service:
- [route_application.py](/home/viktor/PycharmProjects/transport-service/app/services/route_application.py)

2. API layer:
- [routes.py](/home/viktor/PycharmProjects/transport-service/app/routes/routes.py)

3. Audit storage:
- [batch_recalculation_audit.py](/home/viktor/PycharmProjects/transport-service/app/db/models/batch_recalculation_audit.py)
- [batch_recalculation_audit_crud.py](/home/viktor/PycharmProjects/transport-service/app/crud/batch_recalculation_audit_crud.py)
- [20260303_0003_epic07_batch_audit.py](/home/viktor/PycharmProjects/transport-service/alembic/versions/20260303_0003_epic07_batch_audit.py)

4. Schema updates:
- [routes_api.py](/home/viktor/PycharmProjects/transport-service/app/schemas/routes_api.py)

## Ключевое поведение

1. Dedup route ids:
- дубликаты удаляются с сохранением исходного порядка.

2. Chunk loading:
- маршруты читаются по чанкам (`chunk_size=100`).

3. Grouped warm-up:
- кэш прогревается по уникальным группам `(origin, destination, date)`.

4. Partial success:
- `unchanged` для `force_refresh=false`;
- `not_found` для отсутствующих маршрутов;
- `failed` при исключениях обновления;
- `updated` для успешных обновлений.

5. Audit:
- сохраняется summary и payload результата;
- `batch_id` возвращается в API-ответе.

## Тесты Epic 07

- [test_routes_batch_chunking.py](/home/viktor/PycharmProjects/transport-service/tests/test_routes_batch_chunking.py)
- [test_batch_recalculation_orchestration.py](/home/viktor/PycharmProjects/transport-service/tests/test_batch_recalculation_orchestration.py)
- [test_routes_api.py](/home/viktor/PycharmProjects/transport-service/tests/test_routes_api.py)

## Связанные документы

- [epic-07-batch-recalculation-plan.md](/home/viktor/PycharmProjects/transport-service/docs/epic-07-batch-recalculation-plan.md)
- [epic-07-api-contract.md](/home/viktor/PycharmProjects/transport-service/docs/epic-07-api-contract.md)
- [epic-07-sequence-diagrams.md](/home/viktor/PycharmProjects/transport-service/docs/epic-07-sequence-diagrams.md)
