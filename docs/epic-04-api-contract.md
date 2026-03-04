# Epic 04 API Contract

## Scope

Epic 04 не меняет URL endpoint'ов, но меняет логику `POST /routes/search`:
- маршруты теперь строятся через отдельный `RoutingEngine`;
- учитываются ограничения и ранжирование из `preferences`;
- поддерживаются multi-segment маршруты.

## Public API changes

`RouteDTO` расширен полем:
- `score_breakdown: object<string, float>`

Остальные поля и endpoint'ы сохранены:
- `POST /api/transport/routes/search`
- `POST /api/transport/routes/{route_id}/recalculate`
- `POST /api/transport/routes/batch-recalculate`

## Search behavior contract

`POST /routes/search`:
1. Получает candidate segments от provider adapters.
2. Передает сегменты в `RoutingEngine`.
3. Строит допустимые пути с учетом:
   - `min_transfer_minutes`
   - `max_transfers`
   - `budget_amount`
   - `max_total_duration_minutes`
   - `transport_types`
4. Ранжирует по `sort_by`:
   - `price`
   - `time`
   - `balanced`
5. Возвращает `top_n`.

## Internal routing contract

`RoutingEngine.find_routes(...) -> list[RouteCandidate]`

`RouteCandidate`:
- `segments[]`
- `total_price`
- `currency`
- `total_duration_minutes`
- `total_transfer_duration_minutes`
- `transfers_count`
- `score`
- `score_breakdown`

