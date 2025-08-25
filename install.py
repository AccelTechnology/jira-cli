#!/usr/bin/env python3
"""
Install script for Jira CLI with timestamped versioning.
This script installs jira-cli with a version based on the current timestamp.
"""

import os
import sys
import subprocess
from datetime import datetime


def main():
    """Install jira-cli with timestamped version."""
    print("🚀 Installing Jira CLI...")
    
    # Check if we're in the right directory
    if not os.path.exists('setup.py'):
        print("❌ Error: setup.py not found. Please run this script from the jira-cli directory.")
        sys.exit(1)
    
    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    if not in_venv:
        print("⚠️  Warning: You're not in a virtual environment.")
        response = input("Do you want to continue? (y/N): ").lower()
        if response != 'y':
            print("Installation cancelled.")
            sys.exit(0)
    
    try:
        # Install in development mode
        print("📦 Installing package...")
        result = subprocess.run([
            sys.executable, 'setup.py', 'develop'
        ], check=True, capture_output=True, text=True)
        
        # Extract version from output
        version = None
        for line in result.stdout.split('\n'):
            if 'Version' in line and 'written to' in line:
                version = line.split('Version ')[1].split(' written')[0]
                break
        
        print("✅ Installation completed successfully!")
        
        if version:
            # Parse and display install time
            try:
                parts = version.split('.')
                if len(parts) == 4:
                    year, month, day, time_part = parts
                    hour, minute = int(time_part[:2]), int(time_part[2:])
                    
                    install_time = datetime(int(year), int(month), int(day), hour, minute)
                    print(f"📅 Version: {version}")
                    print(f"🕐 Installed: {install_time.strftime('%Y-%m-%d at %H:%M')}")
            except Exception:
                print(f"📅 Version: {version}")
        
        print("\n🎉 Jira CLI is now installed!")
        print("Try running: jira-cli version")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ Installation cancelled by user.")
        sys.exit(1)


if __name__ == "__main__":
    main()