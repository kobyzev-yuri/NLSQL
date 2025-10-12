# Правила ограничений ролей в NL→SQL системе

## Общие принципы

Система применяет ограничения ролей к SQL запросам на основе роли пользователя. Ограничения должны быть логичными и соответствовать бизнес-логике.

## Роли и их ограничения

### 1. Администратор (admin)
- **Доступ**: Полный доступ ко всем данным
- **Ограничения**: Нет ограничений
- **SQL изменения**: Без изменений

### 2. Менеджер (manager)
- **Доступ**: Доступ к данным своего отдела
- **Ограничения**: 
  - Для таблицы `equsers`: только пользователи отдела IT
  - Для таблицы `tbl_principal_assignment`: только поручения отдела IT
  - Для других таблиц: без ограничений
- **SQL изменения**: 
  - `equsers`: добавляется `WHERE department = (SELECT id FROM eq_departments WHERE departmentname = 'IT')`
  - `tbl_principal_assignment`: добавляется `WHERE department_id = (SELECT id FROM eq_departments WHERE departmentname = 'IT')`

### 3. Пользователь (user)
- **Доступ**: Только свои собственные данные
- **Ограничения**:
  - Для таблицы `equsers`: только свой профиль
  - Для таблицы `tbl_principal_assignment`: только свои поручения
  - Для других таблиц: без ограничений
- **SQL изменения**:
  - `equsers`: добавляется `WHERE login = 'user1'` (конкретный пользователь)
  - `tbl_principal_assignment`: добавляется `WHERE user_id = (SELECT id FROM equsers WHERE login = 'user1')`

## Проблемы в текущей реализации

### 1. Неправильное понимание "своих данных"
- **Текущая ошибка**: Пользователь видит данные других пользователей
- **Правильно**: Пользователь должен видеть только свои данные

### 2. Неправильные ограничения для поручений
- **Текущая ошибка**: `WHERE business_unit_id = (SELECT id FROM tbl_business_unit WHERE name = 'user1_company')`
- **Правильно**: `WHERE user_id = (SELECT id FROM equsers WHERE login = 'user1')`

### 3. Отсутствие связи пользователь-поручения
- **Проблема**: Нет связи между пользователем и его поручениями
- **Решение**: Нужно добавить поле `user_id` в таблицу `tbl_principal_assignment` или использовать другую связь

## Правильные правила ограничений

### Для таблицы equsers (пользователи)
```sql
-- Администратор: без ограничений
SELECT * FROM equsers WHERE deleted = false

-- Менеджер: только свой отдел
SELECT * FROM equsers WHERE deleted = false AND department = (SELECT id FROM eq_departments WHERE departmentname = 'IT')

-- Пользователь: только свой профиль
SELECT * FROM equsers WHERE deleted = false AND login = 'user1'
```

### Для таблицы tbl_principal_assignment (поручения)
```sql
-- Администратор: без ограничений
SELECT * FROM tbl_principal_assignment WHERE assignment_date >= CURRENT_DATE - INTERVAL '1 month'

-- Менеджер: только поручения своего отдела
SELECT * FROM tbl_principal_assignment WHERE assignment_date >= CURRENT_DATE - INTERVAL '1 month' 
AND department_id = (SELECT id FROM eq_departments WHERE departmentname = 'IT')

-- Пользователь: только свои поручения
SELECT * FROM tbl_principal_assignment WHERE assignment_date >= CURRENT_DATE - INTERVAL '1 month' 
AND user_id = (SELECT id FROM equsers WHERE login = 'user1')
```

## Мок-данные для тестирования

### Администратор (admin)
- Видит всех пользователей
- Видит все поручения
- Полный доступ

### Менеджер (manager)
- Видит только пользователей отдела IT
- Видит только поручения отдела IT
- Ограниченный доступ

### Пользователь (user)
- Видит только свой профиль
- Видит только свои поручения
- Минимальный доступ

## Требуемые изменения в коде

1. Исправить логику ограничений для таблицы `tbl_principal_assignment`
2. Добавить правильную связь пользователь-поручения
3. Обновить мок-данные для отражения правильных ограничений
4. Добавить логирование для отладки ограничений

## Примеры правильных ограничений

### Запрос: "Покажи всех пользователей"
- **admin**: Все пользователи
- **manager**: Только пользователи отдела IT
- **user**: Только свой профиль

### Запрос: "Покажи поручения за последний месяц"
- **admin**: Все поручения
- **manager**: Поручения отдела IT
- **user**: Только свои поручения

## Заключение

Ограничения ролей должны быть логичными и соответствовать бизнес-требованиям. Пользователь должен видеть только свои данные, менеджер - данные своего отдела, администратор - все данные.
