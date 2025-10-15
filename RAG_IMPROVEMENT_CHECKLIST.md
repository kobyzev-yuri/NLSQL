# RAG Improvement Checklist - Tomorrow

## 🚨 Critical Issues to Fix

### 1. DDL Search Not Working
- [ ] **Problem**: Semantic search returns empty DDL results
- [ ] **Impact**: Models invent non-existent tables (`eqorders`, `eqpayments`)
- [ ] **Fix**: Improve embedding quality, add hybrid search
- [ ] **Test**: Verify DDL search finds relevant tables

### 2. Context Overload
- [ ] **Problem**: Too much irrelevant information in prompts
- [ ] **Impact**: Reduced SQL quality, slower generation
- [ ] **Fix**: Smart filtering, context prioritization
- [ ] **Test**: Measure context size reduction (target: 30-50%)

### 3. No Few-Shot Learning
- [ ] **Problem**: No examples for domain-specific queries
- [ ] **Impact**: Generic SQL generation, poor business logic
- [ ] **Fix**: Add few-shot examples, dynamic selection
- [ ] **Test**: Compare SQL quality with/without examples

## 📋 Morning Tasks (9:00-12:00)

### 9:00-10:00: DDL Search Debug
```bash
# Debug semantic search
python3 debug_semantic_search.py

# Check embedding quality
python3 src/tools/generate_embeddings.py --check-quality

# Test DDL retrieval
python3 -c "
from src.vanna.vanna_semantic_fixed import create_semantic_vanna_client
client = create_semantic_vanna_client()
result = client.get_related_ddl('покажи пользователей')
print('DDL Results:', result)
"
```

### 10:00-11:00: Context Analysis
```bash
# Measure current context size
python3 -c "
import asyncio
from src.services.query_service import QueryService

async def analyze_context():
    service = QueryService()
    # Test context size for different questions
    questions = [
        'покажи пользователей',
        'статистика по отделам', 
        'платежи за месяц'
    ]
    for q in questions:
        # Measure context size
        pass

asyncio.run(analyze_context())
"
```

### 11:00-12:00: Baseline Testing
```bash
# Run comprehensive tests
python3 compare_ollama_models.py

# Test current RAG quality
python3 test_semantic_rag.py

# Measure baseline metrics
python3 -c "
# Create baseline metrics
import json
baseline = {
    'ddl_search_success': 0,
    'context_size_avg': 0,
    'sql_quality_avg': 0,
    'response_time_avg': 0
}
with open('baseline_metrics.json', 'w') as f:
    json.dump(baseline, f)
"
```

## 🔧 Afternoon Tasks (13:00-17:00)

### 13:00-14:30: Fix DDL Search
```python
# Improve semantic search in vanna_semantic_fixed.py
class DocStructureVectorDBSemantic:
    async def get_related_ddl(self, question: str) -> List[str]:
        # 1. Normalize question text
        normalized_question = self.normalize_text(question)
        
        # 2. Hybrid search (semantic + lexical)
        semantic_results = await self.semantic_search(normalized_question)
        lexical_results = await self.lexical_search(normalized_question)
        
        # 3. Combine and rank results
        combined_results = self.combine_search_results(
            semantic_results, lexical_results
        )
        
        # 4. Filter by relevance
        relevant_ddl = self.filter_by_relevance(combined_results)
        
        return relevant_ddl
```

### 14:30-16:00: Optimize Context
```python
# Add context optimization to QueryService
class QueryService:
    def optimize_context(self, context_parts: List[str]) -> str:
        # 1. Filter by relevance score
        relevant_parts = self.filter_by_relevance(context_parts)
        
        # 2. Prioritize by source type
        prioritized_parts = self.prioritize_by_source(relevant_parts)
        
        # 3. Limit context size (4000 tokens)
        limited_context = self.limit_context_size(prioritized_parts, 4000)
        
        # 4. Compress redundant information
        compressed_context = self.compress_context(limited_context)
        
        return compressed_context
```

### 16:00-17:00: Add Few-Shot Learning
```python
# Add few-shot examples to prompts
FEW_SHOT_EXAMPLES = {
    'user_queries': [
        {
            'question': 'покажи всех пользователей',
            'sql': 'SELECT * FROM equsers WHERE deleted = FALSE;'
        },
        {
            'question': 'статистика по отделам',
            'sql': 'SELECT d.name, COUNT(u.id) FROM eq_departments d LEFT JOIN equsers u ON d.id = u.department GROUP BY d.name;'
        }
    ],
    'payment_queries': [
        {
            'question': 'платежи по клиентам',
            'sql': 'SELECT u.login, SUM(p.amount) FROM equsers u JOIN payments p ON u.id = p.user_id GROUP BY u.login;'
        }
    ]
}

def get_few_shot_examples(question: str, domain: str) -> str:
    examples = FEW_SHOT_EXAMPLES.get(domain, [])
    return format_examples(examples)
```

## 🧪 Evening Testing (17:00-19:00)

### 17:00-18:00: Comprehensive Testing
```bash
# Test improved RAG
python3 test_semantic_rag.py --improved

# Compare old vs new
python3 -c "
# Run comparison tests
import asyncio
from src.services.query_service import QueryService

async def compare_rag():
    service = QueryService()
    
    # Test questions
    questions = [
        'покажи пользователей',
        'статистика по отделам',
        'платежи за месяц'
    ]
    
    results = {}
    for q in questions:
        # Test old RAG
        old_result = await service.generate_sql_old_rag(q, {})
        
        # Test new RAG  
        new_result = await service.generate_sql_new_rag(q, {})
        
        results[q] = {
            'old': old_result,
            'new': new_result
        }
    
    # Save comparison
    import json
    with open('rag_comparison.json', 'w') as f:
        json.dump(results, f, indent=2)

asyncio.run(compare_rag())
"
```

### 18:00-19:00: Documentation
```bash
# Create improvement report
cat > RAG_IMPROVEMENT_REPORT.md << EOF
# RAG Improvement Report

## Issues Fixed
- [ ] DDL search now finds relevant tables
- [ ] Context size reduced by X%
- [ ] Few-shot examples added
- [ ] Hybrid search implemented

## Metrics Improved
- SQL Quality: X% improvement
- Response Time: X% faster
- Context Relevance: X% more relevant
- Table Accuracy: X% fewer invented tables

## Next Steps
- [ ] Further optimization
- [ ] Additional few-shot examples
- [ ] Performance tuning
EOF
```

## 🎯 Success Criteria

### Must Have (Critical)
- [ ] DDL search returns relevant tables for 80%+ of queries
- [ ] Context size reduced by 30%+ without quality loss
- [ ] Few-shot examples improve SQL quality by 20%+

### Should Have (Important)
- [ ] Response time improved by 20%+
- [ ] Hybrid search implemented
- [ ] Context prioritization working

### Nice to Have (Optional)
- [ ] Caching implemented
- [ ] Advanced chunking strategy
- [ ] Performance monitoring

## 🚨 Emergency Procedures

### If DDL Search Still Broken
```bash
# Fallback to lexical search
export RAG_FALLBACK_MODE=lexical
python3 test_semantic_rag.py
```

### If Context Too Large
```bash
# Reduce context size
export MAX_CONTEXT_TOKENS=2000
python3 test_semantic_rag.py
```

### If Performance Degraded
```bash
# Revert to old RAG
export USE_OLD_RAG=true
python3 test_semantic_rag.py
```

## 📞 Quick Reference

### Key Files to Modify
- `src/vanna/vanna_semantic_fixed.py` - DDL search fixes
- `src/services/query_service.py` - Context optimization
- `src/vanna/optimized_dual_pipeline.py` - Few-shot integration

### Test Commands
```bash
# Quick test
python3 test_semantic_rag.py

# Full benchmark
python3 compare_ollama_models.py

# Debug specific issue
python3 debug_semantic_search.py
```

### Log Locations
- RAG logs: `logs/rag_*.log`
- SQL generation: `logs/sql_generation.log`
- Performance: `logs/performance.log`




