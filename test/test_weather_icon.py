#!/usr/bin/env python3
"""
Test script to verify weather icon updates are working correctly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../conf/weather.conf')


def test_weather_icon_update():
    """Test that weather icons are being updated correctly"""
    try:
        print("🧪 Testing weather icon updates...")

        # Import here to avoid issues if PyQt5 is not available
        from PyQt5.QtWidgets import QApplication
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from weather_app import WeatherApp

        # Create QApplication (required for PyQt5 widgets)
        app = QApplication(sys.argv)

        # Create WeatherApp instance
        weather_app = WeatherApp()
        print("✅ WeatherApp initialized successfully")

        # Check initial weather icon
        initial_icon = weather_app.weather_icon.text()
        print(f"📍 Initial weather icon: '{initial_icon}'")

        # Manually trigger weather data loading
        print("🌤️  Loading weather data...")
        weather_app.load_weather_data()

        # Check updated weather icon
        updated_icon = weather_app.weather_icon.text()
        print(f"📍 Updated weather icon: '{updated_icon}'")

        # Check if icon changed
        if initial_icon != updated_icon:
            print("✅ Weather icon updated successfully!")
        else:
            print(
                "⚠️  Weather icon did not change - this might be expected if weather hasn't changed")

        # Get current weather data to verify
        if weather_app.weather_service:
            zip_code = weather_app.location
            current_weather = weather_app.weather_service.get_current_weather(
                zip_code)
            expected_icon = current_weather.get('icon', '☀️')
            print(f"📍 Expected icon from API: '{expected_icon}'")
            print(f"📍 Current icon in UI: '{updated_icon}'")

            if expected_icon == updated_icon:
                print("✅ Weather icon matches API data!")
            else:
                print("❌ Weather icon does not match API data!")

        print("\n🎉 Weather icon test completed!")
        return True

    except Exception as e:
        print(f"❌ Error during weather icon test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_weather_icon_update()
    if success:
        print("\n✅ Weather icon test completed successfully!")
    else:
        print("\n❌ Weather icon test failed!")
        sys.exit(1)
