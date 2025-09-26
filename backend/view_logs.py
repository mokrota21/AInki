#!/usr/bin/env python3
"""
Simple script to view AInki logs in real-time
"""
import time
import os
import sys

def view_logs():
    log_file = "ainki.log"
    
    if not os.path.exists(log_file):
        print(f"❌ Log file '{log_file}' not found!")
        print("Make sure the backend is running and has generated logs.")
        return
    
    print(f"📋 Viewing logs from {log_file}")
    print("=" * 50)
    print("Press Ctrl+C to stop")
    print()
    
    try:
        with open(log_file, 'r') as f:
            # Go to end of file
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    print(line.strip())
                else:
                    time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n👋 Stopped viewing logs")
    except Exception as e:
        print(f"❌ Error reading logs: {e}")

if __name__ == "__main__":
    view_logs()
