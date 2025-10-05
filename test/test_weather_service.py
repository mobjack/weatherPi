#!/usr/bin/env python3
"""
Test script for the WeatherService class
Run this to verify your Google Weather API setup is working correctly
"""

import os
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from weather_service import WeatherService


def main():
    # Load environment variables
    load_dotenv('../conf/weather.conf')

    # Check if API key is set
    api_key = os.getenv('GOOGLE_WEATHER_API_KEY')
    if not api_key or api_key == 'your_google_weather_api_key_here':
        print("❌ Error: GOOGLE_WEATHER_API_KEY not set in conf/weather.conf")
        print("Please add your Google Weather API key to conf/weather.conf file")
        return

    print("🌤️  Testing Weather Service...")
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

        print("\n✅ All tests passed! Your weather service is working correctly.")
        print("You can now run your weather app with real weather data.")

    except Exception as e:
        print(f"❌ Error testing weather service: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure your Google Cloud project has billing enabled")
        print("2. Verify the Weather API is enabled in your project")
        print("3. Check that your API key has proper permissions")
        print("4. Ensure your API key is correctly set in conf/weather.conf")


if __name__ == "__main__":
    main()
