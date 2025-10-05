#!/usr/bin/env python3
"""
Test script for the OpenWeatherMap WeatherService class
Run this to verify your OpenWeatherMap API setup is working correctly
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

    # Check if API key is set
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key or api_key == 'your_openweather_api_key_here':
        print("❌ Error: OPENWEATHER_API_KEY not set in conf/weather.conf")
        print("Please add your OpenWeatherMap API key to conf/weather.conf file")
        print("Get your free API key at: https://openweathermap.org/api")
        return

    print("🌤️  Testing OpenWeatherMap Weather Service...")
    # Show partial key for verification
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")

    try:
        # Initialize weather service
        weather_service = WeatherService()
        print("✅ WeatherService initialized successfully")

        # Test current weather
        print("\n📍 Testing current weather for Morgan Hill, CA...")
        current_weather = weather_service.get_current_weather(
            "Morgan Hill, CA")
        print(f"Current Weather: {current_weather}")

        # Test forecast
        print("\n📅 Testing 5-day forecast...")
        forecast = weather_service.get_forecast_weather(
            "Morgan Hill, CA", days=5)
        print(f"Forecast: {forecast}")

        print("\n✅ All tests passed! Your OpenWeatherMap weather service is working correctly.")
        print("You can now run your weather app with real weather data.")

    except Exception as e:
        print(f"❌ Error testing weather service: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure your OpenWeatherMap API key is correct")
        print("2. Verify the API key is properly set in conf/weather.conf")
        print("3. Check that you have an active OpenWeatherMap account")


if __name__ == "__main__":
    main()
