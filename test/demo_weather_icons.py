#!/usr/bin/env python3
"""
Demo script to show different weather icons in the weather app
"""

import os
import sys
import time
from dotenv import load_dotenv
from PyQt5.QtWidgets import QApplication
from weather_app import WeatherApp


def demo_weather_icons():
    """Demo different weather icons by temporarily changing the weather data"""
    print("🎨 Weather Icon Demo")
    print("=" * 30)

    # Load environment variables
    load_dotenv('conf/weather.conf')

    try:
        # Create QApplication
        app = QApplication(sys.argv)

        # Create WeatherApp
        weather_app = WeatherApp()
        print("✅ Weather app created")

        # Demo different weather conditions
        demo_conditions = [
            {'condition': 'CLEAR', 'icon': '☀️',
                'temp': 75, 'description': 'Clear sky'},
            {'condition': 'CLOUDY', 'icon': '☁️',
                'temp': 70, 'description': 'Cloudy'},
            {'condition': 'RAIN', 'icon': '🌧️', 'temp': 65, 'description': 'Rain'},
            {'condition': 'SNOW', 'icon': '❄️', 'temp': 32, 'description': 'Snow'},
            {'condition': 'THUNDERSTORM', 'icon': '⛈️',
                'temp': 68, 'description': 'Thunderstorm'}
        ]

        print("\n🎭 Demo: Cycling through different weather conditions...")
        print("(Each condition will display for 3 seconds)")

        for i, demo_weather in enumerate(demo_conditions, 1):
            print(
                f"\n{i}. {demo_weather['condition']}: {demo_weather['icon']} {demo_weather['temp']}°F")

            # Update the weather display with demo data
            weather_app.update_current_weather_display(demo_weather)

            # Process events to update the UI
            app.processEvents()

            # Wait 3 seconds
            time.sleep(3)

        print("\n✅ Demo completed!")
        print("The weather app should have shown different icons for each condition.")

        return True

    except Exception as e:
        print(f"❌ Error during demo: {e}")
        return False


if __name__ == "__main__":
    print("This demo will show different weather icons in the weather app.")
    print("Make sure the weather app window is visible!")
    input("Press Enter to start the demo...")

    success = demo_weather_icons()
    if success:
        print("\n🎉 Weather icon demo completed!")
    else:
        print("\n❌ Weather icon demo failed!")
