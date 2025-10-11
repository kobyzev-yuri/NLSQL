"""
Подготовка данных для обучения Vanna AI на схеме DocStructureSchema
"""

import json
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class VannaTrainingDataPreparator:
    """
    Класс для подготовки данных обучения Vanna AI
    """
    
    def __init__(self, db_connection=None):
        """
        Инициализация подготовителя данных
        
        Args:
            db_connection: Подключение к базе данных
        """
        self.db_connection = db_connection
        self.training_data = []
    
    def prepare_ddl_statements(self) -> List[str]:
        """
        Подготовка DDL операторов для обучения
        
        Returns:
            List[str]: Список DDL операторов
        """
        ddl_statements = [
            # Основные таблицы пользователей
            """
            CREATE TABLE equsers (
                id UUID PRIMARY KEY,
                login VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                surname VARCHAR(255),
                firstname VARCHAR(255),
                patronymic VARCHAR(255),
                department UUID REFERENCES eq_departments(id),
                accessgranted BOOLEAN DEFAULT true,
                build_in_account BOOLEAN DEFAULT false,
                pass VARCHAR(255),
                refresh_token TEXT,
                validity DATE,
                creationdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT false
            );
            """,
            
            # Отделы
            """
            CREATE TABLE eq_departments (
                id UUID PRIMARY KEY,
                departmentname VARCHAR(255) NOT NULL,
                parentid UUID REFERENCES eq_departments(id),
                description TEXT,
                creationdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT false
            );
            """,
            
            # Группы пользователей
            """
            CREATE TABLE eqgroups (
                id UUID PRIMARY KEY,
                groupname VARCHAR(255) NOT NULL,
                description TEXT,
                ownerid UUID REFERENCES equsers(id),
                creationdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT false
            );
            """,
            
            # Роли системы
            """
            CREATE TABLE eqroles (
                id UUID PRIMARY KEY,
                rolename VARCHAR(255) NOT NULL,
                description TEXT,
                ownerid UUID REFERENCES equsers(id),
                creationdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT false
            );
            """,
            
            # Типы документов
            """
            CREATE TABLE eqdoctypes (
                id UUID PRIMARY KEY,
                doctype VARCHAR(255) NOT NULL,
                category VARCHAR(255),
                tablename VARCHAR(255),
                docurl VARCHAR(500),
                ismanaged BOOLEAN DEFAULT false,
                openmode VARCHAR(10),
                physicaldelete BOOLEAN DEFAULT false,
                creationdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT false
            );
            """,
            
            # Структура документов
            """
            CREATE TABLE eqdocstructure (
                id UUID PRIMARY KEY,
                doctypeid UUID REFERENCES eqdoctypes(id),
                fieldname VARCHAR(255) NOT NULL,
                fieldnamedisplay VARCHAR(255),
                fielddescription TEXT,
                fieldtype INTEGER,
                tablename VARCHAR(255),
                required BOOLEAN DEFAULT false,
                readonly BOOLEAN DEFAULT false,
                uniquefield BOOLEAN DEFAULT false,
                sort INTEGER DEFAULT 0,
                creationdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT false
            );
            """,
            
            # Профили клиентов
            """
            CREATE TABLE tbl_business_unit (
                id UUID PRIMARY KEY,
                business_unit_name VARCHAR(255) NOT NULL,
                inn VARCHAR(20),
                kpp VARCHAR(20),
                ogrn VARCHAR(20),
                legal_address TEXT,
                actual_address TEXT,
                phone VARCHAR(50),
                email VARCHAR(255),
                phone_2 VARCHAR(50),
                website VARCHAR(255),
                creationdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT false
            );
            """,
            
            # Поручения принципала
            """
            CREATE TABLE tbl_principal_assignment (
                id UUID PRIMARY KEY,
                assignment_number VARCHAR(100) NOT NULL,
                assignment_date DATE,
                amount DECIMAL(15,2),
                currency_id UUID,
                status_id UUID,
                business_unit_id UUID REFERENCES tbl_business_unit(id),
                manager_id UUID REFERENCES equsers(id),
                description TEXT,
                creationdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT false
            );
            """,
            
            # Входящие платежи
            """
            CREATE TABLE tbl_incoming_payments (
                id UUID PRIMARY KEY,
                payment_number VARCHAR(100) NOT NULL,
                payment_date DATE,
                amount DECIMAL(15,2),
                currency_id UUID,
                business_unit_id UUID REFERENCES tbl_business_unit(id),
                assignment_id UUID REFERENCES tbl_principal_assignment(id),
                description TEXT,
                creationdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT false
            );
            """,
            
            # Валюты
            """
            CREATE TABLE tbl_currencies (
                id UUID PRIMARY KEY,
                currency_code VARCHAR(3) NOT NULL,
                currency_name VARCHAR(255),
                is_active BOOLEAN DEFAULT true,
                creationdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT false
            );
            """
        ]
        
        return ddl_statements
    
    def prepare_documentation(self) -> str:
        """
        Подготовка документации для обучения
        
        Returns:
            str: Документация на русском языке
        """
        documentation = """
        DocStructureSchema - система управления документами и пользователями
        
        ОСНОВНЫЕ ТАБЛИЦЫ:
        
        1. ПОЛЬЗОВАТЕЛИ И РОЛИ:
        - equsers: пользователи системы (логин, email, отдел, права доступа)
        - eq_departments: отделы организации (название, родительский отдел)
        - eqgroups: группы пользователей (название группы, описание)
        - eqroles: роли системы (название роли, описание)
        
        2. ДОКУМЕНТООБОРОТ:
        - eqdoctypes: типы документов (название типа, категория, связанная таблица)
        - eqdocstructure: структура полей документов (имя поля, тип, обязательность)
        - eqview: представления данных (название представления, условия)
        - eqviewfields: поля представлений (связь с представлением, тип поля)
        
        3. БИЗНЕС-ДАННЫЕ:
        - tbl_business_unit: профили клиентов (название организации, ИНН, КПП, ОГРН)
        - tbl_principal_assignment: поручения принципала (номер, дата, сумма, клиент)
        - tbl_incoming_payments: входящие платежи (номер, дата, сумма, поручение)
        
        4. СПРАВОЧНИКИ:
        - tbl_currencies: валюты (код валюты, название)
        - tbl_countries: страны (код страны, название)
        - tbl_swift: SWIFT коды банков (код, название банка)
        - tbl_bik: БИК коды банков (код, название банка, город)
        
        БИЗНЕС-ЛОГИКА:
        - Каждый пользователь принадлежит отделу (equsers.department → eq_departments.id)
        - Пользователи могут иметь несколько ролей (связь многие-ко-многим)
        - Роли определяют доступ к данным и операциям
        - Поручения связаны с клиентами (tbl_principal_assignment.business_unit_id → tbl_business_unit.id)
        - Платежи связаны с поручениями (tbl_incoming_payments.assignment_id → tbl_principal_assignment.id)
        - Документы имеют настраиваемую структуру полей (eqdocstructure → eqdoctypes)
        
        РОЛЕВАЯ МОДЕЛЬ:
        - admin: полный доступ ко всем данным
        - manager: доступ к данным своего отдела
        - user: доступ только к своим данным
        
        ТИПИЧНЫЕ ЗАПРОСЫ:
        - "Покажи всех пользователей" → SELECT * FROM equsers
        - "Пользователи по отделам" → SELECT u.*, d.departmentname FROM equsers u JOIN eq_departments d ON u.department = d.id
        - "Клиенты с поручениями" → SELECT bu.*, pa.assignment_number FROM tbl_business_unit bu JOIN tbl_principal_assignment pa ON bu.id = pa.business_unit_id
        - "Платежи за период" → SELECT * FROM tbl_incoming_payments WHERE payment_date BETWEEN '2024-01-01' AND '2024-12-31'
        """
        
        return documentation
    
    def prepare_sql_examples(self) -> List[Dict[str, str]]:
        """
        Подготовка примеров SQL запросов для обучения
        
        Returns:
            List[Dict[str, str]]: Список примеров с вопросами и SQL
        """
        examples = [
            {
                "question": "Покажи всех пользователей",
                "sql": "SELECT id, login, email, surname, firstname, department FROM equsers WHERE deleted = false"
            },
            {
                "question": "Список отделов",
                "sql": "SELECT id, departmentname, parentid, description FROM eq_departments WHERE deleted = false"
            },
            {
                "question": "Все клиенты",
                "sql": "SELECT id, business_unit_name, inn, kpp, ogrn, phone, email FROM tbl_business_unit WHERE deleted = false"
            },
            {
                "question": "Пользователи по отделам",
                "sql": """
                SELECT u.login, u.email, u.surname, u.firstname, d.departmentname 
                FROM equsers u 
                LEFT JOIN eq_departments d ON u.department = d.id 
                WHERE u.deleted = false
                """
            },
            {
                "question": "Поручения с клиентами",
                "sql": """
                SELECT pa.assignment_number, pa.assignment_date, pa.amount, 
                       bu.business_unit_name, bu.inn
                FROM tbl_principal_assignment pa
                JOIN tbl_business_unit bu ON pa.business_unit_id = bu.id
                WHERE pa.deleted = false
                """
            },
            {
                "question": "Платежи по клиентам",
                "sql": """
                SELECT bu.business_unit_name, SUM(ip.amount) as total_payments
                FROM tbl_incoming_payments ip
                JOIN tbl_business_unit bu ON ip.business_unit_id = bu.id
                WHERE ip.deleted = false
                GROUP BY bu.id, bu.business_unit_name
                ORDER BY total_payments DESC
                """
            },
            {
                "question": "Пользователи с ролями",
                "sql": """
                SELECT u.login, u.email, r.rolename, r.description
                FROM equsers u
                JOIN user_roles ur ON u.id = ur.user_id
                JOIN eqroles r ON ur.role_id = r.id
                WHERE u.deleted = false
                """
            },
            {
                "question": "Количество пользователей по отделам",
                "sql": """
                SELECT d.departmentname, COUNT(u.id) as user_count
                FROM eq_departments d
                LEFT JOIN equsers u ON d.id = u.department AND u.deleted = false
                WHERE d.deleted = false
                GROUP BY d.id, d.departmentname
                ORDER BY user_count DESC
                """
            },
            {
                "question": "Поручения за последний месяц",
                "sql": """
                SELECT pa.assignment_number, pa.assignment_date, pa.amount, bu.business_unit_name
                FROM tbl_principal_assignment pa
                JOIN tbl_business_unit bu ON pa.business_unit_id = bu.id
                WHERE pa.assignment_date >= CURRENT_DATE - INTERVAL '1 month'
                AND pa.deleted = false
                ORDER BY pa.assignment_date DESC
                """
            },
            {
                "question": "Сумма платежей по месяцам",
                "sql": """
                SELECT DATE_TRUNC('month', payment_date) as month, 
                       SUM(amount) as total_amount
                FROM tbl_incoming_payments
                WHERE deleted = false
                GROUP BY DATE_TRUNC('month', payment_date)
                ORDER BY month DESC
                """
            }
        ]
        
        return examples
    
    def prepare_training_data(self) -> Dict[str, Any]:
        """
        Подготовка всех данных для обучения
        
        Returns:
            Dict[str, Any]: Полный набор данных для обучения
        """
        logger.info("Подготовка данных для обучения Vanna AI")
        
        training_data = {
            "ddl_statements": self.prepare_ddl_statements(),
            "documentation": self.prepare_documentation(),
            "sql_examples": self.prepare_sql_examples(),
            "metadata": {
                "database": "DocStructureSchema",
                "total_tables": 200,
                "main_tables": [
                    "equsers", "eq_departments", "eqgroups", "eqroles",
                    "eqdoctypes", "eqdocstructure", "eqview", "eqviewfields",
                    "tbl_business_unit", "tbl_principal_assignment", "tbl_incoming_payments",
                    "tbl_currencies", "tbl_countries", "tbl_swift", "tbl_bik"
                ],
                "business_domains": [
                    "Пользователи и роли",
                    "Документооборот", 
                    "Бизнес-данные",
                    "Справочники"
                ]
            }
        }
        
        logger.info(f"Подготовлено {len(training_data['ddl_statements'])} DDL операторов")
        logger.info(f"Подготовлено {len(training_data['sql_examples'])} примеров SQL")
        
        return training_data
    
    def save_training_data(self, output_path: str = "./training_data"):
        """
        Сохранение данных обучения в файлы
        
        Args:
            output_path: Путь для сохранения файлов
        """
        training_data = self.prepare_training_data()
        output_dir = Path(output_path)
        output_dir.mkdir(exist_ok=True)
        
        # Сохранение DDL операторов
        with open(output_dir / "ddl_statements.sql", "w", encoding="utf-8") as f:
            for ddl in training_data["ddl_statements"]:
                f.write(ddl + "\n\n")
        
        # Сохранение документации
        with open(output_dir / "documentation.txt", "w", encoding="utf-8") as f:
            f.write(training_data["documentation"])
        
        # Сохранение примеров SQL
        with open(output_dir / "sql_examples.json", "w", encoding="utf-8") as f:
            json.dump(training_data["sql_examples"], f, ensure_ascii=False, indent=2)
        
        # Сохранение метаданных
        with open(output_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(training_data["metadata"], f, ensure_ascii=False, indent=2)
        
        logger.info(f"Данные обучения сохранены в {output_dir}")

def main():
    """
    Основная функция для подготовки данных обучения
    """
    preparator = VannaTrainingDataPreparator()
    preparator.save_training_data()
    print("Данные для обучения Vanna AI подготовлены!")

if __name__ == "__main__":
    main()
