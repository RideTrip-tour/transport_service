# Epic 03: Adapter Layer и интеграции провайдеров

## 1. Цель эпика

Сделать унифицированный слой доступа к внешним провайдерам сегментов без привязки бизнес-логики к конкретному API.

## 2. Результат эпика

- Интерфейс `ProviderAdapter`.
- Реализация `FlightProviderAdapter` как MVP.
- Каркас `Train/Bus/Ferry` адаптеров.
- Унифицированная нормализация provider response -> `Segment`.
- Политики retries/timeouts/fallback.

Артефакты реализации:
- API контракт: [epic-03-api-contract.md](/home/viktor/PycharmProjects/transport-service/docs/epic-03-api-contract.md)
- Sequence-диаграммы: [epic-03-sequence-diagrams.md](/home/viktor/PycharmProjects/transport-service/docs/epic-03-sequence-diagrams.md)
- README эпика: [epic-03-readme.md](/home/viktor/PycharmProjects/transport-service/docs/epic-03-readme.md)

## 3. Задачи

1. Зафиксировать интерфейс `ProviderAdapter`.
2. Реализовать клиент для `FlightProviderAdapter`.
3. Реализовать mapping полей:
   - время отправления/прибытия;
   - стоимость/валюта;
   - provider metadata.
4. Добавить adapter registry/factory.
5. Ввести ограничение конкурентности вызовов к провайдерам.
6. Реализовать retry с backoff.
7. Подготовить заглушки для `Train/Bus/Ferry`.
8. Добавить contract tests на адаптеры.

## 4. Декомпозиция на подзадачи

1. Выделить DTO внешнего провайдера и внутренней модели.
2. Реализовать обработку нестабильных ответов (пустые/частичные данные).
3. Нормализовать таймзоны и валюты.
4. Поддержать trace-id в логах вызова внешнего API.

## 5. Зависимости

- Вход: Epic 01 (контракты), частично Epic 02 (модели хранения).
- Выход для эпиков: 4, 5, 6, 7, 8.

## 6. Риски и меры

1. Риск: неоднородные форматы провайдеров.
   - Мера: strict mapping + валидация обязательных полей.
2. Риск: частая деградация внешнего API.
   - Мера: retry budget, circuit-breaker, graceful fallback.

## 7. Критерии готовности (DoD)

1. `FlightProviderAdapter` возвращает валидный набор сегментов.
2. Ошибки провайдера корректно маппятся в внутренние ошибки.
3. Есть тесты на позитивные и негативные ответы провайдера.
