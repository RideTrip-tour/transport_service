# Epic 07: Batch-пересчет маршрутов

## 1. Цель эпика

Обеспечить массовый пересчет маршрутов с контролируемой нагрузкой на инфраструктуру и внешние API.

## 2. Результат эпика

- Реализован flow batch-пересчета.
- Группировка маршрутов по направлению/дате.
- Частично-успешный итог обработки (`partial success`).
- Поддержка запуска по cron и внешнему триггеру.

Артефакты реализации:
- API контракт: [epic-07-api-contract.md](/home/viktor/PycharmProjects/transport-service/docs/epic-07-api-contract.md)
- Sequence-диаграммы: [epic-07-sequence-diagrams.md](/home/viktor/PycharmProjects/transport-service/docs/epic-07-sequence-diagrams.md)
- README эпика: [epic-07-readme.md](/home/viktor/PycharmProjects/transport-service/docs/epic-07-readme.md)

## 3. Задачи

1. Реализовать orchestration для batch-запроса.
2. Добавить группировку маршрутов для повторного использования сегментов.
3. Настроить bounded concurrency и retry policy.
4. Реализовать статусы по каждому `route_id`:
   - `updated`
   - `unchanged`
   - `failed`.
5. Сохранять audit по результатам batch-запуска.
6. Реализовать ограничения на размер batch и таймаут выполнения.
7. Добавить endpoint/handler для внешнего trigger.

## 4. Декомпозиция на подзадачи

1. Разделить `prepare -> execute -> persist -> report`.
2. Ввести chunking и backpressure.
3. Реализовать retry только для транзиентных ошибок.
4. Добавить дедупликацию одинаковых маршрутов в одном запуске.

## 5. Зависимости

- Вход: Epic 04, 05, 06.
- Выход для эпиков: 8, 9.

## 6. Риски и меры

1. Риск: перегрузка провайдеров.
   - Мера: concurrency limit + группировка + кэш.
2. Риск: слишком долгие batch-операции.
   - Мера: chunk execution + time budget.

## 7. Критерии готовности (DoD)

1. Batch корректно обрабатывает большие списки маршрутов.
2. Ответ содержит детализированные статусы по каждому элементу.
3. Метрики и логи позволяют анализировать деградацию.
