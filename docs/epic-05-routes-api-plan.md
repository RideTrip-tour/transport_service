# Epic 05: API `/routes/*`

## 1. Цель эпика

Реализовать пользовательские API для поиска и пересчета маршрутов по утвержденным контрактам.

## 2. Результат эпика

- Рабочий `POST /routes/search`.
- Рабочий `POST /routes/{id}/recalculate`.
- Рабочий `POST /routes/batch-recalculate`.
- Унифицированная модель ошибок и валидации.

Артефакты реализации:
- API контракт: [epic-05-api-contract.md](/home/viktor/PycharmProjects/transport-service/docs/epic-05-api-contract.md)
- Sequence-диаграммы: [epic-05-sequence-diagrams.md](/home/viktor/PycharmProjects/transport-service/docs/epic-05-sequence-diagrams.md)
- README эпика: [epic-05-readme.md](/home/viktor/PycharmProjects/transport-service/docs/epic-05-readme.md)

## 3. Задачи

1. Реализовать endpoint `POST /routes/search`.
2. Подключить location validation через `location-service`.
3. Интегрировать flow:
   - cache lookup;
   - provider fetch;
   - routing engine;
   - сохранение `search_history`.
4. Реализовать endpoint `POST /routes/{id}/recalculate`.
5. Реализовать endpoint `POST /routes/batch-recalculate`.
6. Добавить idempotency policy для пересчета.
7. Добавить OpenAPI-документацию и примеры.

## 4. Декомпозиция на подзадачи

1. Валидация `preferences` и `top_n`.
2. Маппинг внутренних ошибок в HTTP-ответы.
3. Добавить correlation-id/trace-id в ответы об ошибках.
4. Подготовить rate-friendly обработку batch (чтение и chunking).

## 5. Зависимости

- Вход: Epic 01, 02, 03, 04, 06.
- Выход для эпиков: 7, 8, 9.

## 6. Риски и меры

1. Риск: высокая латентность `search`.
   - Мера: параллелить provider calls и использовать cache.
2. Риск: тяжелые batch-запросы.
   - Мера: ограничить размер batch и вводить пагинацию/чанки.

## 7. Критерии готовности (DoD)

1. Все 3 endpoint проходят интеграционные тесты.
2. Ошибки и валидации соответствуют контракту.
3. API документировано в OpenAPI.
