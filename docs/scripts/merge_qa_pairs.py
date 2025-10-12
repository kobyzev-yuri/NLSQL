#!/usr/bin/env python3
"""
Скрипт для объединения всех Q/A пар в один файл
"""

import json
import os
from typing import List, Dict, Any

def load_qa_pairs(filename: str) -> List[Dict[str, Any]]:
    """Загружает Q/A пары из файла"""
    if not os.path.exists(filename):
        print(f"⚠️ Файл не найден: {filename}")
        return []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ Загружено {len(data)} Q/A пар из {filename}")
        return data
    except Exception as e:
        print(f"❌ Ошибка загрузки {filename}: {e}")
        return []

def merge_qa_pairs():
    """Объединяет все Q/A пары в один файл"""
    print("🔄 Объединение Q/A пар...")
    
    all_qa_pairs = []
    
    # 1. Загружаем существующие SQL примеры
    existing_examples = load_qa_pairs('training_data/sql_examples.json')
    for example in existing_examples:
        example['source'] = 'existing_examples'
        example['category'] = example.get('category', 'Общие')
        example['complexity'] = example.get('complexity', 2)
        example['description'] = example.get('description', 'Существующий пример')
    
    # 2. Загружаем сгенерированные Q/A пары
    generated_qa = load_qa_pairs('generated_qa_pairs.json')
    for qa in generated_qa:
        qa['source'] = 'generated_from_schema'
        qa['category'] = qa.get('category', 'Сгенерированные')
        qa['complexity'] = qa.get('complexity', 2)
        qa['description'] = qa.get('description', 'Сгенерировано из схемы')
    
    # 3. Объединяем все пары
    all_qa_pairs.extend(existing_examples)
    all_qa_pairs.extend(generated_qa)
    
    # 4. Добавляем уникальные ID
    for i, qa in enumerate(all_qa_pairs):
        qa['id'] = i + 1
    
    # 5. Группируем по категориям
    categories = {}
    for qa in all_qa_pairs:
        category = qa.get('category', 'Неизвестно')
        if category not in categories:
            categories[category] = []
        categories[category].append(qa)
    
    # 6. Сохраняем объединенный файл
    output_filename = 'merged_qa_pairs.json'
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(all_qa_pairs, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Сохранено {len(all_qa_pairs)} Q/A пар в {output_filename}")
    
    # 7. Выводим статистику
    print("\n📊 Статистика по категориям:")
    for category, pairs in categories.items():
        print(f"   {category}: {len(pairs)} пар")
    
    print(f"\n📈 Общая статистика:")
    print(f"   Всего Q/A пар: {len(all_qa_pairs)}")
    print(f"   Категорий: {len(categories)}")
    print(f"   Источников: {len(set(qa['source'] for qa in all_qa_pairs))}")
    
    # 8. Создаем файл для заказчика с шаблонами
    create_customer_template(categories)
    
    return all_qa_pairs

def create_customer_template(categories: Dict[str, List[Dict]]):
    """Создает шаблон для заказчика с недостающими категориями"""
    
    # Определяем недостающие категории
    required_categories = {
        'Отделы': 5,
        'Роли': 6, 
        'Группы': 4,
        'Аналитика': 8,
        'Справочники': 5,
        'Сложные запросы': 4
    }
    
    missing_categories = {}
    for category, needed_count in required_categories.items():
        current_count = len(categories.get(category, []))
        if current_count < needed_count:
            missing_categories[category] = needed_count - current_count
    
    if missing_categories:
        template = {
            "missing_categories": missing_categories,
            "templates": {}
        }
        
        # Создаем шаблоны для недостающих категорий
        for category, needed_count in missing_categories.items():
            template["templates"][category] = []
            
            if category == 'Отделы':
                template["templates"][category] = [
                    {
                        "question": "Покажи все отделы с их иерархией",
                        "sql": "SELECT id, departmentname, parentid, description FROM eq_departments WHERE deleted = false ORDER BY parentid, departmentname",
                        "category": "Отделы",
                        "complexity": 2,
                        "description": "Иерархическая структура отделов"
                    },
                    {
                        "question": "Количество пользователей в каждом отделе",
                        "sql": "SELECT d.departmentname, COUNT(u.id) as user_count FROM eq_departments d LEFT JOIN equsers u ON d.id = u.department AND u.deleted = false WHERE d.deleted = false GROUP BY d.id, d.departmentname",
                        "category": "Отделы", 
                        "complexity": 3,
                        "description": "Статистика пользователей по отделам"
                    }
                ]
            elif category == 'Роли':
                template["templates"][category] = [
                    {
                        "question": "Все роли в системе",
                        "sql": "SELECT id, rolename, description FROM eqroles WHERE deleted = false",
                        "category": "Роли",
                        "complexity": 1,
                        "description": "Список всех ролей"
                    },
                    {
                        "question": "Пользователи с определенной ролью",
                        "sql": "SELECT u.login, u.email, r.rolename FROM equsers u JOIN user_roles ur ON u.id = ur.user_id JOIN eqroles r ON ur.role_id = r.id WHERE r.rolename = ? AND u.deleted = false",
                        "category": "Роли",
                        "complexity": 3,
                        "description": "Пользователи с конкретной ролью"
                    }
                ]
            # Добавляем шаблоны для других категорий...
        
        # Сохраняем шаблон
        with open('customer_qa_template.json', 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        
        print(f"\n📋 Создан шаблон для заказчика: customer_qa_template.json")
        print(f"   Недостающие категории: {missing_categories}")

def main():
    """Основная функция"""
    print("🔄 Объединение всех Q/A пар")
    print("=" * 40)
    
    merged_pairs = merge_qa_pairs()
    
    print("\n🎯 Следующие шаги:")
    print("1. Проверьте merged_qa_pairs.json")
    print("2. Отправьте customer_qa_template.json заказчику")
    print("3. Дождитесь дополнений от заказчика")
    print("4. Обновите обучение агента")

if __name__ == "__main__":
    main()
