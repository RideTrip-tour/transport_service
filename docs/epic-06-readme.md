# Epic 06 README

## Что реализовано

Epic 06 добавляет Redis cache-aside для сегментов:
- `SegmentCacheRepository`;
- ключи `segment:{origin}:{dest}:{date}`;
- TTL сегментов `3600` секунд;
- cache интегрирован в `search` и `batch-recalculate`;
- soft fallback на provider при недоступности Redis;
- базовые cache-метрики (`hits/misses/stale/errors`).

## Компоненты

1. Cache repository:
- [segment_cache_repository.py](/home/viktor/PycharmProjects/transport-service/app/services/cache/segment_cache_repository.py)
- [cache/__init__.py](/home/viktor/PycharmProjects/transport-service/app/services/cache/__init__.py)

2. Конфигурация:
- [config.py](/home/viktor/PycharmProjects/transport-service/config.py)
  - `redis_host`, `redis_port`, `redis_db`, `redis_password`, `redis_segments_ttl_seconds`

3. Интеграция:
- [route_application.py](/home/viktor/PycharmProjects/transport-service/app/services/route_application.py)
  - `search` -> cache-aside
  - `batch_recalculate` -> cache warm-up

## Cache flow

1. `search` сначала читает сегменты из кэша.
2. Если `miss/stale/error` — получает сегменты у провайдеров.
3. Полученные сегменты сохраняются в кэш.
4. При недоступности Redis поиск продолжает работать через provider/fallback.

## Тесты Epic 06

- [test_segment_cache_repository.py](/home/viktor/PycharmProjects/transport-service/tests/test_segment_cache_repository.py)
  - key format, set/get, hit/miss/stale counters
- [test_route_application_cache_integration.py](/home/viktor/PycharmProjects/transport-service/tests/test_route_application_cache_integration.py)
  - search cache-aside (второй поиск не вызывает provider повторно)
  - batch warm-up по grouped keys

## Зависимости

Новая зависимость:
- `redis` (async client через `redis.asyncio`) в [requirements.txt](/home/viktor/PycharmProjects/transport-service/requirements.txt)

## Связанные документы

- [epic-06-redis-caching-plan.md](/home/viktor/PycharmProjects/transport-service/docs/epic-06-redis-caching-plan.md)
- [epic-06-api-contract.md](/home/viktor/PycharmProjects/transport-service/docs/epic-06-api-contract.md)
- [epic-06-sequence-diagrams.md](/home/viktor/PycharmProjects/transport-service/docs/epic-06-sequence-diagrams.md)
