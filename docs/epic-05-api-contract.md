# Epic 05 API Contract

## Scope

Epic 05 завершает публичный API `/routes/*`:
- добавляет валидацию локаций через `location-service`;
- фиксирует idempotency policy для `recalculate`;
- фиксирует batch-обработку крупного списка `route_ids` по чанкам.

## Endpoints

1. `POST /api/transport/routes/search`
2. `POST /api/transport/routes/{route_id}/recalculate`
3. `POST /api/transport/routes/batch-recalculate`

## `POST /routes/search`

Поведение:
1. Валидация входного payload.
2. Проверка локаций через `LocationClient`:
   - unknown location -> `422 VALIDATION_ERROR`
   - location service unavailable -> `503 DEPENDENCY_UNAVAILABLE`
3. Provider fetch + routing engine + persistence.
4. Сохранение `search_history`.

## `POST /routes/{route_id}/recalculate`

Idempotency policy:
- поддерживается header `Idempotency-Key`;
- повторный вызов с тем же `Idempotency-Key` и `route_id` возвращает cached response;
- без key пересчет выполняется как обычно.

## `POST /routes/batch-recalculate`

Batch policy:
- вход ограничен схемой `route_ids` (до 500);
- чтение маршрутов из БД выполняется чанками (по 100);
- ответ возвращает per-item статус (`updated`/`not_found`).

## Error model

Все ошибки возвращаются в едином формате:

```json
{
  "code": "VALIDATION_ERROR|NOT_FOUND|DEPENDENCY_UNAVAILABLE",
  "message": "text",
  "details": {},
  "trace_id": "uuid"
}
```

