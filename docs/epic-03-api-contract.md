# Epic 03 API Contract

## Scope

Epic 03 не меняет внешние URL и DTO `/routes/*`, но меняет внутренний источник сегментов:
- вместо локальной генерации используется adapter layer;
- сегменты приходят через `ProviderAdapter` и нормализуются в единую модель.

## Internal contracts

### `ProviderAdapter`
- `transport_type: TransportType`
- `provider_name: str`
- `fetch_segments(query: SegmentSearchQuery) -> list[ProviderSegment]`

### `SegmentSearchQuery`
- `origin_id`
- `destination_id`
- `date`
- `top_n`
- `trace_id` (optional)

### `ProviderSegment`
- `provider`
- `transport_type`
- `external_id`
- `origin_hub_id`
- `destination_hub_id`
- `departure_time`
- `arrival_time`
- `duration_minutes`
- `price_amount`
- `currency`
- `raw_payload`

## Adapter registry

`ProviderRegistry.fetch_segments(query, transport_types)`:
- выбирает адаптеры по `transport_types` из preferences;
- агрегирует сегменты от доступных адаптеров;
- возвращает единый список для дальнейшего ранжирования и сохранения.

## Failure handling

1. `FlightProviderAdapter`:
- retry + exponential backoff;
- ограничение конкурентности через semaphore;
- fallback на локальные stub-сегменты при пустом ответе.

2. `DbRouteApplicationService`:
- при ошибках провайдерного слоя использует fallback-сегменты, чтобы сохранить работоспособность `search`.

