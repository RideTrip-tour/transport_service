# Epic 01 API Contract

## Endpoints

1. `POST /api/transport/routes/search`
2. `POST /api/transport/routes/{route_id}/recalculate`
3. `POST /api/transport/routes/batch-recalculate`

## Unified Error Model

All business errors return:

```json
{
  "code": "STRING_CODE",
  "message": "Human readable message",
  "details": {
    "optional": "context"
  },
  "trace_id": "uuid"
}
```

Supported error statuses for routes API:
- `404`
- `422`
- `503`
- `504`

## Search Contract

Request (`RouteSearchRequest`):
- `origin_id` `int`
- `destination_id` `int`
- `date` `YYYY-MM-DD`
- `top_n` `1..20`
- `sort_by` = `price|time|balanced`
- `preferences` object

Response (`RouteSearchResponse`):
- `routes`: list of `RouteDTO`

## Recalculate Contract

Request (`RouteRecalculateRequest`):
- `force_refresh` `bool`

Response (`RouteRecalculateResponse`):
- `route` `RouteDTO`
- `recalculated_at` `datetime`
- `changed` `bool`

## Batch Recalculate Contract

Request (`RouteBatchRecalculateRequest`):
- `route_ids` `int[]` (1..500)
- `force_refresh` `bool`

Response (`RouteBatchRecalculateResponse`):
- `total`
- `updated`
- `unchanged`
- `failed`
- `items[]` with per-route status

