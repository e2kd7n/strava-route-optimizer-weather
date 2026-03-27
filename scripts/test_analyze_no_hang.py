#!/usr/bin/env python3
"""
Test script to verify --analyze runs without hanging.
Runs analysis with a timeout to detect hangs.
"""

import subprocess
import sys
import signal
from pathlib import Path

def timeout_handler(signum, frame):
    print("\n❌ TIMEOUT: Analysis appears to be hanging!")
    sys.exit(1)

def main():
    # Set 2 minute timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(120)
    
    print("Running: python3 main.py --analyze")
    print("Timeout: 120 seconds")
    print("=" * 60)
    
    try:
        # Run the analysis
        result = subprocess.run(
            ['python3', 'main.py', '--analyze'],
            cwd=Path(__file__).parent.parent,
            capture_output=False,
            text=True
        )
        
        # Cancel the alarm
        signal.alarm(0)
        
        print("\n" + "=" * 60)
        if result.returncode == 0:
            print("✅ Analysis completed successfully without hanging!")
        else:
            print(f"⚠️  Analysis exited with code {result.returncode}")
        
        return result.returncode
        
    except KeyboardInterrupt:
        signal.alarm(0)
        print("\n\n⚠️  Interrupted by user")
        return 130

if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
