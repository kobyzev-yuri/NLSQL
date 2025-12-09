# 🔍 Анализ медленного запроса: Поиск менеджеров (64 секунды)

## 📝 Проблемный запрос

```sql
SELECT u.id, u.login, u.email, u.surname, u.firstname, u.patronymic, g.groupname 
FROM equsers u 
INNER JOIN eqgroupmembers gm ON gm.userorgroupid = u.id 
INNER JOIN eqgroups g ON gm.groupid = g.id 
WHERE g.groupname LIKE 'Менеджер%' 
AND u.deleted = FALSE 
ORDER BY u.surname, u.firstname;
```

**Время выполнения:** 64 секунды ❌

## 🔎 Причины медленной работы

### 1. **Sequential Scan на eqgroups** (основная проблема)
- Фильтрация `LIKE 'Менеджер%'` выполняется через полное сканирование таблицы
- При большом количестве групп это очень медленно

### 2. **Отсутствие индекса для сортировки**
- `ORDER BY u.surname, u.firstname` требует сортировки всех результатов
- Нет индекса, который покрывает фильтрацию `deleted = FALSE` и сортировку

### 3. **Устаревшая статистика**
- PostgreSQL не знает актуальное распределение данных
- Может выбирать неоптимальные планы выполнения

## ✅ Решения

### Решение 1: Индекс для паттерна LIKE на eqgroups.groupname

```sql
-- Индекс с text_pattern_ops для поддержки LIKE с префиксом
CREATE INDEX IF NOT EXISTS idx_eqgroups_groupname_pattern 
ON eqgroups (groupname text_pattern_ops);
```

**Эффект:** Ускорит поиск групп по паттерну `LIKE 'Менеджер%'` с O(n) до O(log n)

### Решение 2: Составной индекс на equsers

```sql
-- Индекс покрывает фильтрацию deleted = FALSE и сортировку
CREATE INDEX IF NOT EXISTS idx_equsers_deleted_surname_firstname 
ON equsers (deleted, surname, firstname) 
WHERE deleted = FALSE;
```

**Эффект:** 
- Ускорит фильтрацию `deleted = FALSE`
- Ускорит сортировку `ORDER BY surname, firstname`
- Частичный индекс (`WHERE deleted = FALSE`) экономит место

### Решение 3: Обновление статистики

```sql
ANALYZE equsers;
ANALYZE eqgroupmembers;
ANALYZE eqgroups;
```

**Эффект:** PostgreSQL сможет выбирать оптимальные планы выполнения

## 🚀 Применение оптимизаций

### Автоматически через скрипт:

```bash
python3 apply_optimization.py
```

### Вручную через SQL:

```bash
psql "$DATABASE_URL" -f optimize_managers_query.sql
```

## 📊 Ожидаемый результат

После применения оптимизаций:

- **Время выполнения:** с 64 секунд до **< 1 секунды** (улучшение в 64+ раз)
- **Использование индексов:** вместо Sequential Scan будет Index Scan
- **План выполнения:** оптимизированный с использованием индексов

## 🔍 Проверка эффективности

После применения оптимизаций проверьте план выполнения:

```sql
EXPLAIN (ANALYZE, BUFFERS, VERBOSE) 
SELECT u.id, u.login, u.email, u.surname, u.firstname, u.patronymic, g.groupname 
FROM equsers u 
INNER JOIN eqgroupmembers gm ON gm.userorgroupid = u.id 
INNER JOIN eqgroups g ON gm.groupid = g.id 
WHERE g.groupname LIKE 'Менеджер%' 
AND u.deleted = FALSE 
ORDER BY u.surname, u.firstname;
```

**Что проверить:**
- ✅ `Index Scan` вместо `Seq Scan` на eqgroups
- ✅ Использование `idx_eqgroups_groupname_pattern`
- ✅ Использование `idx_equsers_deleted_surname_firstname` для сортировки
- ✅ Время выполнения < 1 секунды

## ⚠️ Важные замечания

1. **Индексы занимают место на диске** - проверьте размер после создания
2. **Индексы замедляют INSERT/UPDATE** - но ускоряют SELECT (в вашем случае это оправдано)
3. **Статистику нужно обновлять регулярно** - можно настроить автообновление через `autovacuum`

## 🔄 Регулярное обслуживание

Рекомендуется настроить автоматическое обновление статистики:

```sql
-- Проверить настройки autovacuum
SHOW autovacuum;
SHOW autovacuum_analyze_scale_factor;

-- При необходимости настроить более частое обновление статистики
ALTER TABLE equsers SET (autovacuum_analyze_scale_factor = 0.05);
ALTER TABLE eqgroupmembers SET (autovacuum_analyze_scale_factor = 0.05);
ALTER TABLE eqgroups SET (autovacuum_analyze_scale_factor = 0.05);
```

## 📈 Мониторинг

После применения оптимизаций мониторьте:

```sql
-- Размер индексов
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_indexes 
WHERE tablename IN ('equsers', 'eqgroupmembers', 'eqgroups')
ORDER BY pg_relation_size(indexrelid) DESC;

-- Использование индексов
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes 
WHERE tablename IN ('equsers', 'eqgroupmembers', 'eqgroups')
ORDER BY idx_scan DESC;
```





