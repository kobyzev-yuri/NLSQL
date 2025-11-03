#!/usr/bin/env python3
"""
Генерация Q/A пар для обучения агента на основе DocStructureSchema
"""

import json
import os
from typing import List, Dict, Any

# Whitelist бизнес-таблиц для обучения агента
BUSINESS_TABLES_WHITELIST = [
    # Пользователи и права
    "equsers",
    "eq_departments", 
    "eqgroups",
    "eqroles",
    
    # Бизнес-данные
    "tbl_business_unit",
    "tbl_principal_assignment", 
    "tbl_incoming_payments",
    "tbl_accounts_document",
    "tbl_personal_account",
    
    # Справочники
    "tbl_currencies",
    "tbl_countries",
    "tbl_swift",
    "tbl_bik",
    "tbl_contract_types",
    "tbl_assignment_types",
    "tbl_payment_statuses"
]

def load_doc_structure_schema() -> Dict[str, Any]:
    """Загружает данные из DocStructureSchema"""
    schema_data = {}
    
    # Загружаем основные файлы
    files_to_load = [
        "EQUsers.json",
        "EQDocTypes.json", 
        "EQDocStructure.json",
        "EQGroups.json",
        "EQRoles.json",
        "EQDepartments.json"
    ]
    
    for filename in files_to_load:
        filepath = f"DocStructureSchema/{filename}"
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    schema_data[filename.replace('.json', '')] = json.load(f)
                print(f"✅ Загружен {filename}")
            except Exception as e:
                print(f"❌ Ошибка загрузки {filename}: {e}")
        else:
            print(f"⚠️ Файл не найден: {filepath}")
    
    return schema_data

def generate_qa_pairs(schema_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Генерирует Q/A пары на основе DocStructureSchema"""
    qa_pairs = []
    
    # 1. Пользователи и отделы
    if "EQUsers" in schema_data:
        qa_pairs.extend([
            {
                "question": "Покажи всех пользователей системы",
                "sql": "SELECT id, login, email, surname, firstname, department, accessgranted FROM equsers WHERE deleted = false"
            },
            {
                "question": "Пользователи с истекшим сроком действия",
                "sql": "SELECT login, email, validity FROM equsers WHERE validity < CURRENT_DATE AND deleted = false"
            },
            {
                "question": "Активные пользователи",
                "sql": "SELECT login, email, surname, firstname FROM equsers WHERE accessgranted = true AND deleted = false"
            },
            {
                "question": "Пользователи с встроенными аккаунтами",
                "sql": "SELECT login, email, build_in_account FROM equsers WHERE build_in_account = true AND deleted = false"
            }
        ])
    
    # 2. Отделы
    if "EQDepartments" in schema_data:
        qa_pairs.extend([
            {
                "question": "Все отделы",
                "sql": "SELECT id, departmentname, parentid, description FROM eq_departments WHERE deleted = false"
            },
            {
                "question": "Пользователи по отделам",
                "sql": "SELECT u.login, u.email, d.departmentname FROM equsers u LEFT JOIN eq_departments d ON u.department = d.id WHERE u.deleted = false"
            },
            {
                "question": "Количество пользователей по отделам",
                "sql": "SELECT d.departmentname, COUNT(u.id) as user_count FROM eq_departments d LEFT JOIN equsers u ON d.id = u.department AND u.deleted = false WHERE d.deleted = false GROUP BY d.id, d.departmentname ORDER BY user_count DESC"
            }
        ])
    
    # 3. Группы и роли
    if "EQGroups" in schema_data:
        qa_pairs.extend([
            {
                "question": "Все группы пользователей",
                "sql": "SELECT id, groupname, description FROM eqgroups WHERE deleted = false"
            }
        ])
    
    if "EQRoles" in schema_data:
        qa_pairs.extend([
            {
                "question": "Все роли в системе",
                "sql": "SELECT id, rolename, description FROM eqroles WHERE deleted = false"
            }
        ])
    
    # 4. Бизнес-данные (на основе EQDocTypes.json)
    if "EQDocTypes" in schema_data:
        # Анализируем типы документов для понимания бизнес-логики
        doc_types = schema_data["EQDocTypes"]
        
        # Ищем таблицы, связанные с бизнес-процессами
        business_tables = []
        for doc_type in doc_types:
            if doc_type.get("tablename") and doc_type["tablename"] in BUSINESS_TABLES_WHITELIST:
                business_tables.append(doc_type["tablename"])
        
        # Генерируем Q/A для найденных бизнес-таблиц
        for table in business_tables:
            if table == "tbl_business_unit":
                qa_pairs.extend([
                    {
                        "question": "Все клиенты системы",
                        "sql": "SELECT id, business_unit_name, inn, kpp, ogrn, phone, email FROM tbl_business_unit WHERE deleted = false"
                    },
                    {
                        "question": "Клиенты с определенным ИНН",
                        "sql": "SELECT business_unit_name, inn, phone FROM tbl_business_unit WHERE inn = ? AND deleted = false"
                    },
                    {
                        "question": "Клиенты с указанным телефоном",
                        "sql": "SELECT business_unit_name, inn, phone FROM tbl_business_unit WHERE phone = ? AND deleted = false"
                    }
                ])
            
            elif table == "tbl_principal_assignment":
                qa_pairs.extend([
                    {
                        "question": "Все поручения",
                        "sql": "SELECT assignment_number, assignment_date, amount, business_unit_id FROM tbl_principal_assignment WHERE deleted = false"
                    },
                    {
                        "question": "Поручения за последний месяц",
                        "sql": "SELECT assignment_number, assignment_date, amount, business_unit_id FROM tbl_principal_assignment WHERE assignment_date >= CURRENT_DATE - INTERVAL '1 month' AND deleted = false ORDER BY assignment_date DESC"
                    },
                    {
                        "question": "Поручения с клиентами",
                        "sql": "SELECT pa.assignment_number, pa.assignment_date, pa.amount, bu.business_unit_name FROM tbl_principal_assignment pa JOIN tbl_business_unit bu ON pa.business_unit_id = bu.id WHERE pa.deleted = false"
                    }
                ])
            
            elif table == "tbl_incoming_payments":
                qa_pairs.extend([
                    {
                        "question": "Все входящие платежи",
                        "sql": "SELECT id, payment_date, amount, business_unit_id FROM tbl_incoming_payments WHERE deleted = false"
                    },
                    {
                        "question": "Платежи по клиентам",
                        "sql": "SELECT bu.business_unit_name, SUM(ip.amount) as total_payments FROM tbl_incoming_payments ip JOIN tbl_business_unit bu ON ip.business_unit_id = bu.id WHERE ip.deleted = false GROUP BY bu.id, bu.business_unit_name ORDER BY total_payments DESC"
                    },
                    {
                        "question": "Сумма платежей по месяцам",
                        "sql": "SELECT DATE_TRUNC('month', payment_date) as month, SUM(amount) as total_amount FROM tbl_incoming_payments WHERE deleted = false GROUP BY DATE_TRUNC('month', payment_date) ORDER BY month DESC"
                    }
                ])
            
            elif table == "tbl_accounts_document":
                qa_pairs.extend([
                    {
                        "question": "Все учетные записи",
                        "sql": "SELECT id, account_number, business_unit_id FROM tbl_accounts_document WHERE deleted = false"
                    }
                ])
    
    return qa_pairs

def save_qa_pairs(qa_pairs: List[Dict[str, str]], filename: str = "generated_qa_pairs.json"):
    """Сохраняет Q/A пары в файл"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
    print(f"✅ Сохранено {len(qa_pairs)} Q/A пар в {filename}")

def main():
    """Основная функция"""
    print("🚀 Генерация Q/A пар на основе DocStructureSchema")
    print("=" * 60)
    
    # Загружаем данные схемы
    print("\n📁 Загрузка DocStructureSchema...")
    schema_data = load_doc_structure_schema()
    
    if not schema_data:
        print("❌ Не удалось загрузить данные схемы")
        return
    
    print(f"✅ Загружено {len(schema_data)} файлов схемы")
    
    # Генерируем Q/A пары
    print("\n🔧 Генерация Q/A пар...")
    qa_pairs = generate_qa_pairs(schema_data)
    
    print(f"✅ Сгенерировано {len(qa_pairs)} Q/A пар")
    
    # Показываем примеры
    print("\n📋 Примеры сгенерированных Q/A пар:")
    for i, qa in enumerate(qa_pairs[:5]):  # Показываем первые 5
        print(f"\n{i+1}. Вопрос: {qa['question']}")
        print(f"   SQL: {qa['sql']}")
    
    if len(qa_pairs) > 5:
        print(f"\n... и еще {len(qa_pairs) - 5} пар")
    
    # Сохраняем результат
    print(f"\n💾 Сохранение результатов...")
    save_qa_pairs(qa_pairs)
    
    print("\n🎯 Рекомендации:")
    print("1. Проверьте сгенерированные Q/A пары")
    print("2. Дополните недостающие бизнес-сценарии")
    print("3. Добавьте специфичные для вашей системы запросы")
    print("4. Используйте эти Q/A пары для обучения агента")

if __name__ == "__main__":
    main()
