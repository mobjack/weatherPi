#!/usr/bin/env python3
"""
Test script to fix weather icon display issue
"""

import os
import sys
import time
from dotenv import load_dotenv
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from weather_app import WeatherApp


def test_weather_icon_fix():
    """Test and fix weather icon display"""
    print("🔧 Testing weather icon fix...")

    try:
        app = QApplication(sys.argv)
        weather_app = WeatherApp()

        print("✅ Weather app created")
        print(f"📍 Initial weather icon: '{weather_app.weather_icon.text()}'")

        # Show the app
        weather_app.show()
        print("✅ Weather app is now visible")

        # Create a timer to force icon update after a short delay
        def force_icon_update():
            print("🔄 Forcing weather icon update...")

            # Get current weather data
            if weather_app.weather_service:
                zip_code = weather_app.location
                current_weather = weather_app.weather_service.get_current_weather(
                    zip_code)
                icon = current_weather.get('icon', '☁️')

                print(f"🌤️  Setting weather icon to: {icon}")
                weather_app.weather_icon.setText(icon)
                weather_app.weather_icon.repaint()
                weather_app.weather_icon.update()

                print(
                    f"🔍 Weather icon is now: '{weather_app.weather_icon.text()}'")

                # Also update the temperature
                temp = current_weather.get('temperature', 74)
                weather_app.temp_label.setText(f"{temp}°")

                print(f"🌡️  Temperature updated to: {temp}°F")

        # Set up timer to force update after 2 seconds
        timer = QTimer()
        timer.timeout.connect(force_icon_update)
        timer.setSingleShot(True)
        timer.start(2000)  # 2 seconds

        print("⏰ Timer set to force icon update in 2 seconds...")
        print(
            "Watch the weather icon in the upper center - it should change to a cloud (☁️)")

        # Keep the app running
        print("App will stay open for 20 seconds...")
        time.sleep(20)

        return True

    except Exception as e:
        print(f"❌ Error testing weather icon fix: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_weather_icon_fix()
    if success:
        print("✅ Weather icon fix test completed!")
    else:
        print("❌ Weather icon fix test failed!")
