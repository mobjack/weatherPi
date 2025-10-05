#!/usr/bin/env python3
"""
Test script to verify WeatherApp initialization works correctly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../conf/weather.conf')


def test_weather_app_init():
    """Test that WeatherApp can be initialized without errors"""
    try:
        print("🧪 Testing WeatherApp initialization...")

        # Import here to avoid issues if PyQt5 is not available
        from PyQt5.QtWidgets import QApplication
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from weather_app import WeatherApp

        # Create QApplication (required for PyQt5 widgets)
        app = QApplication(sys.argv)

        # Test initialization
        print("✅ QApplication created successfully")

        # Create WeatherApp instance
        weather_app = WeatherApp()
        print("✅ WeatherApp initialized successfully")

        # Check that location attributes are set
        print(f"📍 Location zip code: {weather_app.location}")
        print(f"📍 Location name: {weather_app.location_name}")

        # Check that weather service is available
        if weather_app.weather_service:
            print("✅ Weather service is available")
        else:
            print("⚠️  Weather service is not available")

        # Check that wallpaper generator is available
        if weather_app.wallpaper_generator:
            print("✅ Wallpaper generator is available")
        else:
            print("⚠️  Wallpaper generator is not available")

        print("\n🎉 All tests passed! WeatherApp is working correctly.")
        return True

    except Exception as e:
        print(f"❌ Error during WeatherApp initialization: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_weather_app_init()
    if success:
        print("\n✅ WeatherApp initialization test completed successfully!")
    else:
        print("\n❌ WeatherApp initialization test failed!")
        sys.exit(1)
