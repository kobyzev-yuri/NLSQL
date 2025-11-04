#!/bin/bash
cd /mnt/ai/cnn/sql4A

git add src/vector_kb_interface.py start_vector_kb.sh config.env.example

git commit -m "fix: обновлен Vector KB Interface - исправлены порты, API endpoints и документация

- Исправлена проверка Core API на порту 8000 вместо 3000
- Обновлены все вызовы API на /query endpoint с правильным форматом JSON
- Заменены неработающие локальные ссылки на документацию на ссылки GitHub
- Добавлена ссылка на README.md с настраиваемым GITHUB_REPO_URL
- Упрощен интерфейс документации для лучшей доступности
- Добавлен автоматический выбор свободного порта в start_vector_kb.sh"

echo "✅ Коммит создан"



