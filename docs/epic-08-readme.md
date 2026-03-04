# Epic 08 README

## Что реализовано

Epic 08 добавляет наблюдаемость и guardrails:
- корреляция запросов (`request_id`, `trace_id`) через middleware + response headers;
- structured logging с автоподстановкой correlation-id;
- in-process метрики операций, провайдеров, ошибок и cache hit ratio;
- readiness с проверками `database` и `redis`;
- guardrails: payload size, batch size, routing exploration limit.

## Основные компоненты

1. Correlation context и logging:
- [request_context.py](/home/viktor/PycharmProjects/transport-service/app/utils/request_context.py)
- [logging.py](/home/viktor/PycharmProjects/transport-service/app/utils/logging.py)
- [main.py](/home/viktor/PycharmProjects/transport-service/main.py)

2. Metrics registry:
- [observability.py](/home/viktor/PycharmProjects/transport-service/app/services/observability.py)

3. Service integration:
- [route_application.py](/home/viktor/PycharmProjects/transport-service/app/services/route_application.py)
- [registry.py](/home/viktor/PycharmProjects/transport-service/app/services/providers/registry.py)
- [routing_engine.py](/home/viktor/PycharmProjects/transport-service/app/services/routing_engine.py)

4. Health endpoints:
- [health.py](/home/viktor/PycharmProjects/transport-service/app/routes/health.py)

5. Config guardrails:
- [config.py](/home/viktor/PycharmProjects/transport-service/config.py)

## Runbook деградации (MVP)

1. Рост latency p95/p99:
- проверить `/health/metrics -> operations.*.latency`;
- уменьшить `top_n` на клиенте;
- снизить `routing_max_paths_to_explore`.

2. Рост provider error-rate:
- проверить `/health/metrics -> providers.*.error_rate`;
- временно ограничить `transport_types` до стабильного провайдера;
- использовать fallback маршруты (уже включены в search flow).

3. Падение cache hit ratio:
- проверить `/health/metrics -> cache.hit_ratio`;
- проверить Redis readiness `/health/ready`;
- увеличить `redis_segments_ttl_seconds` при допустимой свежести данных.

4. Перегрузка batch:
- контролировать `batch_max_size`;
- уменьшить `max_concurrency` в batch payload.

## Тесты Epic 08

- [test_observability_epic08.py](/home/viktor/PycharmProjects/transport-service/tests/test_observability_epic08.py)

