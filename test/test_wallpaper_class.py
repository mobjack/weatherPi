#!/usr/bin/env python3
"""
Test script demonstrating the WallpaperGenerator class usage.
"""

import importlib.util
import time
import sys
import os

# Add the parent directory to Python path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the WallpaperGenerator class
spec = importlib.util.spec_from_file_location(
    "wallpaper_gen", "../generate_wallpapers.py")
wallpaper_gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wallpaper_gen)
WallpaperGenerator = wallpaper_gen.WallpaperGenerator


def test_wallpaper_generation():
    """Test the WallpaperGenerator class with different scenarios."""

    print("🎨 Testing WallpaperGenerator Class")
    print("=" * 50)

    # Create a generator instance
    generator = WallpaperGenerator(
        day_night_json="../conf/day_night.json",
        conditions_json="../conf/gcp_conditions.json",
        output_dir="test_wallpapers"
    )

    # Test cases with different times and weather conditions
    test_cases = [
        {
            "name": "Morning Clear Sky",
            "style": "photoreal-soft",
            "epoch_time": time.time() - 3600 * 2,  # 2 hours ago (morning)
            "weather_condition": "CLEAR",
            "save_prompt": True
        },
        {
            "name": "Afternoon Rain",
            "style": "minimal-gradient",
            "epoch_time": time.time() - 3600 * 1,  # 1 hour ago (afternoon)
            "weather_condition": "RAIN",
            "save_prompt": True
        },
        {
            "name": "Evening Snow",
            "style": "flat-illustration",
            "epoch_time": time.time() + 3600 * 3,  # 3 hours from now (evening)
            "weather_condition": "SNOW",
            "save_prompt": False
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📸 Test {i}: {test_case['name']}")
        print("-" * 30)

        try:
            result = generator.generate_wallpaper(
                style=test_case["style"],
                epoch_time=test_case["epoch_time"],
                weather_condition=test_case["weather_condition"],
            )

            print(f"✅ Success!")
            print(f"   Style: {test_case['style']}")
            print(f"   Weather: {test_case['weather_condition']}")
            print(f"   Filename: {result['filename']}")
            print(f"   Path: {result['path']}")

        except Exception as e:
            print(f"❌ Error: {e}")

    print(f"\n🎉 Test completed! Check the 'test_wallpapers' directory for generated files.")


if __name__ == "__main__":
    test_wallpaper_generation()
