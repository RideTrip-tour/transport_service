# Epic 08 API Contract

## Scope

Epic 08 не меняет core routes URL, но добавляет observability/reliability контракт:
- correlation headers в каждом ответе;
- guardrail по размеру payload;
- метрики и расширенная readiness проверка.

## Existing endpoints (unchanged)

1. `POST /api/transport/routes/search`
2. `POST /api/transport/routes/{route_id}/recalculate`
3. `POST /api/transport/routes/batch-recalculate`
4. `POST /api/transport/routes/batch-recalculate/trigger`

## New/extended health endpoints

1. `GET /api/transport/health/live`  
   Response: `{"status":"ok"}`
2. `GET /api/transport/health/ready`  
   Response:
   - `status`: `ok | error`
   - `checks.database`: `ok | error`
   - `checks.redis`: `ok | error | disabled`
3. `GET /api/transport/health/metrics`  
   Response содержит:
   - `operations` (`search`, `recalculate`, `batch_recalculate`) с latency/error-rate;
   - `providers` с SLA (`calls`, `errors`, `sla_success_rate`);
   - `cache` (`hits`, `misses`, `stale`, `errors`, `hit_ratio`);
   - `error_codes`.

## Correlation contract

Для всех HTTP ответов:
- header `X-Request-ID`
- header `X-Trace-ID`

Если заголовки пришли от upstream, сервис переиспользует их, иначе генерирует UUID.

## Guardrails contract

1. Payload size:
- ограничение `settings.max_request_body_bytes`;
- при превышении: `413 PAYLOAD_TOO_LARGE` (`ApiErrorResponse`).

2. Batch size:
- runtime limit `settings.batch_max_size`;
- при превышении: `422 VALIDATION_ERROR` (`details.batch_max_size`).

3. Routing exploration:
- ограничение `settings.routing_max_paths_to_explore` применяется в routing engine.

