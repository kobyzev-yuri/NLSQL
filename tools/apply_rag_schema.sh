#!/usr/bin/env bash
set -euo pipefail

# Apply RAG schema into the target Postgres database.
# Usage:
#   CUSTOMER_DB_DSN=postgresql://postgres:1234@localhost:5432/test_docstructure \
#   bash tools/apply_rag_schema.sh

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCHEMA_SQL="$REPO_DIR/src/tools/rag_schema.sql"
DSN="${CUSTOMER_DB_DSN:-}"

if ! command -v psql >/dev/null 2>&1; then
  echo "psql not found. Please install PostgreSQL client tools." >&2
  exit 1
fi

if [ -z "$DSN" ]; then
  echo "CUSTOMER_DB_DSN is not set. Example: postgresql://postgres:1234@localhost:5432/test_docstructure" >&2
  exit 2
fi

if [ ! -f "$SCHEMA_SQL" ]; then
  echo "Schema file not found: $SCHEMA_SQL" >&2
  exit 3
fi

echo "Applying RAG schema to: $DSN"
psql "$DSN" -v ON_ERROR_STOP=1 -f "$SCHEMA_SQL"
echo "Done."



