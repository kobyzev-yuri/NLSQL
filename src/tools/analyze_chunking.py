#!/usr/bin/env python3
"""
Скрипт для анализа текущих чанков и рекомендаций по оптимизации параметров chunking
"""

import os
import sys
import argparse
import asyncio
from typing import Dict, List, Any
from statistics import median

import asyncpg

def get_percentile(values: List[float], percentile: float) -> float:
    """Вычисляет перцентиль для списка значений"""
    sorted_values = sorted(values)
    index = int(len(sorted_values) * percentile / 100)
    return sorted_values[min(index, len(sorted_values) - 1)]

async def analyze_chunks(dsn: str) -> Dict[str, Any]:
    """Анализирует текущие чанки в векторной базе"""
    conn = await asyncpg.connect(dsn)
    try:
        # Получаем статистику по типам контента
        rows = await conn.fetch("""
            SELECT 
                content_type,
                COUNT(*) as total_chunks,
                AVG(LENGTH(content))::int as avg_length,
                MIN(LENGTH(content)) as min_length,
                MAX(LENGTH(content)) as max_length,
                COUNT(CASE WHEN LENGTH(content) > 4000 THEN 1 END) as chunks_over_4k,
                COUNT(CASE WHEN LENGTH(content) > 8000 THEN 1 END) as chunks_over_8k,
                COUNT(CASE WHEN LENGTH(content) > 16000 THEN 1 END) as chunks_over_16k
            FROM vanna_vectors
            GROUP BY content_type
            ORDER BY content_type
        """)
        
        # Получаем детальное распределение размеров
        distribution = {}
        for row in rows:
            content_type = row['content_type']
            lengths = await conn.fetch("""
                SELECT LENGTH(content) as length
                FROM vanna_vectors
                WHERE content_type = $1
                ORDER BY LENGTH(content)
            """, content_type)
            
            lengths_list = [r['length'] for r in lengths]
            
            distribution[content_type] = {
                'total': row['total_chunks'],
                'avg': row['avg_length'],
                'min': row['min_length'],
                'max': row['max_length'],
                'median': median(lengths_list) if lengths_list else 0,
                'p50': median(lengths_list) if lengths_list else 0,
                'p75': get_percentile(lengths_list, 75) if lengths_list else 0,
                'p90': get_percentile(lengths_list, 90) if lengths_list else 0,
                'p95': get_percentile(lengths_list, 95) if lengths_list else 0,
                'p99': get_percentile(lengths_list, 99) if lengths_list else 0,
                'chunks_over_4k': row['chunks_over_4k'],
                'chunks_over_8k': row['chunks_over_8k'],
                'chunks_over_16k': row['chunks_over_16k'],
                'lengths': lengths_list
            }
        
        return distribution
    finally:
        await conn.close()

def recommend_chunk_size(stats: Dict[str, Any], content_type: str) -> Dict[str, Any]:
    """Рекомендует оптимальный размер чанка для типа контента"""
    p90 = stats.get('p90', 0)
    p95 = stats.get('p95', 0)
    max_size = stats.get('max', 0)
    
    # Рекомендуемый размер: 90-95 перцентиль, но не более разумного максимума
    if content_type == 'ddl':
        # DDL обычно разбивается по таблицам
        recommended_size = min(int(p95 * 1.2), 8000)  # Максимум 8000 для DDL
        recommended_overlap = 0  # DDL не нужны перекрытия
    elif content_type == 'documentation':
        # Документация: баланс между контекстом и размером
        recommended_size = min(int(p90 * 1.1), 4000)  # Максимум 4000 для документации
        recommended_overlap = int(recommended_size * 0.1)  # 10% перекрытие
    elif content_type == 'question_sql':
        # Q/A пары обычно маленькие
        recommended_size = min(int(p95 * 1.2), 1000)  # Максимум 1000 для Q/A
        recommended_overlap = 0  # Q/A не нужны перекрытия
    else:
        # По умолчанию
        recommended_size = min(int(p90 * 1.1), 3000)
        recommended_overlap = int(recommended_size * 0.1)
    
    return {
        'recommended_size': recommended_size,
        'recommended_overlap': recommended_overlap,
        'reasoning': _get_reasoning(content_type, stats, recommended_size, recommended_overlap)
    }

def _get_reasoning(content_type: str, stats: Dict[str, Any], size: int, overlap: int) -> str:
    """Генерирует обоснование рекомендаций"""
    p90 = stats.get('p90', 0)
    max_size = stats.get('max', 0)
    chunks_over_current = stats.get('chunks_over_4k', 0)
    total = stats.get('total', 0)
    
    reasons = []
    
    if content_type == 'ddl':
        reasons.append(f"DDL обычно разбивается по таблицам (одна таблица = один чанк)")
        reasons.append(f"90% чанков < {p90} символов, максимум {max_size}")
        if max_size > size:
            reasons.append(f"⚠️  ВНИМАНИЕ: Есть {stats.get('chunks_over_8k', 0)} чанков > 8000 символов - их нужно разбить!")
    elif content_type == 'documentation':
        reasons.append(f"Документация требует баланса между контекстом и размером")
        reasons.append(f"90% чанков < {p90} символов, но есть максимум {max_size} символов")
        if chunks_over_current > 0:
            pct = (chunks_over_current / total * 100) if total > 0 else 0
            reasons.append(f"⚠️  {chunks_over_current} чанков ({pct:.1f}%) превышают 4000 символов")
        if overlap > 0:
            reasons.append(f"Перекрытие {overlap} символов ({overlap*100//size}%) сохранит контекст на границах")
    elif content_type == 'question_sql':
        reasons.append(f"Q/A пары обычно компактные (один вопрос-ответ = один чанк)")
        reasons.append(f"90% чанков < {p90} символов, максимум {max_size}")
    
    return " | ".join(reasons)

def print_analysis(results: Dict[str, Dict[str, Any]]):
    """Выводит результаты анализа"""
    print("\n" + "="*80)
    print("📊 АНАЛИЗ ТЕКУЩИХ ЧАНКОВ В ВЕКТОРНОЙ БАЗЕ")
    print("="*80)
    
    for content_type, stats in results.items():
        print(f"\n📋 Тип контента: {content_type}")
        print("-" * 80)
        print(f"  Всего чанков:        {stats['total']:,}")
        print(f"  Средний размер:      {stats['avg']:,} символов")
        print(f"  Медианный размер:    {stats['median']:,.0f} символов")
        print(f"  Минимальный размер:  {stats['min']:,} символов")
        print(f"  Максимальный размер: {stats['max']:,} символов")
        print(f"\n  Перцентили:")
        print(f"    P50 (медиана):     {stats['p50']:,.0f} символов")
        print(f"    P75:               {stats['p75']:,.0f} символов")
        print(f"    P90:               {stats['p90']:,.0f} символов")
        print(f"    P95:               {stats['p95']:,.0f} символов")
        print(f"    P99:               {stats['p99']:,.0f} символов")
        
        print(f"\n  Чанки превышающие пороги:")
        print(f"    > 4000 символов:   {stats['chunks_over_4k']:,} ({stats['chunks_over_4k']/stats['total']*100:.1f}%)")
        print(f"    > 8000 символов:   {stats['chunks_over_8k']:,} ({stats['chunks_over_8k']/stats['total']*100:.1f}%)")
        print(f"    > 16000 символов:  {stats['chunks_over_16k']:,} ({stats['chunks_over_16k']/stats['total']*100:.1f}%)")
        
        # Рекомендации
        recommendations = recommend_chunk_size(stats, content_type)
        print(f"\n  💡 Рекомендации:")
        print(f"    Размер чанка:      {recommendations['recommended_size']:,} символов")
        print(f"    Перекрытие:        {recommendations['recommended_overlap']:,} символов")
        print(f"    Обоснование:       {recommendations['reasoning']}")

def generate_config_example(results: Dict[str, Dict[str, Any]]):
    """Генерирует пример конфигурации на основе анализа"""
    print("\n" + "="*80)
    print("⚙️  РЕКОМЕНДУЕМАЯ КОНФИГУРАЦИЯ (для config.env)")
    print("="*80)
    print("\n# Chunking Configuration (автоматически сгенерировано)")
    
    for content_type, stats in results.items():
        recommendations = recommend_chunk_size(stats, content_type)
        
        if content_type == 'ddl':
            print(f"CHUNK_SIZE_DDL={recommendations['recommended_size']}")
            print(f"CHUNK_OVERLAP_DDL={recommendations['recommended_overlap']}")
        elif content_type == 'documentation':
            print(f"CHUNK_SIZE_DOCUMENTATION={recommendations['recommended_size']}")
            print(f"CHUNK_OVERLAP_DOCUMENTATION={recommendations['recommended_overlap']}")
        elif content_type == 'question_sql':
            print(f"CHUNK_SIZE_QA={recommendations['recommended_size']}")
            print(f"CHUNK_OVERLAP_QA={recommendations['recommended_overlap']}")
    
    print("\nCHUNK_USE_SMART_BOUNDARIES=true")
    print("\n# Примечание: Эти значения основаны на анализе текущих данных")
    print("# При необходимости скорректируйте вручную")

async def main():
    parser = argparse.ArgumentParser(
        description="Анализ текущих чанков и рекомендации по оптимизации"
    )
    parser.add_argument(
        "--dsn",
        default=os.getenv("DATABASE_URL", ""),
        help="PostgreSQL DSN (или используйте DATABASE_URL env var)"
    )
    parser.add_argument(
        "--generate-config",
        action="store_true",
        help="Сгенерировать пример конфигурации"
    )
    
    args = parser.parse_args()
    
    if not args.dsn:
        print("❌ Ошибка: Укажите DSN через --dsn или установите DATABASE_URL", file=sys.stderr)
        return 1
    
    try:
        results = await analyze_chunks(args.dsn)
        print_analysis(results)
        
        if args.generate_config:
            generate_config_example(results)
        
        return 0
    except Exception as e:
        print(f"❌ Ошибка: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

