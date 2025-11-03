# ✅ Исправленные SQL запросы для добавления в векторную базу

## 📋 Правильные имена колонок

### Таблица `tbl_principal_assignment`:
- ❌ `assignment_number` → ✅ `reg_number` (integer) или `registration_number` (character varying)
- ❌ `amount` → ✅ `total_sum` (double precision) или `rub_sum` (double precision)
- ✅ `creationdatetime` (timestamp) - дата создания

### Таблица `tbl_incoming_payments`:
- ✅ `payment_date` (timestamp) - дата платежа
- ✅ `debit` (double precision) - дебет
- ✅ `credit` (double precision) - кредит
- ✅ `assignment_number` (character varying) - номер поручения (ЕСТЬ!)
- ✅ `client_name` (character varying) - имя клиента

---

## 1️⃣ Поручения за последний месяц

### Базовый SQL:
```sql
SELECT * 
FROM tbl_principal_assignment 
WHERE creationdatetime >= CURRENT_DATE - INTERVAL '1 month'
  AND deleted = false
```

### Оптимизированный SQL:
```sql
SELECT reg_number, total_sum, creationdatetime, name, principal_name
FROM tbl_principal_assignment 
WHERE creationdatetime >= CURRENT_DATE - INTERVAL '1 month' 
  AND deleted = false
ORDER BY creationdatetime DESC
```

**Параметры для интерфейса:**
- **Вопрос**: `Поручения за последний месяц`
- **SQL Basic**: Скопируйте базовый SQL выше
- **SQL Optimized**: Скопируйте оптимизированный SQL выше
- **Improvement**: `Использование ORDER BY и выборка конкретных колонок вместо SELECT * для лучшей производительности. Width уменьшение: ~96.8% (с 17438 до 554 байт)`

**Результаты валидации:**
- ✅ Валидация пройдена (width улучшение: 96.82%)
- Cost: 306.28 → 306.30 (небольшое увеличение из-за ORDER BY)
- Width: 17438 → 554 байт (значительное улучшение!)

---

## 2️⃣ Платежи по отделам

### Базовый SQL:
```sql
SELECT ip.payment_date, ip.client_name, ip.credit, ip.debit
FROM tbl_incoming_payments ip
WHERE ip.deleted = false
  AND ip.payment_date >= CURRENT_DATE - INTERVAL '1 month'
```

### Оптимизированный SQL:
```sql
SELECT 
  d.name AS department_name,
  SUM(ip.credit) AS total_credit,
  SUM(ip.debit) AS total_debit,
  COUNT(*) AS payment_count
FROM tbl_incoming_payments ip
LEFT JOIN equsers u ON ip.owner_id = u.id
LEFT JOIN eq_departments d ON u.department = d.id
WHERE ip.deleted = false
  AND ip.payment_date >= CURRENT_DATE - INTERVAL '1 month'
GROUP BY d.name
ORDER BY total_credit DESC
```

**Параметры для интерфейса:**
- **Вопрос**: `Платежи по отделам`
- **SQL Basic**: Скопируйте базовый SQL выше
- **SQL Optimized**: Скопируйте оптимизированный SQL выше
- **Improvement**: `Группировка по отделам с агрегацией сумм и использованием JOIN вместо множественных запросов`

---

## 3️⃣ Платежи по клиентам

### Базовый SQL:
```sql
SELECT client_name, payment_date, credit, debit
FROM tbl_incoming_payments
WHERE deleted = false
ORDER BY payment_date DESC
```

### Оптимизированный SQL:
```sql
SELECT 
  client_name,
  SUM(credit) AS total_credit,
  SUM(debit) AS total_debit,
  COUNT(*) AS payment_count,
  MAX(payment_date) AS last_payment_date
FROM tbl_incoming_payments
WHERE deleted = false
GROUP BY client_name
ORDER BY total_credit DESC
```

**Параметры для интерфейса:**
- **Вопрос**: `Платежи по клиентам`
- **SQL Basic**: Скопируйте базовый SQL выше
- **SQL Optimized**: Скопируйте оптимизированный SQL выше
- **Improvement**: `Группировка по клиентам с агрегацией для получения итоговых сумм`

---

## 📝 Как использовать

1. Откройте интерфейс Vector KB (обычно на порту 8503 или 8504)
2. Перейдите на вкладку **"Оптимизация SQL"**
3. В разделе **"➕ Добавление пары SQL/SQL optimized"**:
   - Вставьте **Вопрос**
   - Вставьте **SQL Basic** (базовый SQL)
   - Вставьте **SQL Optimized** (оптимизированный SQL)
   - Вставьте **Improvement** (описание улучшения)
4. Нажмите **"💾 Добавить в векторную базу (с EXPLAIN планом)"**
5. Дождитесь генерации EXPLAIN планов и проверки оптимизации

---

## 🔍 Проверка структуры таблиц

Если нужно проверить структуру таблицы:

```bash
# Для tbl_principal_assignment
python src/tools/check_table_columns.py

# Для tbl_incoming_payments
python src/tools/check_payments_table.py
```

---

## ⚠️ Важные замечания

1. **Всегда используйте `deleted = false`** для фильтрации удаленных записей
2. **Проверяйте имена колонок** перед использованием в SQL
3. **Используйте индексы**: `creationdatetime`, `payment_date`, `reg_number` обычно индексированы
4. **Избегайте `SELECT *`** в оптимизированных запросах - указывайте конкретные колонки

