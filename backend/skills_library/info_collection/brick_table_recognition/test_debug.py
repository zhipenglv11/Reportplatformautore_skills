#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug script to capture the real exception"""

import sys
import traceback

# Add skill dir to path
sys.path.insert(0, '.')

try:
    from scripts import batch_process
    print("Import successful")
    
    # Try running with --help
    sys.argv = ['batch_process.py', '--help']
    batch_process.main()
    
except Exception as e:
    print("=" * 60)
    print("EXCEPTION CAUGHT:")
    print("=" * 60)
    print(f"Type: {type(e).__name__}")
    print(f"Message: {str(e)}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
