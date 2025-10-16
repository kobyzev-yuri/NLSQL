#!/usr/bin/env python3
"""
Конфигурации для различных векторных БД в Vanna AI
"""

from typing import Dict, Any
import os

class VectorDBConfigs:
    """Конфигурации для различных векторных БД"""
    
    @staticmethod
    def get_pgvector_config(database_url: str) -> Dict[str, Any]:
        """
        Конфигурация для pgvector (PostgreSQL)
        
        Args:
            database_url: URL подключения к PostgreSQL
            
        Returns:
            Dict с конфигурацией для Vanna AI
        """
        return {
            "vector_db": "postgresql",
            "database_url": database_url,
            "vector_table": "vanna_vectors",
            "vector_dimension": 1536,  # Размерность для OpenAI embeddings
            "distance_metric": "cosine",
            "index_type": "ivfflat",  # или "hnsw"
            "index_lists": 100,
            "index_m": 16,
            "index_ef_construction": 64,
            "index_ef_search": 40
        }
    
    @staticmethod
    def get_faiss_config() -> Dict[str, Any]:
        """
        Конфигурация для FAISS
        
        Returns:
            Dict с конфигурацией для Vanna AI
        """
        return {
            "vector_db": "faiss",
            "vector_dimension": 1536,
            "distance_metric": "cosine",
            "index_type": "IndexFlatIP",  # или "IndexIVFFlat", "IndexHNSWFlat"
            "nlist": 100,
            "nprobe": 10,
            "storage_path": "./faiss_index"
        }
    
    @staticmethod
    def get_chromadb_config() -> Dict[str, Any]:
        """
        Конфигурация для ChromaDB (текущая)
        
        Returns:
            Dict с конфигурацией для Vanna AI
        """
        return {
            "vector_db": "chromadb",
            "collection_name": "docstructure_schema",
            "distance_metric": "cosine",
            "n_results": 5,
            "storage_path": "./chroma_db",
            "embedding_function": "default",
            "timeout": 300  # 5 минут
        }
    
    @staticmethod
    def get_weaviate_config() -> Dict[str, Any]:
        """
        Конфигурация для Weaviate
        
        Returns:
            Dict с конфигурацией для Vanna AI
        """
        return {
            "vector_db": "weaviate",
            "url": "http://localhost:8081",
            "api_key": os.getenv("WEAVIATE_API_KEY"),
            "class_name": "DocStructureSchema",
            "vector_dimension": 1536,
            "distance_metric": "cosine"
        }
    
    @staticmethod
    def get_qdrant_config() -> Dict[str, Any]:
        """
        Конфигурация для Qdrant
        
        Returns:
            Dict с конфигурацией для Vanna AI
        """
        return {
            "vector_db": "qdrant",
            "url": "http://localhost:6333",
            "api_key": os.getenv("QDRANT_API_KEY"),
            "collection_name": "docstructure_schema",
            "vector_size": 1536,
            "distance_metric": "Cosine"
        }

def get_recommended_config(database_url: str, vector_db_type: str = "pgvector") -> Dict[str, Any]:
    """
    Получить рекомендуемую конфигурацию
    
    Args:
        database_url: URL подключения к БД
        vector_db_type: Тип векторной БД ("pgvector", "faiss", "chromadb", "weaviate", "qdrant")
        
    Returns:
        Dict с конфигурацией
    """
    configs = VectorDBConfigs()
    
    if vector_db_type == "pgvector":
        return configs.get_pgvector_config(database_url)
    elif vector_db_type == "faiss":
        return configs.get_faiss_config()
    elif vector_db_type == "chromadb":
        return configs.get_chromadb_config()
    elif vector_db_type == "weaviate":
        return configs.get_weaviate_config()
    elif vector_db_type == "qdrant":
        return configs.get_qdrant_config()
    else:
        raise ValueError(f"Неподдерживаемый тип векторной БД: {vector_db_type}")

# Рекомендации по выбору
RECOMMENDATIONS = {
    "pgvector": {
        "pros": [
            "Родная интеграция с PostgreSQL",
            "ACID транзакции",
            "SQL интерфейс",
            "Простота развертывания",
            "Хорошая производительность"
        ],
        "cons": [
            "Требует установки расширения pgvector",
            "Может быть медленнее для очень больших объемов"
        ],
        "best_for": "Средние проекты с PostgreSQL"
    },
    
    "faiss": {
        "pros": [
            "Очень быстрая",
            "Минимальные зависимости",
            "Локальное хранение",
            "Хорошо для небольших проектов"
        ],
        "cons": [
            "Нет персистентности по умолчанию",
            "Требует дополнительной настройки для продакшена"
        ],
        "best_for": "Быстрое прототипирование и небольшие проекты"
    },
    
    "chromadb": {
        "pros": [
            "Готовая интеграция с Vanna AI",
            "Хорошая документация",
            "Поддержка метаданных"
        ],
        "cons": [
            "Медленная загрузка моделей",
            "Тяжелые зависимости",
            "Проблемы с таймаутами"
        ],
        "best_for": "Когда нужна готовая интеграция"
    }
}
