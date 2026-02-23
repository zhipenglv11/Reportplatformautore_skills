import sys
sys.path.insert(0, 'backend')

from models.db import get_engine
from sqlalchemy import text

engine = get_engine()
conn = engine.connect()

result = conn.execute(text("""
    SELECT 
        id, 
        test_item, 
        raw_result, 
        confirmed_result 
    FROM professional_data 
    WHERE project_id = '1' 
    AND test_item IN ('brick_table_recognition', 'concrete_table_recognition', 'mortar_table_recognition')
    LIMIT 5
"""))

for i, row in enumerate(result, 1):
    print(f"\n--- Record {i} ---")
    print(f"test_item: {row[1]}")
    print(f"raw_result: {row[2]}")
    print(f"confirmed_result: {row[3]}")
    print(f"raw_result is None: {row[2] is None}")
    print(f"confirmed_result is None: {row[3] is None}")
