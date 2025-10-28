"""
Генератор SQL через нативный Ollama API (не OpenAI-совместимый)
"""
import os
import logging
import requests
from typing import Dict, Any
import psycopg

logger = logging.getLogger(__name__)


class OllamaNativeSQL:
    """Генератор SQL через нативный Ollama API"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализация
        
        Args:
            config: Конфигурация с model, database_url, ollama_url
        """
        if config is None:
            config = {}
        
        self.model = config.get('model', 'phi3:latest')
        self.database_url = config.get('database_url', 'postgresql://postgres:1234@localhost:5432/test_docstructure')
        self.ollama_url = config.get('ollama_url', 'http://localhost:11434')
        self.temperature = config.get('temperature', 0.2)
        
        logger.info(f"✅ OllamaNativeSQL инициализирован (model={self.model})")
    
    def get_table_schema(self) -> str:
        """Получение схемы основных таблиц из БД"""
        try:
            conn = psycopg.connect(self.database_url)
            cur = conn.cursor()
            
            # Основные таблицы
            tables = ['equsers', 'eq_departments', 'tbl_incoming_payments', 
                      'tbl_principal_assignment', 'tbl_business_unit']
            
            schema_parts = []
            for table in tables:
                cur.execute(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public'
                    ORDER BY ordinal_position
                """, (table,))
                
                columns = cur.fetchall()
                if columns:
                    cols_str = ", ".join([f"{col[0]} {col[1]}" for col in columns])
                    schema_parts.append(f"Table {table}: {cols_str}")
            
            cur.close()
            conn.close()
            
            return "\n".join(schema_parts)
        except Exception as e:
            logger.warning(f"Не удалось получить схему БД: {e}")
            return ""
    
    def generate_sql(self, question: str, timeout: int = 60) -> str:
        """
        Генерация SQL через нативный Ollama API
        
        Args:
            question: Вопрос или промпт для генерации SQL
            timeout: Таймаут запроса в секундах
            
        Returns:
            Сгенерированный SQL
        """
        try:
            logger.info(f"🔄 Генерация SQL для: {question[:100]}")
            
            # Получаем схему БД
            schema = self.get_table_schema()
            
            # Короткий промпт для быстрой генерации
            prompt = f"""Generate PostgreSQL SELECT query. Return ONLY SQL, no text.

Schema: equsers(id, name, email), eq_departments(id, name)

Question: {question}
SQL:"""
            
            # Запрос к нативному Ollama API (передаем таймаут явно)
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": 100,
                        "num_ctx": 512
                    }
                },
                timeout=(10, timeout)  # (connect_timeout, read_timeout)
            )
            
            if response.status_code == 200:
                data = response.json()
                sql = data.get('message', {}).get('content', '').strip()
                
                # Очистка SQL от markdown
                sql = sql.replace('```sql', '').replace('```', '').strip()
                
                logger.info(f"✅ SQL сгенерирован: {sql[:100]}")
                return sql
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка генерации SQL через Ollama: {e}")
            raise


def create_ollama_native_sql_generator(config: Dict[str, Any]) -> OllamaNativeSQL:
    """Фабричная функция для создания генератора"""
    return OllamaNativeSQL(config)

