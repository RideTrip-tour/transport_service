# Epic 02 API Contract

## Scope

Epic 02 не меняет URL публичного API, но меняет семантику: данные теперь персистятся в PostgreSQL (`segments`, `routes`, `search_history`).

## Endpoints

1. `POST /api/transport/routes/search`
2. `POST /api/transport/routes/{route_id}/recalculate`
3. `POST /api/transport/routes/batch-recalculate`

## Persistence semantics

### `POST /routes/search`
- создает запись в `segments` (stub-сегмент для каждого найденного маршрута);
- создает запись в `routes` с `segments_snapshot` (full `SegmentDTO`);
- создает запись в `search_history` (`user_id = null` на текущем этапе).

### `POST /routes/{route_id}/recalculate`
- читает `routes.id`;
- инкрементирует `route_version`;
- обновляет `recalculated_at`;
- возвращает обновленный `RouteDTO`.

### `POST /routes/batch-recalculate`
- читает маршруты батчем;
- для найденных маршрутов инкрементирует `route_version`;
- для отсутствующих возвращает `status = not_found`.

## Error contract

Единый формат ошибок сохраняется:

```json
{
  "code": "STRING_CODE",
  "message": "Human readable message",
  "details": {},
  "trace_id": "uuid"
}
```

Основные коды:
- `NOT_FOUND` (404)
- `VALIDATION_ERROR` (422)
- `DEPENDENCY_UNAVAILABLE` (503)

