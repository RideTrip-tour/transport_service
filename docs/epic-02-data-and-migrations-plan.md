# Epic 02: Данные и миграции

## 1. Цель эпика

Подготовить устойчивую модель хранения маршрутов, сегментов и истории поисков с учетом пересчета и масштабирования.

## 2. Результат эпика

- Новые таблицы `segments`, `routes`, `search_history` с индексами и ограничениями.
- Alembic-миграции `upgrade/downgrade`.
- CRUD-репозитории для чтения/записи.
- Правила versioning маршрутов (`route_version`).

Артефакты реализации:
- API контракт: [epic-02-api-contract.md](/home/viktor/PycharmProjects/transport-service/docs/epic-02-api-contract.md)
- Sequence-диаграммы: [epic-02-sequence-diagrams.md](/home/viktor/PycharmProjects/transport-service/docs/epic-02-sequence-diagrams.md)
- README эпика: [epic-02-readme.md](/home/viktor/PycharmProjects/transport-service/docs/epic-02-readme.md)

## 3. Задачи

1. Спроектировать DDL для `segments`.
2. Спроектировать DDL для `routes`:
   - `segments_snapshot jsonb`
   - `route_version`
   - `recalculated_at`.
3. Спроектировать DDL для `search_history`.
4. Добавить ограничения целостности:
   - проверки дат и неотрицательных цен;
   - обязательные ключи связей.
5. Добавить индексы:
   - по направлению/дате;
   - по пользователю/времени;
   - по `expires_at`.
6. Реализовать миграцию Alembic.
7. Реализовать ORM модели и CRUD.
8. Добавить migration tests (smoke upgrade/downgrade).

## 4. Декомпозиция на подзадачи

1. Таблица `segments`: определить, что хранится как источник истины, а что как snapshot.
2. Таблица `routes`: определить формат `segments_snapshot`.
3. Таблица `search_history`: определить формат `preferences` (`jsonb`).
4. Подготовить rollback-сценарий миграции.
5. Уточнить retention policy для `search_history`.

## 5. Зависимости

- Вход: Epic 01 (контракты и доменная модель).
- Выход для эпиков: 4, 5, 7, 9.

## 6. Риски и меры

1. Риск: неоптимальные индексы под боевые запросы.
   - Мера: предварительный `EXPLAIN` для основных селектов.
2. Риск: рост объема `segments_snapshot`.
   - Мера: лимит размера snapshot и политика архивации.

## 7. Критерии готовности (DoD)

1. Миграции проходят на чистой БД и при обновлении существующей.
2. Индексы подтверждены планами выполнения.
3. CRUD-операции покрыты тестами.
