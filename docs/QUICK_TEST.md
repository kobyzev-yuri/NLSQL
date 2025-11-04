# 🚀 Быстрый тест EXPLAIN планов

## ✅ Да, можно запустить!

```bash
cd NLSQL
python -m src.tools.test_optimized_sql_with_plan
```

Или:

```bash
cd NLSQL
python3 src/tools/test_optimized_sql_with_plan.py
```

## 📋 Что проверяет тест

1. **Оптимизированный SQL с планами:**
   - Добавляет оптимизированный SQL в векторную базу
   - Проверяет, что планы сгенерированы
   - Проверяет, что планы сохранены в `metadata.explain_plan` и `metadata.explain_plan_basic`
   - Проверяет, что планы попадают в RAG контекст

2. **Обычный SQL без планов:**
   - Добавляет обычный SQL (без `is_optimized`)
   - Проверяет, что планы **НЕ** генерируются

## 🔍 Ожидаемый результат

### ✅ Успешно:
```
✅ ПРОШЕЛ: Оптимизированный SQL с планами
✅ ПРОШЕЛ: Обычный SQL без планов

Результат: 2/2 тестов прошли
🎉 Все тесты прошли! Планы генерируются только для оптимизированных SQL.
```

### 📊 Вывод теста включает:
- EXPLAIN план для оптимизированного SQL
- EXPLAIN план для базового SQL
- Проверку сохранения в metadata
- Проверку попадания в RAG контекст

## ⚠️ Требования

1. **База данных должна быть доступна:**
   - `DATABASE_URL` должен быть настроен в `config.env`
   - Таблица `vanna_vectors` должна существовать
   - Пользователь БД должен иметь права на выполнение `EXPLAIN`

2. **Таблица `equsers` должна существовать** (для тестового SQL)

## 🔧 Если тест не проходит

1. **Проверьте подключение к БД:**
   ```bash
   psql "$DATABASE_URL" -c "SELECT 1;"
   ```

2. **Проверьте, что таблица существует:**
   ```sql
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public' AND table_name = 'equsers';
   ```

3. **Проверьте права на EXPLAIN:**
   ```sql
   EXPLAIN SELECT 1;
   ```

## 📝 Альтернативный способ проверки

Если тест не запускается, можно проверить вручную:

1. **Добавьте оптимизированный SQL через интерфейс:**
   - http://localhost:8503
   - Вкладка "🚀 Оптимизация SQL"
   - Кнопка "💾 Добавить в векторную базу (с EXPLAIN планом)"

2. **Проверьте в БД:**
   ```sql
   SELECT 
       id,
       metadata->>'is_optimized' as is_optimized,
       CASE WHEN metadata->>'explain_plan' IS NOT NULL THEN '✅' ELSE '❌' END as plan,
       LEFT(metadata->>'explain_plan', 100) as plan_preview
   FROM vanna_vectors
   WHERE content_type = 'question_sql'
     AND metadata->>'is_optimized' = 'true'
   ORDER BY id DESC
   LIMIT 1;
   ```


