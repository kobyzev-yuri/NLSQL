## Пользовательское руководство (NL→SQL)

### Требования
- Python 3.10+
- PostgreSQL 14+ с БД `test_docstructure`
- Переменные окружения из `config.env`

### Быстрый старт
```bash
cd /mnt/ai/cnn/sql4A
./start_all_services.sh
# UI:
#  - http://localhost:3000  (Simple UI)
#  - http://localhost:8501  (Streamlit UI)
#  - http://localhost:8503  (Vector KB)
# API:
#  - http://localhost:8000/docs
```

### Основные сценарии
- Генерация SQL: в UI введите вопрос, выберите роль (admin/manager/user), выполните.
- Обучение RAG: интерфейс Vector KB (http://localhost:8503) — проверка поиска, добавление Q/A.
- Проверка здоровья: `curl http://localhost:8000/health`.

### Конфигурация
Отредактируйте `config.env` и перезапустите сервисы.

### Типичные вопросы
- «Покажи всех пользователей» → построит SELECT по `equsers` с ролевыми фильтрами.
- «Платежи за последний месяц» → SELECT из `tbl_incoming_payments` с датой.

### Отладка
Логи в каталоге `logs/`. Быстрые команды:
```bash
./run_stack.sh status
tail -f logs/core_api_8000.err
```

### Частые проблемы
- Отсутствует API-ключ: проверьте `OPENAI_API_KEY`/`OPENAI_BASE_URL`.
- Нет соединения с БД: проверьте `DATABASE_URL` и доступность PostgreSQL.


