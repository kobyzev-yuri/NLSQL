"""
Адаптеры для работы с различными СУБД
"""

from .base import DatabaseAdapter
from .postgresql_adapter import PostgreSQLAdapter

# Oracle адаптер доступен только локально (не публикуется на GitHub)
try:
    from .oracle_adapter import OracleAdapter
    __all__ = [
        'DatabaseAdapter',
        'PostgreSQLAdapter',
        'OracleAdapter',
    ]
except ImportError:
    # Oracle адаптер недоступен (не установлен драйвер или файл исключен из репозитория)
    __all__ = [
        'DatabaseAdapter',
        'PostgreSQLAdapter',
    ]

