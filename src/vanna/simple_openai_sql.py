#!/usr/bin/env python3
"""
Упрощенная версия генерации SQL с прямым вызовом OpenAI
Без использования Vanna AI (который зависает)
"""

import os
import logging
from pathlib import Path
from openai import OpenAI
import psycopg
from typing import Dict, Any

# Load environment variables from config.env before anything else
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / "config.env", override=True)

logger = logging.getLogger(__name__)

class SimpleOpenAISQL:
    """Простой генератор SQL через OpenAI без Vanna AI"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализация
        
        Args:
            config: Конфигурация с api_key, base_url, model, database_url
        """
        if config is None:
            config = {}
        
        self.api_key = config.get('api_key') or os.getenv('OPENAI_API_KEY')
        self.base_url = config.get('base_url') or os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        self.model = config.get('model', 'gpt-4o')
        self.temperature = config.get('temperature') or float(os.getenv('OPENAI_TEMPERATURE', '0.2'))
        self.database_url = config.get('database_url', 'postgresql://postgres:1234@localhost:5432/test_docstructure')
        
        # Создаем OpenAI клиент
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        logger.info(f"✅ SimpleOpenAISQL инициализирован (model={self.model})")
    
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
                    cols_str = ', '.join([f"{col[0]} ({col[1]})" for col in columns])
                    schema_parts.append(f"Table {table}: {cols_str}")
            
            cur.close()
            conn.close()
            
            return "\n".join(schema_parts)
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения схемы: {e}")
            return "equsers: id, login, firstname, lastname, departmentid\neq_departments: id, departmentname"
    
    def generate_sql(self, question: str, timeout: int = 20) -> str:
        """
        Генерация SQL с прямым вызовом OpenAI
        
        Args:
            question: Вопрос на естественном языке
            timeout: Таймаут в секундах
            
        Returns:
            str: Сгенерированный SQL
        """
        try:
            logger.info(f"🔄 Генерация SQL для: {question}")
            
            # Получаем схему таблиц
            schema = self.get_table_schema()
            
            # Создаем промпт с приоритетом оптимизации
            system_prompt = f"""You are a PostgreSQL expert. Generate ONLY valid, OPTIMIZED SQL code without any explanations.

Database Schema:
{schema}

PERFORMANCE OPTIMIZATION RULES (PRIORITY):
1. Use specific column names instead of SELECT * (minimize data transfer)
2. Add WHERE filters to reduce data volume (filter early)
3. Use INNER JOIN instead of LEFT JOIN when possible (faster execution)
4. Add ORDER BY for logical sorting when needed
5. Consider indexes: filter on indexed columns when possible

Rules:
- Use ONLY tables from the schema above
- Generate SELECT queries
- Use proper JOINs when needed
- Return ONLY SQL code, no markdown, no explanations
- Prefer efficient SQL patterns (specific columns, filters, proper JOINs)
"""
            
            # Вызываем OpenAI с таймаутом
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=500,
                temperature=self.temperature,
                timeout=timeout
            )
            
            sql = response.choices[0].message.content.strip()
            
            # Очищаем от markdown
            if '```sql' in sql:
                sql = sql.split('```sql')[1].split('```')[0].strip()
            elif '```' in sql:
                sql = sql.split('```')[1].split('```')[0].strip()
            
            # Убираем точку с запятой в конце
            if sql.endswith(';'):
                sql = sql[:-1]
            
            logger.info(f"✅ SQL сгенерирован: {sql[:100]}...")
            return sql
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации SQL: {e}")
            raise

def create_simple_sql_generator(config: Dict[str, Any] = None) -> SimpleOpenAISQL:
    """Создание простого генератора SQL"""
    return SimpleOpenAISQL(config)

