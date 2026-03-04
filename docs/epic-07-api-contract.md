# Epic 07 API Contract

## Scope

Epic 07 усиливает batch API:
- добавляет orchestration `prepare -> execute -> persist -> report`;
- добавляет `unchanged` и `failed` статусы;
- добавляет audit id в batch response;
- добавляет trigger endpoint для внешних систем.

## Endpoints

1. `POST /api/transport/routes/batch-recalculate`
2. `POST /api/transport/routes/batch-recalculate/trigger`

## Request contract

`RouteBatchRecalculateRequest`:
- `route_ids: int[]` (1..500)
- `force_refresh: bool`
- `max_concurrency: int` (1..20)

## Response contract

`RouteBatchRecalculateResponse`:
- `batch_id: int | null` (audit record id)
- `total`
- `updated`
- `unchanged`
- `failed`
- `items[]`:
  - `route_id`
  - `status`: `updated | unchanged | failed | not_found`
  - `route` optional
  - `error` optional

## Behavioral notes

1. `route_ids` deduplicated in request order.
2. `force_refresh=false` returns `unchanged` for existing routes.
3. `failed` includes explicit `failed` + `not_found` in summary counter.
4. For each batch execution service stores audit record in `batch_recalculation_audit`.
5. Trigger endpoint returns `202 Accepted`.

