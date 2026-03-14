#!/usr/bin/env python3
"""
Verify all dependencies for the long ride recommendation feature are installed.
"""

import sys

def check_dependencies():
    """Check if all required dependencies are installed."""
    missing = []
    
    dependencies = {
        'numpy': 'numpy',
        'geopy': 'geopy',
        'polyline': 'polyline',
        'requests': 'requests',
        'scipy': 'scipy',
        'jinja2': 'jinja2',
        'cryptography': 'cryptography',
        'stravalib': 'stravalib',
        'pandas': 'pandas',
        'scikit-learn': 'sklearn',
        'folium': 'folium',
        'pyyaml': 'yaml',
        'python-dotenv': 'dotenv',
        'similaritymeasures': 'similaritymeasures',
    }
    
    print("Checking dependencies for long ride recommendations...")
    print("=" * 60)
    
    for package, import_name in dependencies.items():
        try:
            __import__(import_name)
            print(f"✅ {package:20s} - installed")
        except ImportError:
            print(f"❌ {package:20s} - MISSING")
            missing.append(package)
    
    print("=" * 60)
    
    if missing:
        print(f"\n❌ Missing {len(missing)} dependencies:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\nInstall missing dependencies with:")
        print("   pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All dependencies installed!")
        print("\nYou can now run the application:")
        print("   python3 main.py")
        return True

if __name__ == "__main__":
    success = check_dependencies()
    sys.exit(0 if success else 1)

# Made with Bob
