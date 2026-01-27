#!/usr/bin/env python3
"""Simple test to check if script output works"""
import sys

print("=== Test Output ===", file=sys.stdout)
print("stdout test", file=sys.stdout)
sys.stdout.flush()

print("stderr test", file=sys.stderr)
sys.stderr.flush()

sys.exit(0)
