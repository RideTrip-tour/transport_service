# Epic 06: Кэширование (Redis)

## 1. Цель эпика

Снизить нагрузку на внешние провайдеры и уменьшить latency поиска за счет кэширования сегментов.

## 2. Результат эпика

- Подключен Redis.
- Реализован `cache-aside` для сегментов.
- Ключи соответствуют формату `segment:{origin}:{dest}:{date}`.
- TTL сегментов = `3600` секунд.
- Есть базовые cache-метрики.

Артефакты реализации:
- API контракт: [epic-06-api-contract.md](/home/viktor/PycharmProjects/transport-service/docs/epic-06-api-contract.md)
- Sequence-диаграммы: [epic-06-sequence-diagrams.md](/home/viktor/PycharmProjects/transport-service/docs/epic-06-sequence-diagrams.md)
- README эпика: [epic-06-readme.md](/home/viktor/PycharmProjects/transport-service/docs/epic-06-readme.md)

## 3. Задачи

1. Добавить настройки Redis в конфиг и окружение.
2. Реализовать `SegmentCacheRepository`.
3. Определить сериализацию сегментов для Redis.
4. Реализовать `get/set/invalidate` операции.
5. Интегрировать кэш в `search` и `batch-recalculate`.
6. Добавить счетчики hit/miss/stale.
7. Реализовать fallback на direct-provider при отказе Redis.

## 4. Декомпозиция на подзадачи

1. Выбрать формат ключей с учетом `date` и filters.
2. Определить кешируемые поля (без избыточного payload).
3. Реализовать мягкую деградацию при недоступности Redis.
4. Добавить логирование причин cache-miss.

## 5. Зависимости

- Вход: Epic 03 (provider adapters), Epic 05 (`search`, `batch`).
- Выход для эпиков: 5, 7, 8, 9.

## 6. Риски и меры

1. Риск: cache stampede.
   - Мера: lock per key или jitter TTL.
2. Риск: устаревшие данные в кэше.
   - Мера: строгое TTL и forced refresh для recalculate.

## 7. Критерии готовности (DoD)

1. Повторные запросы используют кэш.
2. При отказе Redis сервис остается работоспособным.
3. Видны метрики hit/miss и влияние на latency.
