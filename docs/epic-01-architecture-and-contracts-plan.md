# Epic 01: Архитектурный каркас и контракты

## 1. Цель эпика

Зафиксировать стабильный доменный и API-контур сервиса, чтобы остальные эпики выполнялись без пересмотра базовых контрактов.

## 2. Результат эпика

- Утвержден OpenAPI для `/routes/search`, `/routes/{id}/recalculate`, `/routes/batch-recalculate`.
- Описаны входные/выходные DTO, коды ошибок и единый формат error response.
- Зафиксированы sequence-диаграммы 3 ключевых сценариев.
- Утверждена схема модулей сервиса (API -> Application -> Domain -> Infrastructure).

Артефакты реализации:
- Контракты API: [epic-01-api-contract.md](/home/viktor/PycharmProjects/transport-service/docs/epic-01-api-contract.md)
- Sequence-диаграммы: [epic-01-sequence-diagrams.md](/home/viktor/PycharmProjects/transport-service/docs/epic-01-sequence-diagrams.md)

## 3. Задачи

1. Описать `RouteSearchRequest`, `RouteSearchResponse`, `RouteDTO`, `SegmentDTO`.
2. Описать DTO для пересчета одного маршрута и batch-пересчета.
3. Ввести стандарт ошибки:
   - `code`
   - `message`
   - `details`
   - `trace_id`
4. Зафиксировать коды статусов:
   - `200/202/207`
   - `400/404/409/422`
   - `429/503/504`
5. Подготовить sequence для:
   - online search;
   - recalculate;
   - batch-recalculate.
6. Зафиксировать интерфейсы application-сервисов:
   - `RouteSearchService`
   - `RouteRecalculationService`
   - `BatchRecalculationService`
7. Уточнить boundaries с `gateway`, `location-service`, провайдерами сегментов.
8. Провести review контрактов (архитектор + backend + QA).

## 4. Декомпозиция на подзадачи

1. Черновик OpenAPI и JSON schema.
2. Сверка с требованиями и risks-list.
3. Уточнение неочевидных полей (`preferences`, `top_n`, `max_transfers`).
4. Контракт batch-ответа (`success/failed/skipped`).
5. Финализация и публикация в `docs`.

## 5. Зависимости

- Вход: [transport-service-requirements.md](/home/viktor/PycharmProjects/transport-service/docs/transport-service-requirements.md)
- Выход для эпиков: 2, 3, 4, 5, 6, 7.

## 6. Риски и меры

1. Риск: частые изменения DTO.
   - Мера: ввести policy совместимости и фиксировать breaking changes отдельно.
2. Риск: расплывчатая модель `preferences`.
   - Мера: ограничить MVP-набором полей и enum-значений.

## 7. Критерии готовности (DoD)

1. Контракты согласованы и доступны в `docs`.
2. Все поля и ошибки имеют однозначную спецификацию.
3. Есть трассируемость `требование -> endpoint/DTO`.
