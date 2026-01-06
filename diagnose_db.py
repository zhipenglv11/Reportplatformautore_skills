import sys
import os
import json
from sqlalchemy import create_engine, text

# Add backend directory to sys.path to import config
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from config import settings
    db_url = settings.db_url
except ImportError:
    # Fallback if config import fails (e.g. environment variables not set)
    # Assuming standard location or hardcoded for this diagnostic
    db_url = "sqlite:///./backend/data/report_platform.db" 
    # Adjust based on your actual db location logic if needed, 
    # but preferably use the one from config.

print(f"Connecting to database: {db_url}")
engine = create_engine(db_url)

def diagnose():
    with engine.connect() as conn:
        print("\n--- Recent Run Logs (Last 5) ---")
        query_logs = text("""
            SELECT id, run_id, status, stage, error_message, created_at, record_id 
            FROM run_log 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        logs = conn.execute(query_logs).fetchall()
        
        if not logs:
            print("No run logs found.")
        
        for log in logs:
            print(f"ID: {log.id}")
            print(f"Run ID: {log.run_id}")
            print(f"Status: {log.status}")
            print(f"Stage: {log.stage}")
            print(f"Record ID: {log.record_id}")
            print(f"Created At: {log.created_at}")
            print(f"Error: {log.error_message}")
            print("-" * 30)

        print("\n--- Recent Professional Data (Last 5) ---")
        query_data = text("""
            SELECT id, project_id, test_item, test_result, input_fingerprint, created_at
            FROM professional_data
            ORDER BY created_at DESC
            LIMIT 5
        """)
        data = conn.execute(query_data).fetchall()
        
        if not data:
            print("No professional data found.")
            
        for d in data:
            print(f"ID: {d.id}")
            print(f"Project: {d.project_id}")
            print(f"Item: {d.test_item}")
            print(f"Result: {d.test_result}")
            print(f"Fingerprint: {d.input_fingerprint}")
            print(f"Created At: {d.created_at}")
            print("-" * 30)

if __name__ == "__main__":
    diagnose()

