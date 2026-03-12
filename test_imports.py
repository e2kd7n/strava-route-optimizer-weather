#!/usr/bin/env python3
"""
Test script to validate all imports and basic structure.
Run this before installing dependencies to check for syntax errors.
"""

import ast
import sys
from pathlib import Path


def check_syntax(file_path):
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r') as f:
            code = f.read()
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, str(e)


def main():
    """Check all Python files for syntax errors."""
    src_dir = Path('src')
    errors = []
    
    print("Checking Python files for syntax errors...\n")
    
    # Check all Python files
    python_files = list(src_dir.glob('*.py')) + [Path('main.py')]
    
    for file_path in python_files:
        if not file_path.exists():
            continue
            
        valid, error = check_syntax(file_path)
        
        if valid:
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}: {error}")
            errors.append((file_path, error))
    
    print(f"\n{'='*60}")
    
    if errors:
        print(f"\n❌ Found {len(errors)} syntax error(s):\n")
        for file_path, error in errors:
            print(f"  {file_path}:")
            print(f"    {error}\n")
        sys.exit(1)
    else:
        print("\n✅ All files have valid syntax!")
        print("\nNext steps:")
        print("  1. Create virtual environment: python3 -m venv venv")
        print("  2. Activate it: source venv/bin/activate")
        print("  3. Install dependencies: pip install -r requirements.txt")
        print("  4. Run authentication: python3 main.py --auth")
        sys.exit(0)


if __name__ == '__main__':
    main()

# Made with Bob
