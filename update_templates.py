import sys
import os
from sqlalchemy import create_engine, text

sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from config import settings
    db_url = settings.db_url
except ImportError:
    db_url = "postgresql://postgres.lncfenfoynvbuhxhmdgj:0AbjqFtsjzH4irSw@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres?sslmode=require"

print(f"Connecting to: {db_url}")
engine = create_engine(db_url)

def update_templates():
    with engine.begin() as conn:
        # Update concrete_strength_v1 mapping rules
        print("Updating concrete_strength_v1 template...")
        conn.execute(text("""
            UPDATE template_registry
            SET mapping_rules = '{
                "test_item": "混凝土抗压强度",
                "fields": {
                    "test_result": {
                        "source_keys": [
                            "混凝土强度推定值_MPa", 
                            "混凝土强度推定值（MPa）", 
                            "混凝土强度推定值(MPa)",
                            "混凝土强度推定值", 
                            "回弹推定强度",
                            "混凝土回弹推定强度",
                            "推定值", 
                            "强度推定值",
                            "strength_value", 
                            "test_result"
                        ],
                        "transform": "number"
                    },
                    "test_unit": {
                        "value": "MPa"
                    },
                    "component_type": {
                        "source_keys": ["设计强度等级", "强度等级", "design_grade"],
                        "transform": "string"
                    },
                    "location": {
                        "source_keys": ["检测部位", "部位", "location"],
                        "transform": "string"
                    }
                }
            }'::jsonb
            WHERE template_id = 'concrete_strength_v1';
        """))
        
        # Update rebound_record_v1 mapping rules as well just in case
        print("Updating rebound_record_v1 template...")
        conn.execute(text("""
            UPDATE template_registry
            SET mapping_rules = '{
                "test_item": "混凝土回弹检测-原始记录",
                "fields": {
                     "test_result": { "value": 0 },
                     "test_unit": { "value": "None" },
                     "raw_result": { "source_keys": ["rows"], "transform": "json" },
                     "meta": { "source_keys": ["header"], "transform": "json" }
                }
            }'::jsonb
            WHERE template_id = 'rebound_record_v1';
        """))

        print("Templates updated successfully.")

if __name__ == "__main__":
    update_templates()

