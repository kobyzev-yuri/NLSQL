#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ARCHIVE_DIR="$ROOT_DIR/archive/py310/root"

mkdir -p "$ARCHIVE_DIR"

# Move known logs and reports
for f in \
  "$ROOT_DIR"/*.log \
  "$ROOT_DIR"/run_full_architecture.log \
  "$ROOT_DIR"/COMPLEXITY_BENCHMARK_REPORT.md \
  "$ROOT_DIR"/FINAL_MODEL_COMPARISON_REPORT.md \
  "$ROOT_DIR"/PLAN_FOR_TOMORROW.md \
  "$ROOT_DIR"/missing_tables_ddl.sql
do
  [ -e "$f" ] && git mv "$f" "$ARCHIVE_DIR/" || true
done

# Move logs directory
if [ -d "$ROOT_DIR/logs" ]; then
  git mv "$ROOT_DIR/logs" "$ARCHIVE_DIR/" || true
fi

echo "Cleanup complete. Archived to: $ARCHIVE_DIR"

