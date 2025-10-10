#!/usr/bin/env python3
"""
Test script for the updated WallpaperGenerator with real weather integration
"""

from config_helper import get_location_config
from generate_wallpapers import WallpaperGenerator
import os
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    # Load environment variables
    load_dotenv('../conf/weather.conf')

    print("🎨 Testing WallpaperGenerator with Real Weather Data")
    print("=" * 60)

    try:
        # Create a generator instance
        generator = WallpaperGenerator(
            day_night_json="../conf/day_night.json",
            conditions_json="../conf/gcp_conditions.json",
            output_dir="images/generated_wallpapers"
        )

        print("✅ WallpaperGenerator initialized successfully")

        # Get zip code from config file
        zip_code, location_name = get_location_config()

        # Test 1: Get current weather condition
        print(
            f"\n🌤️  Test 1: Getting current weather condition for zip {zip_code}...")
        current_condition = generator.get_current_weather_condition(zip_code)
        print(f"Current weather condition: {current_condition}")

        # Test 2: Get current time
        print("\n⏰ Test 2: Getting current time...")
        current_epoch = generator.get_current_time_epoch()
        print(f"Current epoch time: {current_epoch}")

        # Test 3: Generate wallpaper based on current weather
        print(
            f"\n🎨 Test 3: Generating wallpaper based on current weather for zip {zip_code}...")
        result = generator.generate_current_weather_wallpaper(
            style="photoreal-soft",
            location=zip_code,
            target_size=(800, 600),
            try_resize=True,
            save_prompt=True
        )

        print(f"✅ Generated current weather wallpaper successfully!")
        print(f"   Filename: {result['filename']}")
        print(f"   Path: {result['path']}")

        # Test 4: Test the mapping function
        print("\n🔄 Test 4: Testing OpenWeatherMap to Google condition mapping...")
        from generate_wallpapers import map_openweather_to_google

        test_conditions = ['Clear', 'Clouds', 'Rain', 'Snow', 'Thunderstorm']
        for condition in test_conditions:
            mapped = map_openweather_to_google(condition)
            print(f"   {condition} -> {mapped}")

        print("\n✅ All tests completed successfully!")
        print("Your wallpaper generator is now integrated with real weather data.")

    except Exception as e:
        print(f"❌ Error testing wallpaper generator: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure your OpenWeatherMap API key is set in conf/weather.conf")
        print("2. Verify the weather service is working")
        print(
            "3. Check that all required files (conf/day_night.json, conf/gcp_conditions.json) exist")


if __name__ == "__main__":
    main()
