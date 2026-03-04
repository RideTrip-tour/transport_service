# Epic 06 API Contract

## Scope

Epic 06 не меняет публичные URL и DTO API, но добавляет cache-aside семантику для сегментов:
- Redis-ключ: `segment:{origin}:{dest}:{date}`;
- TTL: `3600` секунд (по умолчанию);
- fallback на direct-provider при недоступности Redis.

## Public endpoints

1. `POST /api/transport/routes/search`
2. `POST /api/transport/routes/{route_id}/recalculate`
3. `POST /api/transport/routes/batch-recalculate`

## Cache behavior contract

### Search
1. Формируется `SegmentSearchQuery`.
2. Выполняется `cache.get(key)`:
   - `hit` -> сегменты берутся из cache;
   - `miss/stale/error` -> загрузка из provider registry.
3. После provider fetch сегменты сохраняются в cache (`set` + TTL).
4. При Redis error сервис продолжает работу через provider/fallback.

### Batch-recalculate
1. Маршруты группируются по `(origin, destination, date)`.
2. По каждой группе выполняется cache warm-up.
3. Повторные batch-процессы получают сегменты из cache при наличии.

## Metrics contract

Cache-метрики:
- `hits`
- `misses`
- `stale`
- `errors`

Метрики доступны на уровне `SegmentCacheRepository.metrics`.

