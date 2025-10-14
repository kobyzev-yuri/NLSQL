#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Источник README. Если есть docs/README_CURRENT.md — используем его, иначе — текущий README.md.
SRC_README="$REPO_DIR/docs/README_CURRENT.md"
DST_README="$REPO_DIR/README.md"

if [ ! -f "$SRC_README" ]; then
  echo "Нет $SRC_README. Обнови его или отредактируй $DST_README вручную."
  exit 1
fi

# На всякий случай проверка на ключи перед коммитом
if rg -n --hidden --no-ignore -i "sk-[A-Za-z0-9-]{20,}" "$SRC_README" >/dev/null 2>&1; then
  echo "Похоже, в README есть секреты (sk-...). Остановлено."
  exit 2
fi

cp "$SRC_README" "$DST_README"
git add "$DST_README"
git commit -m "docs: update README to current run instructions (8000/8080/3000/8501), env-based config"
git push origin main

echo "README обновлён и запушен."
