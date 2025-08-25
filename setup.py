#!/usr/bin/env python3
"""Setup script for Jira CLI."""

import os
from datetime import datetime
from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop


def generate_version():
    """Generate PEP 440 compliant version string based on timestamp."""
    now = datetime.now()
    # Use format: YYYY.M.D.HHMM (PEP 440 compliant)
    return f"{now.year}.{now.month}.{now.day}.{now.hour:02d}{now.minute:02d}"


def write_version_file(version):
    """Write version to .version file in the package directory."""
    package_dir = os.path.join('src', 'jira_cli')
    version_file = os.path.join(package_dir, '.version')
    
    # Ensure directory exists
    os.makedirs(package_dir, exist_ok=True)
    
    # Write version file
    with open(version_file, 'w') as f:
        f.write(version)
    
    print(f"Version {version} written to {version_file}")


class CustomInstall(install):
    """Custom install command that generates version at install time."""
    
    def run(self):
        version = generate_version()
        write_version_file(version)
        super().run()


class CustomDevelop(develop):
    """Custom develop command that generates version at development install time."""
    
    def run(self):
        version = generate_version()
        write_version_file(version)
        super().run()


def get_version_for_setup():
    """Get or generate version for setuptools."""
    # Check if .version file already exists (from previous install)
    package_dir = os.path.join('src', 'jira_cli')
    version_file = os.path.join(package_dir, '.version')
    
    if os.path.exists(version_file):
        try:
            with open(version_file, 'r') as f:
                return f.read().strip()
        except Exception:
            pass
    
    # Generate new version
    return generate_version()


if __name__ == "__main__":
    # Get version for build
    version = get_version_for_setup()
    
    setup(
        version=version,
        cmdclass={
            'install': CustomInstall,
            'develop': CustomDevelop,
        }
    )