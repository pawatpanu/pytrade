import sqlite3
import json

conn = sqlite3.connect('signals_demo_433329124.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('''
SELECT id, symbol, direction, score, category, hard_filters_passed, 
       hard_filter_reasons_json, component_scores_json
FROM signals
ORDER BY id DESC
LIMIT 5
''')

print('\n=== LATEST 5 SIGNALS (Debug) ===\n')
for i, row in enumerate(cursor.fetchall(), 1):
    reasons = json.loads(row["hard_filter_reasons_json"] or "[]")
    components = json.loads(row["component_scores_json"] or "{}")
    print(f'{i}. {row["symbol"]} {row["direction"]}: score={row["score"]:.1f}')
    print(f'   Hard Filters Passed: {row["hard_filters_passed"]}')
    print(f'   Reasons: {reasons}')
    if components:
        top = sorted(components.items(), key=lambda x: x[1], reverse=True)[:3]
        print(f'   Top Components: {top}')
    print()

conn.close()
