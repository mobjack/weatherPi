#!/usr/bin/env python3
"""
Helper module for loading configuration values from weather.conf
Used by test files to avoid hardcoded values
"""

import os
import sys
from pathlib import Path


def load_config_value(key, default=None):
    """Load a configuration value from weather.conf file"""
    # Try to find the config file in multiple locations
    possible_config_paths = [
        "conf/weather.conf",  # Relative to current directory
        os.path.join(os.path.dirname(__file__), "..", "conf",
                     "weather.conf"),  # Relative to test directory
        # Relative to working directory
        os.path.join(os.getcwd(), "conf", "weather.conf"),
    ]

    config_path = None
    for path in possible_config_paths:
        if os.path.exists(path):
            config_path = path
            break

    if not config_path:
        print(f"⚠️  Warning: Could not find weather.conf in any of these locations:")
        for path in possible_config_paths:
            print(f"    - {path}")
        return default

    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith(f'{key}='):
                    value = line.split('=', 1)[1].strip()
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    return value
    except Exception as e:
        print(f"⚠️  Warning: Error reading config file {config_path}: {e}")

    return default


def get_location_config():
    """Get location configuration from config file"""
    zip_code = load_config_value('LOCATION_ZIP_CODE', '12345')
    location_name = load_config_value('LOCATION_NAME', 'Your City, State')
    return zip_code, location_name
