## PostgreSQL Dialect Issues and Fixes

### Problem
Generated SQL contains `public.` schema prefixes and other non-standard PostgreSQL syntax that may cause issues.

### Root Cause
1. **Dialect setting**: Vanna AI has `self.dialect = "postgresql"` but models may still generate schema-prefixed SQL
2. **Training data**: Q/A examples may contain `public.` prefixes from DDL extraction
3. **Model behavior**: LLMs sometimes add schema prefixes even when not needed

### Current Issues in Generated SQL
- `public.equsers` instead of `equsers`
- `public.tbl_incoming_payments` instead of `tbl_incoming_payments`
- Models generate schema-qualified names unnecessarily

### Solutions

#### 1. Update Training Data
Remove `public.` prefixes from Q/A examples:
```python
# In training data preparation
sql = sql.replace('public.', '')
```

#### 2. Add Post-Processing
```python
def clean_sql(sql: str) -> str:
    # Remove unnecessary schema prefixes
    sql = re.sub(r'public\.', '', sql)
    # Fix other PostgreSQL-specific issues
    return sql
```

#### 3. Update Prompts
Add explicit instruction in system prompts:
```
Generate PostgreSQL-compliant SQL without schema prefixes unless necessary.
Use simple table names (equsers, not public.equsers).
```

#### 4. Schema Configuration
Ensure Vanna AI knows the default schema:
```python
vanna.connect_to_postgres(
    host="localhost",
    dbname="test_docstructure", 
    user="postgres",
    password="1234",
    port="5432"
)
```

### Implementation Priority
1. **Immediate**: Add SQL post-processing to remove `public.` prefixes
2. **Short-term**: Clean training data of schema prefixes
3. **Long-term**: Update prompts with explicit PostgreSQL dialect instructions
