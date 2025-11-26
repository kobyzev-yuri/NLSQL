"""
Адаптер для работы с PostgreSQL (обертка над текущим кодом)
"""

import os
import asyncpg
import logging
from typing import List, Dict, Optional
from .base import DatabaseAdapter

logger = logging.getLogger(__name__)


class PostgreSQLAdapter(DatabaseAdapter):
    """Адаптер для PostgreSQL - обертка над текущим кодом из main.py"""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        self.schema = "public"
        if not self.database_url:
            raise ValueError("DATABASE_URL не настроен")
    
    async def _get_connection(self):
        """Получить подключение к PostgreSQL"""
        return await asyncpg.connect(self.database_url)
    
    async def get_tables(self) -> List[Dict]:
        """Получить список всех таблиц с информацией о комментариях"""
        conn = None
        try:
            conn = await self._get_connection()
            
            rows = await conn.fetch("""
                SELECT 
                    t.table_name,
                    COALESCE(obj_description(c.oid, 'pg_class'), '') as table_comment
                FROM information_schema.tables t
                LEFT JOIN pg_class c ON c.relname = t.table_name
                LEFT JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = $1
                WHERE t.table_schema = $1
                AND t.table_type = 'BASE TABLE'
                ORDER BY 
                    CASE WHEN obj_description(c.oid, 'pg_class') IS NULL THEN 0 ELSE 1 END,
                    t.table_name
            """, self.schema)
            
            return [
                {
                    "table_name": row['table_name'],
                    "table_comment": row['table_comment'] if row['table_comment'] else None
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Ошибка получения списка таблиц PostgreSQL: {e}")
            raise
        finally:
            if conn:
                await conn.close()
    
    async def get_table_columns(self, table_name: str) -> List[Dict]:
        """Получить список колонок таблицы с комментариями"""
        conn = None
        try:
            conn = await self._get_connection()
            
            # Получаем OID таблицы
            table_oid = await conn.fetchval("""
                SELECT c.oid
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = $1 AND n.nspname = $2
            """, table_name, self.schema)
            
            if not table_oid:
                raise ValueError(f"Таблица '{table_name}' не найдена")
            
            # Получаем колонки с комментариями
            rows = await conn.fetch("""
                SELECT 
                    c.column_name,
                    c.data_type,
                    COALESCE(col_description($1::oid, c.ordinal_position), '') as column_comment
                FROM information_schema.columns c
                WHERE c.table_schema = $2 
                AND c.table_name = $3
                ORDER BY c.ordinal_position
            """, table_oid, self.schema, table_name)
            
            return [
                {
                    "column_name": row['column_name'],
                    "data_type": row['data_type'],
                    "column_comment": row['column_comment'] if row['column_comment'] else None
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Ошибка получения колонок таблицы {table_name}: {e}")
            raise
        finally:
            if conn:
                await conn.close()
    
    async def get_ddl(self, table_name: str) -> str:
        """Получить DDL таблицы (через pg_dump или системные представления)"""
        # Для PostgreSQL можно использовать pg_dump или системные представления
        # Пока возвращаем заглушку - можно расширить позже
        raise NotImplementedError("DDL extraction для PostgreSQL будет реализовано позже")
    
    async def add_table_comment(self, table_name: str, comment: str) -> Dict:
        """Добавить или обновить COMMENT ON TABLE"""
        conn = None
        try:
            conn = await self._get_connection()
            
            # Проверяем существование таблицы
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_schema = $1 AND table_name = $2
                )
            """, self.schema, table_name)
            
            if not table_exists:
                raise ValueError(f"Таблица '{table_name}' не найдена")
            
            # Экранируем одинарные кавычки
            escaped_comment = comment.replace("'", "''")
            await conn.execute(
                f'COMMENT ON TABLE {self.schema}."{table_name}" IS \'{escaped_comment}\''
            )
            
            logger.info(f"✅ Комментарий добавлен для таблицы {table_name}")
            return {
                "success": True,
                "message": f"Комментарий для таблицы '{table_name}' успешно добавлен",
                "table_name": table_name,
                "comment": comment
            }
        except Exception as e:
            logger.error(f"Ошибка добавления комментария для таблицы {table_name}: {e}")
            raise
        finally:
            if conn:
                await conn.close()
    
    async def add_column_comment(self, table_name: str, column_name: str, comment: str) -> Dict:
        """Добавить или обновить COMMENT ON COLUMN"""
        conn = None
        try:
            conn = await self._get_connection()
            
            # Проверяем существование колонки
            column_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_schema = $1 
                    AND table_name = $2 
                    AND column_name = $3
                )
            """, self.schema, table_name, column_name)
            
            if not column_exists:
                raise ValueError(f"Колонка '{column_name}' в таблице '{table_name}' не найдена")
            
            # Экранируем одинарные кавычки
            escaped_comment = comment.replace("'", "''")
            await conn.execute(
                f'COMMENT ON COLUMN {self.schema}."{table_name}"."{column_name}" IS \'{escaped_comment}\''
            )
            
            logger.info(f"✅ Комментарий добавлен для колонки {table_name}.{column_name}")
            return {
                "success": True,
                "message": f"Комментарий для колонки '{table_name}.{column_name}' успешно добавлен",
                "table_name": table_name,
                "column_name": column_name,
                "comment": comment
            }
        except Exception as e:
            logger.error(f"Ошибка добавления комментария для колонки {table_name}.{column_name}: {e}")
            raise
        finally:
            if conn:
                await conn.close()
    
    async def get_comments_stats(self) -> Dict:
        """Получить статистику по комментариям в БД"""
        conn = None
        try:
            conn = await self._get_connection()
            
            # Статистика по таблицам
            table_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_tables,
                    COUNT(CASE WHEN obj_description(c.oid, 'pg_class') IS NOT NULL THEN 1 END) as tables_with_comments
                FROM information_schema.tables t
                LEFT JOIN pg_class c ON c.relname = t.table_name
                LEFT JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = $1
                WHERE t.table_schema = $1
                AND t.table_type = 'BASE TABLE'
            """, self.schema)
            
            # Статистика по колонкам
            column_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_columns,
                    COUNT(CASE WHEN col_description(c.oid, col.ordinal_position) IS NOT NULL THEN 1 END) as columns_with_comments
                FROM information_schema.columns col
                JOIN information_schema.tables t ON t.table_name = col.table_name AND t.table_schema = col.table_schema
                LEFT JOIN pg_class c ON c.relname = col.table_name
                LEFT JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = $1
                WHERE col.table_schema = $1
                AND t.table_type = 'BASE TABLE'
            """, self.schema)
            
            total_tables = table_stats['total_tables'] or 0
            tables_with_comments = table_stats['tables_with_comments'] or 0
            tables_without_comments = total_tables - tables_with_comments
            
            total_columns = column_stats['total_columns'] or 0
            columns_with_comments = column_stats['columns_with_comments'] or 0
            columns_without_comments = total_columns - columns_with_comments
            
            coverage_tables = (tables_with_comments / total_tables * 100) if total_tables > 0 else 0.0
            coverage_columns = (columns_with_comments / total_columns * 100) if total_columns > 0 else 0.0
            
            return {
                "total_tables": total_tables,
                "tables_with_comments": tables_with_comments,
                "tables_without_comments": tables_without_comments,
                "total_columns": total_columns,
                "columns_with_comments": columns_with_comments,
                "columns_without_comments": columns_without_comments,
                "coverage_tables": round(coverage_tables, 2),
                "coverage_columns": round(coverage_columns, 2)
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики по комментариям: {e}")
            raise
        finally:
            if conn:
                await conn.close()



