#!/usr/bin/env python3
"""
Test script to verify weather data integration in the weather app
"""

from config_helper import get_location_config
from weather_service_openweather import WeatherService
import os
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    # Load environment variables
    load_dotenv('../conf/weather.conf')

    print("🌤️  Testing Weather Integration...")

    try:
        # Initialize weather service
        weather_service = WeatherService()
        print("✅ WeatherService initialized successfully")

        # Get location from config
        zip_code, location_name = get_location_config()

        # Test current weather
        print(f"\n📍 Getting current weather for {location_name}...")
        current_weather = weather_service.get_current_weather(location_name)
        print(f"Current Weather:")
        print(f"  Temperature: {current_weather['temperature']}°F")
        print(f"  Condition: {current_weather['condition']}")
        print(f"  Icon: {current_weather['icon']}")
        print(f"  Description: {current_weather['description']}")
        print(f"  Humidity: {current_weather['humidity']}%")
        print(f"  Wind Speed: {current_weather['wind_speed']} mph")

        # Test forecast
        print("\n📅 Getting 5-day forecast...")
        forecast = weather_service.get_forecast_weather(location_name, days=5)
        print("5-Day Forecast:")
        for day in forecast:
            print(
                f"  {day['day']}: {day['temperature']}°F {day['icon']} ({day['description']})")

        print("\n✅ Weather integration test completed successfully!")
        print("Your weather app should now display real weather data.")

    except Exception as e:
        print(f"❌ Error testing weather integration: {e}")


if __name__ == "__main__":
    main()
