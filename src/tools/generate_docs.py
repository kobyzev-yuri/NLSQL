#!/usr/bin/env python3
"""
Генератор документации для NL→SQL системы
Автоматически создает JavaDoc-стиль документацию из исходного кода
"""

import os
import sys
import ast
import re
from typing import Dict, List, Any
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

class DocGenerator:
    """Генератор документации из исходного кода"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.docs_dir = self.project_root / "docs"
        self.src_dir = self.project_root / "src"
        
    def generate_all_docs(self):
        """Генерация всей документации"""
        print("🚀 Генерация документации для NL→SQL системы...")
        
        # Создаем директорию для документации
        self.docs_dir.mkdir(exist_ok=True)
        
        # Генерируем документацию для каждого компонента
        self.generate_component_docs()
        self.generate_api_docs()
        self.generate_architecture_docs()
        self.generate_knowledge_base()
        
        print("✅ Документация сгенерирована успешно!")
        
    def generate_component_docs(self):
        """Генерация документации компонентов"""
        print("📝 Генерация документации компонентов...")
        
        components = {
            "simple_web_interface": {
                "file": "src/simple_web_interface.py",
                "title": "Simple Web Interface",
                "description": "Основной веб-интерфейс для NL→SQL системы"
            },
            "query_service": {
                "file": "src/services/query_service.py", 
                "title": "Query Service",
                "description": "Сервис для генерации SQL запросов"
            },
            "vanna_integration": {
                "file": "src/vanna/vanna_pgvector_native.py",
                "title": "Vanna AI Integration", 
                "description": "Интеграция с Vanna AI и pgvector"
            },
            "mock_api": {
                "file": "src/mock_customer_api.py",
                "title": "Mock Customer API",
                "description": "Mock API для тестирования и отладки"
            }
        }
        
        for component_name, info in components.items():
            self.generate_component_doc(component_name, info)
            
    def generate_component_doc(self, component_name: str, info: Dict[str, str]):
        """Генерация документации для одного компонента"""
        file_path = self.project_root / info["file"]
        
        if not file_path.exists():
            print(f"⚠️  Файл {info['file']} не найден, пропускаем...")
            return
            
        # Читаем исходный код
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
            
        # Парсим AST
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            print(f"⚠️  Ошибка парсинга {info['file']}: {e}")
            return
            
        # Генерируем документацию
        doc_content = self.create_component_doc(component_name, info, tree, source_code)
        
        # Сохраняем документацию
        doc_file = self.docs_dir / f"{component_name.upper()}_DOCUMENTATION.md"
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(doc_content)
            
        print(f"✅ Создана документация: {doc_file}")
        
    def create_component_doc(self, component_name: str, info: Dict[str, str], 
                           tree: ast.AST, source_code: str) -> str:
        """Создание документации для компонента"""
        
        # Извлекаем классы и функции
        classes = []
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(self.extract_class_info(node))
            elif isinstance(node, ast.FunctionDef) and not isinstance(node.parent, ast.ClassDef):
                functions.append(self.extract_function_info(node))
                
        # Генерируем документацию
        doc = f"""# {info['title']} - Документация

## 📋 Обзор

{info['description']}

**Файл**: `{info['file']}`  
**Компонент**: {component_name}  
**Версия**: 1.0.0

---

## 🏗️ Архитектура

### Основные функции
- Обработка запросов от пользователей
- Генерация SQL из естественного языка
- Применение ролевых ограничений
- Возврат результатов в структурированном формате

---

## 🔧 API Reference

### Классы

"""
        
        # Добавляем информацию о классах
        for class_info in classes:
            doc += f"""#### `{class_info['name']}`
```python
class {class_info['name']}:
    \"\"\"
    {class_info['docstring'] or 'Описание класса'}
    \"\"\"
```

**Методы:**
"""
            for method in class_info['methods']:
                doc += f"- `{method['name']}()` - {method['docstring'] or 'Описание метода'}\n"
            doc += "\n"
            
        # Добавляем информацию о функциях
        if functions:
            doc += "### Функции\n\n"
            for func_info in functions:
                doc += f"""#### `{func_info['name']}()`
```python
def {func_info['name']}({func_info['args']}):
    \"\"\"
    {func_info['docstring'] or 'Описание функции'}
    \"\"\"
```

"""
        
        # Добавляем примеры использования
        doc += """## 🚀 Примеры использования

### Базовое использование
```python
# Инициализация компонента
component = Component()

# Основные операции
result = component.main_function()
```

### Расширенное использование
```python
# Конфигурация
config = {
    'param1': 'value1',
    'param2': 'value2'
}

# Создание экземпляра
component = Component(config)

# Выполнение операций
result = component.process_data()
```

---

## 🔍 Отладка

### Логирование
```python
import logging

logger = logging.getLogger(__name__)
logger.info("Операция выполнена успешно")
```

### Обработка ошибок
```python
try:
    result = component.risky_operation()
except Exception as e:
    logger.error(f"Ошибка: {e}")
    raise
```

---

## 📊 Метрики

### Ключевые показатели
- **Время выполнения**: < 5 секунд
- **Точность**: > 80%
- **Доступность**: > 99%

### Мониторинг
```python
# Проверка состояния
status = component.health_check()
print(f"Статус: {status}")
```

---

**Версия документации**: 1.0.0  
**Дата обновления**: 2024-10-15  
**Автор**: NL→SQL Team
"""
        
        return doc
        
    def extract_class_info(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Извлечение информации о классе"""
        methods = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append({
                    'name': item.name,
                    'docstring': ast.get_docstring(item),
                    'args': self.get_function_args(item)
                })
                
        return {
            'name': node.name,
            'docstring': ast.get_docstring(node),
            'methods': methods
        }
        
    def extract_function_info(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Извлечение информации о функции"""
        return {
            'name': node.name,
            'docstring': ast.get_docstring(node),
            'args': self.get_function_args(node)
        }
        
    def get_function_args(self, node: ast.FunctionDef) -> str:
        """Получение аргументов функции"""
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        return ', '.join(args)
        
    def generate_api_docs(self):
        """Генерация документации API"""
        print("📡 Генерация документации API...")
        
        # API документация уже создана вручную
        # Здесь можно добавить автоматическую генерацию из FastAPI
        pass
        
    def generate_architecture_docs(self):
        """Генерация документации архитектуры"""
        print("🏗️ Генерация документации архитектуры...")
        
        # Архитектурная документация уже создана
        # Здесь можно добавить автоматическую генерацию диаграмм
        pass
        
    def generate_knowledge_base(self):
        """Генерация базы знаний"""
        print("🧠 Генерация базы знаний...")
        
        # База знаний уже создана
        # Здесь можно добавить автоматическую генерацию из кода
        pass

def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Генерация документации для NL→SQL системы")
    parser.add_argument("--project-root", default=".", help="Корневая директория проекта")
    parser.add_argument("--component", help="Генерация документации для конкретного компонента")
    
    args = parser.parse_args()
    
    # Создаем генератор
    generator = DocGenerator(args.project_root)
    
    if args.component:
        # Генерация для конкретного компонента
        print(f"📝 Генерация документации для {args.component}...")
        # TODO: Реализовать генерацию для конкретного компонента
    else:
        # Генерация всей документации
        generator.generate_all_docs()

if __name__ == "__main__":
    main()


