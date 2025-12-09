# Проверка таймаутов для GPT-4 во всех сервисах

## Текущее состояние

### 1. Конфигурация (config.env)

```env
OPENAI_TIMEOUT=60  # Таймаут для GPT-4 (секунды)
OLLAMA_TIMEOUT=500  # Таймаут для Ollama (секунды)
```

**Статус:** ✅ Настроено правильно (60 секунд для GPT-4)

---

### 2. Генератор SQL (src/vanna/simple_openai_sql.py)

**Метод:** `generate_sql(question: str, timeout: int = 20)`

**Проблема:** ⚠️ **Дефолтный таймаут 20 секунд** вместо использования значения из config.env

**Код:**
```python
def generate_sql(self, question: str, timeout: int = 20) -> str:
    # ...
    response = self.client.chat.completions.create(
        model=self.model,
        messages=[...],
        timeout=timeout  # Используется переданный таймаут
    )
```

**Рекомендация:** Изменить дефолтное значение на чтение из config.env:
```python
def generate_sql(self, question: str, timeout: int = None) -> str:
    if timeout is None:
        timeout = int(os.getenv('OPENAI_TIMEOUT', '60'))
```

---

### 3. Сервис запросов (src/services/query_service.py)

**Метод:** `generate_sql(question: str, user_context: Dict, timeout: int = None)`

**Статус:** ✅ **Работает правильно**

**Код:**
```python
# Определяем таймаут: из параметра, или из config.env, или по умолчанию
if timeout is None:
    if llm_provider == "ollama":
        timeout = int(os.getenv("OLLAMA_TIMEOUT", "500"))
    else:
        timeout = int(os.getenv("OPENAI_TIMEOUT", "60"))

logger.info(f"⏱️ Используется таймаут: {timeout} сек")

# Передаем таймаут в генератор
sql = await asyncio.to_thread(self.pipeline.generate_sql, smart_question, timeout)
```

**Вывод:** Таймаут правильно берется из config.env и передается в генератор.

---

### 4. API Endpoint (src/api/main.py)

**Endpoint:** `POST /query`

**Проблема:** ⚠️ **Таймаут не передается из запроса**

**Код:**
```python
@app.post("/query", response_model=SQLResponse)
async def generate_sql(request: QueryRequest):
    sql = await query_service.generate_sql(
        question=request.question,
        user_context={...}
        # timeout не передается!
    )
```

**Модель запроса (src/models/requests.py):**
```python
class QueryRequest(BaseModel):
    question: str
    user_id: str
    role: str
    department: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    # timeout отсутствует!
```

**Рекомендация:** Добавить поле `timeout` в `QueryRequest` и передавать его в `query_service.generate_sql()`.

---

### 5. Веб-интерфейс (src/simple_web_interface.py)

**Статус:** ✅ **Таймаут передается через JavaScript**

**Код (JavaScript в HTML):**
```javascript
const timeout = llm_provider === 'ollama' ? 120000 : 90000; // 120 сек для Ollama, 90 сек для GPT-4
```

**Проблема:** ⚠️ Таймаут захардкожен в JavaScript (90 сек для GPT-4), не берется из config.env или из формы.

**Рекомендация:** 
1. Добавить поле ввода таймаута в форму
2. Или брать значение из config.env при загрузке страницы

---

## Итоговая таблица проверки

| Компонент | Статус | Таймаут GPT-4 | Проблема |
|-----------|--------|---------------|----------|
| **config.env** | ✅ | 60 сек | Нет |
| **simple_openai_sql.py** | ⚠️ | Дефолт 20 сек | Дефолт не из config.env |
| **query_service.py** | ✅ | 60 сек (из config.env) | Нет |
| **API endpoint** | ⚠️ | 60 сек (через query_service) | Нельзя задать из запроса |
| **Веб-интерфейс** | ⚠️ | 90 сек (захардкожено) | Не из config.env |

---

## Рекомендации по исправлению

### 1. Исправить дефолтный таймаут в simple_openai_sql.py

```python
def generate_sql(self, question: str, timeout: int = None) -> str:
    """
    Генерация SQL с прямым вызовом OpenAI
    
    Args:
        question: Вопрос на естественном языке ИЛИ готовый промпт от QueryService
        timeout: Таймаут в секундах (если None, берется из OPENAI_TIMEOUT)
    """
    if timeout is None:
        timeout = int(os.getenv('OPENAI_TIMEOUT', '60'))
    
    # ... остальной код
```

### 2. Добавить timeout в QueryRequest

```python
class QueryRequest(BaseModel):
    question: str
    user_id: str
    role: str
    department: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = Field(None, description="Таймаут генерации SQL в секундах")
```

### 3. Передавать timeout в API endpoint

```python
@app.post("/query", response_model=SQLResponse)
async def generate_sql(request: QueryRequest):
    sql = await query_service.generate_sql(
        question=request.question,
        user_context={...},
        timeout=request.timeout  # Передаем таймаут из запроса
    )
```

### 4. Исправить веб-интерфейс

Вариант 1: Добавить поле ввода таймаута
Вариант 2: Брать значение из config.env при загрузке страницы

---

## Выводы

1. ✅ **Основной поток работает:** config.env → query_service → simple_openai_sql (60 сек)
2. ⚠️ **Проблемы:**
   - Дефолтный таймаут в `simple_openai_sql.py` = 20 сек (должен быть 60)
   - Нельзя задать таймаут из API запроса
   - В веб-интерфейсе захардкожен 90 сек вместо использования config.env

3. **Рекомендация:** Исправить все три проблемы для консистентности.

