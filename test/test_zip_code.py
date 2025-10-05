#!/usr/bin/env python3
"""
Test script for the OpenWeatherMap Weather Service using zip code
"""

import os
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from weather_service_openweather import WeatherService


def main():
    # Load environment variables
    load_dotenv('../conf/weather.conf')

    # Get zip code from environment
    zip_code = os.getenv('LOCATION_ZIP_CODE', '95037')
    location_name = os.getenv('LOCATION_NAME', 'Morgan Hill, CA')

    print(
        f"🌤️  Testing OpenWeatherMap Weather Service with Zip Code: {zip_code}")
    print(f"📍 Location: {location_name}")
    print("=" * 60)

    try:
        # Initialize weather service
        weather_service = WeatherService()
        print("✅ WeatherService initialized successfully")

        # Test current weather with zip code
        print(f"\n📍 Testing current weather for zip code {zip_code}...")
        current_weather = weather_service.get_current_weather(zip_code)
        print(f"Current Weather:")
        print(f"  Temperature: {current_weather['temperature']}°F")
        print(f"  Condition: {current_weather['condition']}")
        print(f"  Icon: {current_weather['icon']}")
        print(f"  Description: {current_weather['description']}")
        print(f"  Humidity: {current_weather['humidity']}%")
        print(f"  Wind Speed: {current_weather['wind_speed']} mph")

        # Test forecast with zip code
        print(f"\n📅 Testing 5-day forecast for zip code {zip_code}...")
        forecast = weather_service.get_forecast_weather(zip_code, days=5)
        print("5-Day Forecast:")
        for day in forecast:
            print(
                f"  {day['day']}: {day['temperature']}°F {day['icon']} ({day['description']})")

        print(
            f"\n✅ All tests passed! Zip code {zip_code} is working correctly.")
        print("Your weather app should now work without geocoding errors.")

    except Exception as e:
        print(f"❌ Error testing weather service with zip code: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure your OpenWeatherMap API key is correct")
        print("2. Verify the zip code is valid")
        print("3. Check your internet connection")


if __name__ == "__main__":
    main()
