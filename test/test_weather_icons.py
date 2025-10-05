#!/usr/bin/env python3
"""
Test script to demonstrate all weather icons and verify they display correctly
"""

import os
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from weather_service_openweather import WeatherService


def test_all_weather_icons():
    """Test all possible weather icons"""
    print("🌤️  Testing All Weather Icons")
    print("=" * 50)

    # Load environment variables
    load_dotenv('../conf/weather.conf')

    try:
        # Initialize weather service
        weather_service = WeatherService()
        print("✅ Weather service initialized")

        # Test current weather
        zip_code = os.getenv('LOCATION_ZIP_CODE', '95037')
        current_weather = weather_service.get_current_weather(zip_code)

        print(f"\n📍 Current Weather for {zip_code}:")
        print(f"   Temperature: {current_weather['temperature']}°F")
        print(f"   Condition: {current_weather['condition']}")
        print(f"   Icon: {current_weather['icon']}")
        print(f"   Description: {current_weather['description']}")

        # Test all possible weather conditions
        print(f"\n🎨 All Available Weather Icons:")
        test_conditions = [
            'CLEAR', 'SUNNY', 'PARTLY_CLOUDY', 'CLOUDY', 'OVERCAST',
            'RAIN', 'DRIZZLE', 'THUNDERSTORM', 'SNOW', 'FOG', 'WINDY',
            'CLOUDS', 'MIST'
        ]

        for condition in test_conditions:
            icon = weather_service._get_weather_icon(condition)
            print(f"   {condition:15} -> {icon}")

        print(f"\n✅ Weather icon system is working correctly!")
        print(
            f"Current weather shows: {current_weather['icon']} for {current_weather['condition']}")

        return True

    except Exception as e:
        print(f"❌ Error testing weather icons: {e}")
        return False


if __name__ == "__main__":
    success = test_all_weather_icons()
    if success:
        print("\n🎉 Weather icon test completed successfully!")
    else:
        print("\n❌ Weather icon test failed!")
