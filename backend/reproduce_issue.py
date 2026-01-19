
import sys
from pathlib import Path
import os

# Add backend to path
sys.path.append(str(Path.cwd() / "backend"))

from config import settings
from services.skill_registry.registry import SkillRegistry
from api.declarative_skill_routes import skill_registry, initialize_declarative_skills

print("Initializing Declarative Skills...")
try:
    initialize_declarative_skills()
    print("Initialization done.")
except Exception as e:
    print(f"Initialization FAILED: {e}")

print("Listing Skills...")
try:
    skills = skill_registry.list_skills()
    print("Skills:", skills)
    
    print("\nGetting Skill Info for Declarative Skills...")
    for skill_name in skills['declarative']:
        print(f"Checking {skill_name}...")
        try:
            info = skill_registry.get_skill_info(skill_name)
            print(f"  OK: {info.get('display_name')} ({info.get('version')})")
        except Exception as e:
            print(f"  FAILED: {e}")
            import traceback
            traceback.print_exc()

except Exception as e:
    print(f"List Skills FAILED: {e}")
    import traceback
    traceback.print_exc()
