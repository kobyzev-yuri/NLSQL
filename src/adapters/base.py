"""
Базовый интерфейс для адаптеров работы с метаданными БД
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class DatabaseAdapter(ABC):
    """Базовый интерфейс для работы с метаданными БД"""
    
    @abstractmethod
    def get_tables(self) -> List[Dict]:
        """
        Получить список всех таблиц с информацией о комментариях
        
        Returns:
            List[Dict]: Список словарей с ключами:
                - table_name: str
                - table_comment: Optional[str]
        """
        pass
    
    @abstractmethod
    def get_table_columns(self, table_name: str) -> List[Dict]:
        """
        Получить список колонок таблицы с комментариями
        
        Args:
            table_name: Имя таблицы
            
        Returns:
            List[Dict]: Список словарей с ключами:
                - column_name: str
                - data_type: str
                - column_comment: Optional[str]
        """
        pass
    
    @abstractmethod
    def get_ddl(self, table_name: str) -> str:
        """
        Получить DDL таблицы
        
        Args:
            table_name: Имя таблицы
            
        Returns:
            str: DDL скрипт таблицы
        """
        pass
    
    @abstractmethod
    def add_table_comment(self, table_name: str, comment: str) -> Dict:
        """
        Добавить или обновить COMMENT ON TABLE
        
        Args:
            table_name: Имя таблицы
            comment: Текст комментария
            
        Returns:
            Dict: Результат операции
        """
        pass
    
    @abstractmethod
    def add_column_comment(self, table_name: str, column_name: str, comment: str) -> Dict:
        """
        Добавить или обновить COMMENT ON COLUMN
        
        Args:
            table_name: Имя таблицы
            column_name: Имя колонки
            comment: Текст комментария
            
        Returns:
            Dict: Результат операции
        """
        pass
    
    @abstractmethod
    def get_comments_stats(self) -> Dict:
        """
        Получить статистику по комментариям в БД
        
        Returns:
            Dict: Статистика с ключами:
                - total_tables: int
                - tables_with_comments: int
                - tables_without_comments: int
                - total_columns: int
                - columns_with_comments: int
                - columns_without_comments: int
                - coverage_tables: float
                - coverage_columns: float
        """
        pass










