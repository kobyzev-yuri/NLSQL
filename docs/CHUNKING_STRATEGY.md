# 📊 Стратегия разбиения на чанки (Chunking Strategy)

> Документ описывает текущую реализацию разбиения текста на чанки для векторной базы данных, настройки и рекомендации по оптимизации.

## 🔍 Текущее состояние

### Где происходит chunking?

#### 1. **`src/tools/ingest_kb.py`** (наш код)
- **Функция:** `chunk_text(text: str, max_chars: int = 4000)`
- **Размер чанка:** 4000 символов (жестко закодировано)
- **Перекрытия (overlap):** ❌ НЕТ
- **Стратегия:** Простое разбиение по символам без учета границ предложений/слов

**Текущий код:**
```python
def chunk_text(text: str, max_chars: int = 4000) -> List[str]:
    chunks: List[str] = []
    cursor = 0
    n = len(text)
    while cursor < n:
        end = min(cursor + max_chars, n)
        chunks.append(text[cursor:end])
        cursor = end  # Без перекрытия!
    return chunks if chunks else [""]
```

**Используется для:**
- `.sql` файлы → DDL
- `.md`, `.txt` файлы → документация
- `.jsonl` файлы → Q/A пары (каждая строка = один чанк)

#### 2. **`src/vanna/vanna_pgvector_native.py`** (интеграция с vanna-ai)
- **Методы:** `add_ddl()`, `add_documentation()`, `add_question_sql()`
- **Chunking:** ❌ НЕТ - весь контент добавляется как один чанк
- **Проблема:** Большие документы (например, 10MB JSON) сохраняются целиком

### Статистика текущих чанков

```sql
-- Текущее состояние в БД:
SELECT content_type, 
       COUNT(*) as count,
       AVG(LENGTH(content)) as avg_length,
       MIN(LENGTH(content)) as min_length,
       MAX(LENGTH(content)) as max_length,
       COUNT(CASE WHEN LENGTH(content) > 4000 THEN 1 END) as large_chunks
FROM vanna_vectors 
GROUP BY content_type;
```

**Результаты:**
- **documentation:** 4355 чанков, средний размер 3736 символов, **максимум 10MB!** (129 чанков >4000)
- **ddl:** 186 чанков, средний 1757, максимум 8028 (3 чанка >4000)
- **question_sql:** 461 чанков, средний 254, максимум 536 (все <4000)

### Проблемы текущего подхода

1. **Нет перекрытий:**
   - Контекст теряется на границах чанков
   - Если важная информация находится на границе, она может быть разделена

2. **Жестко закодированный размер:**
   - 4000 символов может быть не оптимальным для всех типов контента
   - DDL может быть лучше разбивать по таблицам, а не по символам
   - Документация может требовать разбиения по разделам

3. **Большие чанки:**
   - Некоторые чанки документации превышают 10MB
   - Это затрудняет семантический поиск и увеличивает размер контекста

4. **Нет учета семантических границ:**
   - Разбиение происходит по символам, а не по предложениям/абзацам
   - Может обрезать SQL запросы или предложения

---

## 🎯 Рекомендации по улучшению

### 1. Добавить перекрытия (Overlap)

**Зачем:**
- Сохраняет контекст на границах чанков
- Улучшает качество семантического поиска
- Рекомендуемый overlap: 10-20% от размера чанка

**Пример:**
```python
def chunk_text(text: str, max_chars: int = 4000, overlap: int = 400) -> List[str]:
    chunks: List[str] = []
    cursor = 0
    n = len(text)
    while cursor < n:
        end = min(cursor + max_chars, n)
        chunks.append(text[cursor:end])
        cursor = end - overlap  # Перекрытие!
        if cursor >= n:
            break
    return chunks if chunks else [""]
```

### 2. Разные стратегии для разных типов контента

#### DDL (CREATE TABLE):
- **Рекомендация:** Разбивать по таблицам (один DDL = один чанк)
- **Размер:** Обычно <8000 символов, может быть одним чанком
- **Overlap:** Не нужен (таблицы независимы)

#### Документация:
- **Рекомендация:** Разбивать по абзацам/разделам
- **Размер:** 2000-4000 символов
- **Overlap:** 200-400 символов (10-20%)

#### Q/A пары:
- **Рекомендация:** Один вопрос-ответ = один чанк
- **Размер:** Обычно <1000 символов
- **Overlap:** Не нужен

### 3. Умное разбиение с учетом границ

```python
def smart_chunk_text(text: str, max_chars: int = 4000, overlap: int = 400) -> List[str]:
    """
    Умное разбиение с учетом границ предложений и абзацев
    """
    chunks: List[str] = []
    cursor = 0
    n = len(text)
    
    while cursor < n:
        end = min(cursor + max_chars, n)
        
        # Если не конец текста, пытаемся найти границу предложения
        if end < n:
            # Ищем последнюю точку, перенос строки или конец SQL
            for i in range(end, max(cursor, end - 200), -1):
                if text[i] in ['.', '\n', ';']:
                    end = i + 1
                    break
        
        chunks.append(text[cursor:end])
        cursor = max(cursor + 1, end - overlap)  # Перекрытие с учетом границ
        
        if cursor >= n:
            break
    
    return chunks if chunks else [""]
```

---

## ⚙️ Настройки для вынесения в конфигурацию

### Предлагаемая структура `config.env`:

```bash
# Chunking Configuration
CHUNK_SIZE_DDL=8000              # Размер чанка для DDL (обычно одна таблица)
CHUNK_SIZE_DOCUMENTATION=3000    # Размер чанка для документации
CHUNK_SIZE_QA=1000               # Размер чанка для Q/A (обычно один вопрос-ответ)
CHUNK_OVERLAP_DOCUMENTATION=300  # Перекрытие для документации (10%)
CHUNK_OVERLAP_DDL=0              # Перекрытие для DDL (не нужно)
CHUNK_OVERLAP_QA=0               # Перекрытие для Q/A (не нужно)
CHUNK_USE_SMART_BOUNDARIES=true  # Использовать умное разбиение по границам
```

### Код для чтения настроек:

```python
import os

class ChunkingConfig:
    def __init__(self):
        self.chunk_size_ddl = int(os.getenv('CHUNK_SIZE_DDL', '8000'))
        self.chunk_size_documentation = int(os.getenv('CHUNK_SIZE_DOCUMENTATION', '3000'))
        self.chunk_size_qa = int(os.getenv('CHUNK_SIZE_QA', '1000'))
        self.chunk_overlap_documentation = int(os.getenv('CHUNK_OVERLAP_DOCUMENTATION', '300'))
        self.chunk_overlap_ddl = int(os.getenv('CHUNK_OVERLAP_DDL', '0'))
        self.chunk_overlap_qa = int(os.getenv('CHUNK_OVERLAP_QA', '0'))
        self.use_smart_boundaries = os.getenv('CHUNK_USE_SMART_BOUNDARIES', 'true').lower() == 'true'
```

---

## 📊 Как определить оптимальные параметры

### Метод 1: Анализ текущих данных

```sql
-- Анализ размеров чанков по типам
SELECT 
    content_type,
    COUNT(*) as total_chunks,
    AVG(LENGTH(content)) as avg_length,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY LENGTH(content)) as median_length,
    PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY LENGTH(content)) as p90_length,
    MAX(LENGTH(content)) as max_length,
    COUNT(CASE WHEN LENGTH(content) > 4000 THEN 1 END) as chunks_over_4k,
    COUNT(CASE WHEN LENGTH(content) > 8000 THEN 1 END) as chunks_over_8k
FROM vanna_vectors
GROUP BY content_type;
```

### Метод 2: Тестирование качества поиска

```python
# Скрипт для тестирования разных размеров чанков
def test_chunk_sizes():
    test_sizes = [1000, 2000, 3000, 4000, 5000, 8000]
    test_overlaps = [0, 100, 200, 300, 400, 500]
    
    results = []
    for size in test_sizes:
        for overlap in test_overlaps:
            if overlap >= size:
                continue
            
            # Пересоздать чанки с новыми параметрами
            # Тестировать качество поиска
            # Измерить метрики (precision, recall, relevance)
            
            results.append({
                'size': size,
                'overlap': overlap,
                'quality_score': ...,
                'search_time': ...
            })
    
    # Найти оптимальные параметры
    return max(results, key=lambda x: x['quality_score'])
```

### Метод 3: Рекомендации на основе практики

| Тип контента | Размер чанка | Overlap | Обоснование |
|--------------|--------------|---------|-------------|
| **DDL** | 8000 | 0 | Одна таблица обычно <8000 символов |
| **Документация** | 2000-4000 | 200-400 | Баланс между контекстом и размером |
| **Q/A пары** | 1000 | 0 | Один вопрос-ответ обычно <1000 символов |
| **Большие документы** | 3000 | 300 | Предотвращает слишком большие чанки |

---

## 🚀 План внедрения

### Этап 1: Вынести настройки в конфигурацию
- [ ] Добавить параметры chunking в `config.env.example`
- [ ] Создать класс `ChunkingConfig`
- [ ] Обновить `chunk_text()` для использования настроек

### Этап 2: Добавить перекрытия
- [ ] Реализовать `smart_chunk_text()` с перекрытиями
- [ ] Добавить поддержку разных стратегий для разных типов контента
- [ ] Протестировать на реальных данных

### Этап 3: Улучшить chunking в vanna-ai методах
- [ ] Добавить chunking в `add_documentation()` для больших документов
- [ ] Добавить chunking в `add_ddl()` если DDL слишком большой
- [ ] Сохранить метаданные о связи чанков (chunk_id, total_chunks)

### Этап 4: Создать скрипт оптимизации
- [ ] Скрипт для анализа текущих чанков
- [ ] Скрипт для тестирования разных параметров
- [ ] Скрипт для пересоздания чанков с новыми параметрами

---

## 📝 Примеры использования

### Пример 1: Текущий подход (без настроек)

```python
# В ingest_kb.py
chunks = chunk_text(content, max_chars=4000)  # Жестко закодировано
```

### Пример 2: С настройками

```python
from config import ChunkingConfig

config = ChunkingConfig()

# Для документации
chunks = smart_chunk_text(
    doc_content,
    max_chars=config.chunk_size_documentation,
    overlap=config.chunk_overlap_documentation,
    use_smart_boundaries=config.use_smart_boundaries
)

# Для DDL
chunks = chunk_text(
    ddl_content,
    max_chars=config.chunk_size_ddl,
    overlap=config.chunk_overlap_ddl
)
```

### Пример 3: Разбиение больших документов в add_documentation()

```python
def add_documentation(self, doc: str, **kwargs) -> str:
    config = ChunkingConfig()
    max_size = config.chunk_size_documentation
    
    if len(doc) > max_size:
        # Разбиваем на чанки
        chunks = smart_chunk_text(
            doc,
            max_chars=max_size,
            overlap=config.chunk_overlap_documentation
        )
        
        ids = []
        for i, chunk in enumerate(chunks):
            id = self._add_single_chunk(chunk, 'documentation', {
                'chunk_index': i,
                'total_chunks': len(chunks),
                'original_doc_length': len(doc)
            })
            ids.append(id)
        
        return ids[0]  # Возвращаем первый ID
    else:
        # Один чанк
        return self._add_single_chunk(doc, 'documentation', {})
```

---

## 🔬 Метрики для оценки качества

### Метрики размера чанков:
- **Средний размер:** Должен быть близок к целевому размеру
- **Максимальный размер:** Не должен превышать целевой размер более чем на 20%
- **Распределение:** Большинство чанков должно быть в диапазоне 80-120% от целевого размера

### Метрики качества поиска:
- **Recall@K:** Сколько релевантных чанков найдено в топ-K
- **Precision@K:** Сколько из топ-K релевантны
- **MRR (Mean Reciprocal Rank):** Средний ранг первого релевантного чанка

### Метрики производительности:
- **Время поиска:** Должно быть <100ms для типичных запросов
- **Размер контекста:** Должен быть управляемым для LLM (обычно <32K токенов)

---

**Дата обновления:** 2025-11-04  
**Версия:** 1.0

