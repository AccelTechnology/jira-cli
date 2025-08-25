"""Jira CLI package."""

import os
from datetime import datetime

__author__ = "AccelERP Team"
__email__ = "team@accelerp.com"

def _get_version():
    """Get version from installed version file or generate development version."""
    # Try to read from installed version file
    version_file = os.path.join(os.path.dirname(__file__), '.version')
    if os.path.exists(version_file):
        try:
            with open(version_file, 'r') as f:
                return f.read().strip()
        except Exception:
            pass
    
    # Fallback to development version with current timestamp
    now = datetime.now()
    return f"dev.{now.year}.{now.month}.{now.day}.{now.hour:02d}{now.minute:02d}"

__version__ = _get_version()