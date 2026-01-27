#!/usr/bin/env python3
"""
Brick strength table recognition entry point.
Standard entry for Claude skills.
"""

import sys
from pathlib import Path

# Add scripts directory to path
skill_dir = Path(__file__).parent
sys.path.insert(0, str(skill_dir))

from scripts.batch_process import main

if __name__ == "__main__":
    main()
