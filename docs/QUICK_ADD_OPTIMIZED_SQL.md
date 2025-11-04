# 🚀 Быстрое добавление оптимизированного SQL с планами

## Способ 1: Через интерфейс Vector KB (рекомендуется)

### Шаги:

1. **Запустите сервисы:**
   ```bash
   cd NLSQL
   ./run_stack.sh start core_api
   ./start_vector_kb.sh
   ```

2. **Откройте интерфейс:**
   - http://localhost:8503 (или порт, который показан в терминале)

3. **Перейдите на вкладку "🚀 Оптимизация SQL"**

4. **Заполните форму:**
   - **Вопрос:** `Покажи активных пользователей`
   - **SQL базовый (неоптимизированный):** 
     ```sql
     SELECT * FROM equsers
     ```
   - **SQL оптимизированный:**
     ```sql
     SELECT id, login, email FROM equsers WHERE deleted = FALSE
     ```
   - **Описание улучшения:** `Меньше данных, быстрее выполнение`

5. **Нажмите кнопку:**
   - **"💾 Добавить в векторную базу (с EXPLAIN планом)"**
   
   ⚠️ **НЕ используйте** кнопку "➕ Добавить в JSON" - она только сохраняет в сессию, но не добавляет в БД!

6. **Проверьте результат:**
   - Должно появиться сообщение: "✅ Оптимизированный SQL добавлен в векторную базу!"
   - Должны быть показаны EXPLAIN планы (если API их возвращает)
   - Планы автоматически сгенерированы и сохранены

## Способ 2: Через API напрямую

### Используя curl:

```bash
curl -X POST http://localhost:8000/training/example \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Покажи активных пользователей",
    "sql": "SELECT id, login, email FROM equsers WHERE deleted = FALSE",
    "user_id": "test_user",
    "verified": true,
    "sql_basic": "SELECT * FROM equsers",
    "sql_optimized": "SELECT id, login, email FROM equsers WHERE deleted = FALSE",
    "improvement": "Меньше данных, быстрее выполнение",
    "is_optimized": true
  }'
```

### Используя Python:

```python
import requests
import json

url = "http://localhost:8000/training/example"
data = {
    "question": "Покажи активных пользователей",
    "sql": "SELECT id, login, email FROM equsers WHERE deleted = FALSE",
    "user_id": "test_user",
    "verified": True,
    "sql_basic": "SELECT * FROM equsers",
    "sql_optimized": "SELECT id, login, email FROM equsers WHERE deleted = FALSE",
    "improvement": "Меньше данных, быстрее выполнение",
    "is_optimized": True
}

response = requests.post(url, json=data)
print(response.json())
```

## Способ 3: Через Python скрипт напрямую

```python
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path('.') / "config.env")

from src.vanna.vanna_semantic_fixed import create_semantic_vanna_client

async def add_optimized_sql():
    vanna = create_semantic_vanna_client()
    
    example_id = await vanna.add_question_sql(
        question="Покажи активных пользователей",
        sql="SELECT id, login, email FROM equsers WHERE deleted = FALSE",
        sql_basic="SELECT * FROM equsers",
        improvement="Меньше данных, быстрее выполнение",
        is_optimized=True
    )
    
    print(f"✅ Добавлено с ID: {example_id}")

asyncio.run(add_optimized_sql())
```

## ✅ После добавления

1. **Перегенерируйте эмбеддинги** (если нужно):
   ```bash
   python -m src.tools.generate_embeddings_hf \
     --dsn "$DATABASE_URL" \
     --model "$HF_MODEL_NAME"
   ```

2. **Проверьте, что SQL попал в RAG контекст:**
   ```bash
   # Полный тест гипотезы (рекомендуется)
   python -m src.tools.test_optimized_sql_rag_hypothesis
   
   # Или быстрая проверка
   python -m src.tools.debug_optimized_sql_search
   ```

3. **Проверьте через интерфейс:**
   - http://localhost:8503
   - Вкладка "🔍 Тестирование поиска"
   - Введите: "Покажи активных пользователей"
   - Проверьте, что оптимизированный SQL с планами в результатах

## 🧪 Тестирование

**Полный тест гипотезы:**
```bash
python -m src.tools.test_optimized_sql_rag_hypothesis
```

Этот скрипт:
- ✅ Добавляет оптимизированный SQL с планами
- ✅ Перегенерирует эмбеддинги
- ✅ Проверяет попадание в RAG контекст
- ✅ Проверяет наличие маркировки `[OPTIMIZED SQL]`
- ✅ Проверяет наличие EXPLAIN планов
- ✅ Проверяет формирование промпта с инструкциями

**Результат последнего теста (2025-11-04):** ✅ **ГИПОТЕЗА ПОДТВЕРЖДЕНА**

См. [docs/TEST_RESULTS.md](docs/TEST_RESULTS.md) для детальных результатов.

## 🔍 Проверка в БД

```sql
-- Проверяем, что SQL добавлен с планами
SELECT 
    id,
    metadata->>'question' as question,
    metadata->>'is_optimized' as is_optimized,
    CASE WHEN metadata->>'explain_plan' IS NOT NULL THEN '✅' ELSE '❌' END as plan,
    LEFT(metadata->>'explain_plan', 100) as plan_preview
FROM vanna_vectors
WHERE content_type = 'question_sql'
  AND metadata->>'question' LIKE '%активных пользователей%'
ORDER BY id DESC
LIMIT 3;
```

