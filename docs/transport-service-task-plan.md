# Transport Service: План реализации и декомпозиция задач

Источник требований: [transport-service-requirements.md](/home/viktor/PycharmProjects/transport-service/docs/transport-service-requirements.md)

## 1. Цель плана

Преобразовать требования в последовательный backlog задач для реализации production-ready `transport-service` с поддержкой:
- онлайн-поиска маршрутов;
- пересчета маршрута;
- batch-пересчета;
- внешних провайдеров;
- кэширования сегментов;
- хранения истории поисков.

## 2. Эпики

1. Архитектурный каркас и контракты. Подробный план: [epic-01-architecture-and-contracts-plan.md](/home/viktor/PycharmProjects/transport-service/docs/epic-01-architecture-and-contracts-plan.md)
2. Данные и миграции. Подробный план: [epic-02-data-and-migrations-plan.md](/home/viktor/PycharmProjects/transport-service/docs/epic-02-data-and-migrations-plan.md)
3. Adapter layer и интеграции провайдеров. Подробный план: [epic-03-provider-adapters-plan.md](/home/viktor/PycharmProjects/transport-service/docs/epic-03-provider-adapters-plan.md)
4. Routing engine. Подробный план: [epic-04-routing-engine-plan.md](/home/viktor/PycharmProjects/transport-service/docs/epic-04-routing-engine-plan.md)
5. API `/routes/*`. Подробный план: [epic-05-routes-api-plan.md](/home/viktor/PycharmProjects/transport-service/docs/epic-05-routes-api-plan.md)
6. Кэширование (Redis). Подробный план: [epic-06-redis-caching-plan.md](/home/viktor/PycharmProjects/transport-service/docs/epic-06-redis-caching-plan.md)
7. Batch-пересчет. Подробный план: [epic-07-batch-recalculation-plan.md](/home/viktor/PycharmProjects/transport-service/docs/epic-07-batch-recalculation-plan.md)
8. Наблюдаемость и надежность. Подробный план: [epic-08-observability-and-reliability-plan.md](/home/viktor/PycharmProjects/transport-service/docs/epic-08-observability-and-reliability-plan.md)
9. Тестирование и выпуск. Подробный план: [epic-09-testing-and-release-plan.md](/home/viktor/PycharmProjects/transport-service/docs/epic-09-testing-and-release-plan.md)

## 3. Декомпозиция на задачи

## Эпик 1. Архитектурный каркас и контракты

1. Зафиксировать DTO и API-контракты для:
   - `POST /routes/search`
   - `POST /routes/{id}/recalculate`
   - `POST /routes/batch-recalculate`
2. Ввести доменные сущности уровня сервиса:
   - `Segment`
   - `Route`
   - `SearchHistoryEntry`
   - `ProviderQuote`
3. Определить ошибки и коды ответов (422/404/503/504).
4. Подготовить sequence-диаграммы для сценариев search/recalculate/batch.

Критерий готовности:
- есть утвержденный контракт API и доменная модель, достаточные для начала реализации.

## Эпик 2. Данные и миграции

1. Спроектировать таблицу `segments`:
   - индексы по `(origin_hub_id, destination_hub_id, departure_time)`, `provider`, `expires_at`.
2. Спроектировать таблицу `routes`:
   - `segments_snapshot jsonb`
   - `route_version`
   - `recalculated_at`
3. Спроектировать таблицу `search_history`:
   - индексы `(user_id, created_at)`, `(origin_location_id, destination_location_id, date)`.
4. Создать Alembic-миграцию.
5. Добавить CRUD-слой для новых сущностей.

Критерий готовности:
- миграции применяются, чтение/запись новых сущностей работает.

## Эпик 3. Adapter Layer и интеграции

1. Ввести интерфейс `ProviderAdapter`:
   - `fetch_segments(...)`
   - `refresh_segment(...)`
2. Реализовать базовый `FlightProviderAdapter` (MVP-провайдер).
3. Подготовить каркас для:
   - `TrainProviderAdapter`
   - `BusProviderAdapter`
   - `FerryProviderAdapter`
4. Реализовать нормализацию ответов провайдеров в единую модель `Segment`.
5. Добавить retry/timeout/circuit-breaker политику.

Критерий готовности:
- сервис может получать сегменты минимум от одного реального/стаб-провайдера через единый интерфейс.

## Эпик 4. Routing Engine

1. Реализовать построение графа: узлы = хабы, ребра = сегменты.
2. Реализовать поиск маршрутов:
   - shortest path по времени;
   - shortest path по стоимости;
   - weighted-score (комбинированный).
3. Добавить ограничения:
   - минимальное время пересадки;
   - максимум пересадок (например, 3);
   - фильтр типов транспорта;
   - бюджет и максимальная длительность.
4. Реализовать выдачу `top-N` маршрутов.
5. Подготовить расширение под Pareto frontier (без включения в MVP).

Критерий готовности:
- движок стабильно возвращает валидные top-N маршруты с учетом ограничений.

## Эпик 5. API `/routes/*`

1. `POST /routes/search`:
   - валидация входа;
   - вызов location-service;
   - получение сегментов (cache/provider);
   - расчет маршрутов;
   - сохранение `search_history`;
   - возврат `RouteDTO[]`.
2. `POST /routes/{id}/recalculate`:
   - загрузка сохраненного маршрута;
   - обновление сегментов;
   - пересчет цены/времени;
   - обновление `route_version`, `recalculated_at`.
3. `POST /routes/batch-recalculate`:
   - прием списка `route_id`;
   - групповая обработка с reuse кэша;
   - возврат статусов по каждому маршруту.
4. Унифицировать модель ошибок и ответов.

Критерий готовности:
- все 3 endpoint работают по согласованному контракту.

## Эпик 6. Redis-кэш

1. Подключить Redis и конфигурацию (`host`, `port`, `ttl`).
2. Реализовать ключи:
   - `segment:{origin}:{dest}:{date}`
3. Добавить слой `SegmentCacheRepository`:
   - `get_segments(...)`
   - `set_segments(..., ttl=3600)`
4. Встроить cache-aside в `search` и `batch`.
5. Добавить метрики cache-hit/cache-miss.

Критерий готовности:
- сегменты кэшируются на 1 час, повторные запросы снижают нагрузку на провайдеров.

## Эпик 7. Batch-пересчет

1. Реализовать группировку маршрутов по направлению/дате.
2. Настроить ограничение конкурентности внешних запросов.
3. Реализовать частично-успешный результат (partial success).
4. Подготовить запуск от cron/внешнего триггера.

Критерий готовности:
- batch обрабатывает большие списки маршрутов без перегрузки провайдеров.

## Эпик 8. Наблюдаемость и надежность

1. Добавить метрики:
   - latency по endpoint;
   - ошибки интеграций;
   - cache hit ratio;
   - время расчета маршрутов.
2. Добавить структурированные логи с `request_id`, `route_id`, `provider`.
3. Ввести guardrails:
   - лимиты размера графа;
   - fail-fast при деградации провайдера.
4. Алерты на рост ошибок провайдера и времени расчета.

Критерий готовности:
- поведение сервиса прозрачно и управляемо в проде.

## Эпик 9. Тестирование и выпуск

1. Unit-тесты:
   - routing engine;
   - фильтры ограничений;
   - scoring/ranking.
2. Интеграционные тесты:
   - `/routes/search`
   - `/routes/{id}/recalculate`
   - `/routes/batch-recalculate`
3. Контрактные тесты адаптеров провайдеров.
4. Нагрузочный smoke для batch.
5. Обновить `README` и runbook.

Критерий готовности:
- тесты зеленые, SLA/SLO подтверждены, документация обновлена.

## 4. Порядок выполнения (рекомендуемый)

1. Эпик 1 -> Эпик 2.
2. Эпик 3 (Flight MVP) + Эпик 6 (Redis базовый слой).
3. Эпик 4 (routing engine MVP).
4. Эпик 5 (`/routes/search`, затем `/recalculate`, затем `/batch-recalculate`).
5. Эпик 7 (оптимизация batch).
6. Эпик 8 + Эпик 9 перед релизом.

## 5. План по итерациям

### Итерация 1 (MVP поиска)
- Эпики: 1, 2, 3 (только Flight), 4 (базовый алгоритм), 5 (`/routes/search`), 6 (cache-aside).
- Результат: онлайн-поиск top-N маршрутов с кэшированием.

### Итерация 2 (Пересчет и batch)
- Эпики: 5 (`/recalculate`, `/batch-recalculate`), 7.
- Результат: актуализация маршрутов и массовый пересчет.

### Итерация 3 (Production hardening)
- Эпики: 8, 9 + добавление Train/Bus/Ferry адаптеров.
- Результат: эксплуатационная готовность и масштабирование.

## 6. Критический путь

1. Контракт API -> 2. Миграции -> 3. Adapter MVP -> 4. Routing engine -> 5. `/routes/search`.

Задержка любого шага на критическом пути блокирует выпуск MVP.

## 7. Definition of Done (общий)

Задача считается завершенной, если:
1. Реализована бизнес-логика и покрыта тестами.
2. Добавлены логи/метрики для новой функциональности.
3. Обновлены документация и OpenAPI.
4. Нет критических дефектов в smoke/integration проверках.
