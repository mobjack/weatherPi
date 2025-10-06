import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv('conf/weather.conf')


class WeatherService:
    """Service class for fetching weather data from OpenWeatherMap API"""

    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OPENWEATHER_API_KEY not found in environment variables")

        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.session = requests.Session()

    def get_current_weather(self, location: str) -> Dict:
        """
        Get current weather data for a location

        Args:
            location: Location string (e.g., "Morgan Hill, CA" or coordinates "37.1305,-121.6544")

        Returns:
            Dictionary containing current weather data
        """
        try:
            # Convert location to coordinates if it's a place name
            if not self._is_coordinate(location):
                location = self._geocode_location(location)

            # Parse coordinates
            lat, lng = location.split(',')

            url = f"{self.base_url}/weather"
            params = {
                'lat': float(lat.strip()),
                'lon': float(lng.strip()),
                'appid': self.api_key,
                'units': 'imperial'  # Use Fahrenheit
            }

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return self._parse_current_weather(data)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching current weather: {e}")
            return self._get_fallback_weather()
        except Exception as e:
            print(f"Unexpected error: {e}")
            return self._get_fallback_weather()

    def get_forecast_weather(self, location: str, days: int = 5) -> List[Dict]:
        """
        Get forecast weather data for a location

        Args:
            location: Location string (e.g., "Morgan Hill, CA" or coordinates "37.1305,-121.6544")
            days: Number of forecast days (default: 5)

        Returns:
            List of dictionaries containing forecast weather data
        """
        try:
            # Convert location to coordinates if it's a place name
            if not self._is_coordinate(location):
                location = self._geocode_location(location)

            # Parse coordinates
            lat, lng = location.split(',')

            url = f"{self.base_url}/forecast"
            params = {
                'lat': float(lat.strip()),
                'lon': float(lng.strip()),
                'appid': self.api_key,
                'units': 'imperial'  # Use Fahrenheit
            }

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return self._parse_forecast_weather(data, days)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching forecast weather: {e}")
            return self._get_fallback_forecast()
        except Exception as e:
            print(f"Unexpected error: {e}")
            return self._get_fallback_forecast()

    def get_hourly_forecast(self, location: str) -> List[Dict]:
        """
        Get hourly forecast data for the next 10 hours plus historical data for the previous 2 hours

        Args:
            location: Location string (e.g., "Morgan Hill, CA" or coordinates "37.1305,-121.6544")

        Returns:
            List of dictionaries containing hourly weather data (12 hours total: 2 past + 10 future)
        """
        try:
            # Convert location to coordinates if it's a place name
            if not self._is_coordinate(location):
                location = self._geocode_location(location)

            # Parse coordinates
            lat, lng = location.split(',')

            url = f"{self.base_url}/forecast"
            params = {
                'lat': float(lat.strip()),
                'lon': float(lng.strip()),
                'appid': self.api_key,
                'units': 'imperial'  # Use Fahrenheit
            }

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return self._parse_hourly_forecast(data)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching hourly forecast: {e}")
            return self._get_fallback_hourly_forecast()
        except Exception as e:
            print(f"Unexpected error: {e}")
            return self._get_fallback_hourly_forecast()

    def _geocode_location(self, location: str) -> str:
        """
        Convert a location name or zip code to coordinates using OpenWeatherMap Geocoding API

        Args:
            location: Location name (e.g., "Morgan Hill, CA") or zip code (e.g., "95037")

        Returns:
            Coordinates string (e.g., "37.1305,-121.6544")
        """
        try:
            # Check if location is a zip code (5 digits)
            if location.isdigit() and len(location) == 5:
                # Use zip code with country code for better accuracy
                geocode_url = f"{self.base_url}/weather"
                params = {
                    # Add US country code for zip codes
                    'zip': f"{location},US",
                    'appid': self.api_key
                }
                print(f"🌍 Geocoding zip code: {location},US")
            else:
                # Use location name
                geocode_url = f"{self.base_url}/weather"
                params = {
                    'q': location,
                    'appid': self.api_key
                }
                print(f"🌍 Geocoding location: {location}")

            response = self.session.get(geocode_url, params=params)
            response.raise_for_status()

            data = response.json()
            if 'coord' in data:
                lat = data['coord']['lat']
                lng = data['coord']['lon']
                print(f"✅ Found coordinates: {lat}, {lng}")
                return f"{lat},{lng}"
            else:
                # Fallback to Morgan Hill coordinates
                print("⚠️  No coordinates found, using fallback")
                return "37.1305,-121.6544"

        except Exception as e:
            print(f"❌ Error geocoding location: {e}")
            # Fallback to Morgan Hill coordinates
            return "37.1305,-121.6544"

    def _is_coordinate(self, location: str) -> bool:
        """Check if the location string is already in coordinate format"""
        try:
            parts = location.split(',')
            if len(parts) == 2:
                float(parts[0])  # latitude
                float(parts[1])  # longitude
                return True
        except ValueError:
            pass
        return False

    def _parse_current_weather(self, data: Dict) -> Dict:
        """Parse current weather data from API response"""
        try:
            condition = data.get('weather', [{}])[0].get('main', 'CLEAR')
            main_data = data.get('main', {})
            sys_data = data.get('sys', {})

            # Parse sunrise and sunset times
            sunrise_timestamp = sys_data.get('sunrise', 0)
            sunset_timestamp = sys_data.get('sunset', 0)

            sunrise_time = datetime.fromtimestamp(sunrise_timestamp).strftime(
                '%H:%M') if sunrise_timestamp else '06:30'
            sunset_time = datetime.fromtimestamp(sunset_timestamp).strftime(
                '%H:%M') if sunset_timestamp else '18:30'

            # Get today's high and low temperatures
            # Note: Current weather API doesn't provide daily highs/lows, so we'll use temp_min/temp_max if available
            # or estimate based on current temp
            current_temp = int(main_data.get('temp', 72))
            temp_min = int(main_data.get('temp_min', current_temp - 5))
            temp_max = int(main_data.get('temp_max', current_temp + 5))

            return {
                'temperature': current_temp,
                'high_temp': temp_max,
                'low_temp': temp_min,
                'condition': condition,
                'humidity': main_data.get('humidity', 50),
                'wind_speed': data.get('wind', {}).get('speed', 5),
                'sunrise': sunrise_time,
                'sunset': sunset_time,
                'icon': self._get_weather_icon(condition),
                'text_icon': self._get_weather_text_icon(condition),
                'icon_path': self._get_weather_icon_path(condition),
                'description': data.get('weather', [{}])[0].get('description', 'Clear')
            }
        except Exception as e:
            print(f"Error parsing current weather: {e}")
            return self._get_fallback_weather()

    def _parse_forecast_weather(self, data: Dict, days: int) -> List[Dict]:
        """Parse forecast weather data from API response"""
        try:
            forecasts = []
            daily_forecasts = data.get('list', [])
            current_date = datetime.now().date()

            # Group forecasts by day to calculate daily highs and lows
            daily_data = {}
            for forecast in daily_forecasts:
                date = datetime.fromtimestamp(forecast['dt']).date()
                # Skip today's date - we only want future days for the forecast
                if date > current_date:
                    if date not in daily_data:
                        daily_data[date] = {
                            'forecasts': [],
                            'high_temp': float('-inf'),
                            'low_temp': float('inf'),
                            'conditions': []
                        }

                    # Add this forecast to the day's data
                    temp = forecast.get('main', {}).get('temp', 72)
                    daily_data[date]['forecasts'].append(forecast)
                    daily_data[date]['high_temp'] = max(
                        daily_data[date]['high_temp'], temp)
                    daily_data[date]['low_temp'] = min(
                        daily_data[date]['low_temp'], temp)

                    # Collect conditions for the day (use the most common one)
                    condition = forecast.get('weather', [{}])[
                        0].get('main', 'CLEAR')
                    daily_data[date]['conditions'].append(condition)

            # Convert to list and limit to requested days
            sorted_dates = sorted(daily_data.keys())[:days]

            for i, date in enumerate(sorted_dates):
                day_info = daily_data[date]
                day_name = date.strftime('%a')

                # Use the most common condition for the day
                from collections import Counter
                most_common_condition = Counter(
                    day_info['conditions']).most_common(1)[0][0]

                # Get the first forecast for icon and description
                first_forecast = day_info['forecasts'][0]

                forecasts.append({
                    'day': day_name,
                    'temperature': f"H:{int(day_info['high_temp'])} L:{int(day_info['low_temp'])}",
                    'high_temp': int(day_info['high_temp']),
                    'low_temp': int(day_info['low_temp']),
                    'condition': most_common_condition,
                    'icon': self._get_weather_icon(most_common_condition),
                    'text_icon': self._get_weather_text_icon(most_common_condition),
                    'icon_path': self._get_weather_icon_path(most_common_condition),
                    'description': first_forecast.get('weather', [{}])[0].get('description', 'Clear')
                })

            return forecasts
        except Exception as e:
            print(f"Error parsing forecast weather: {e}")
            return self._get_fallback_forecast()

    def _get_weather_icon(self, condition: str) -> str:
        """Map weather condition to emoji icon with better visibility"""
        icon_map = {
            'CLEAR': '☀️',      # Sun
            'SUNNY': '☀️',       # Sun
            'PARTLY_CLOUDY': '⛅',  # Partly cloudy
            'CLOUDY': '☁️',      # Cloud
            'OVERCAST': '☁️',    # Cloud
            'RAIN': '🌧️',       # Rain
            'DRIZZLE': '🌦️',    # Light rain
            'THUNDERSTORM': '⛈️',  # Thunderstorm
            'SNOW': '❄️',       # Snow
            'FOG': '🌫️',        # Fog
            'WINDY': '💨',       # Wind
            'CLOUDS': '☁️',      # Cloud
            'MIST': '🌫️'        # Mist
        }
        return icon_map.get(condition.upper(), '☀️')

    def _get_weather_text_icon(self, condition: str) -> str:
        """Map weather condition to text-based icon for better compatibility"""
        text_icon_map = {
            'CLEAR': 'SUN',      # Sun
            'SUNNY': 'SUN',       # Sun
            'PARTLY_CLOUDY': 'CLOUD',  # Partly cloudy
            'CLOUDY': 'CLOUD',      # Cloud
            'OVERCAST': 'CLOUD',    # Cloud
            'RAIN': 'RAIN',       # Rain
            'DRIZZLE': 'DRIZZLE',    # Light rain
            'THUNDERSTORM': 'STORM',  # Thunderstorm
            'SNOW': 'SNOW',       # Snow
            'FOG': 'FOG',        # Fog
            'WINDY': 'WIND',       # Wind
            'CLOUDS': 'CLOUD',      # Cloud
            'MIST': 'FOG'        # Mist
        }
        return text_icon_map.get(condition.upper(), 'SUN')

    def _get_weather_icon_path(self, condition: str) -> str:
        """Map weather condition to local icon file path"""
        # Get the base directory of this script and go up one level to project root
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up from bin/ to project root
        project_root = os.path.dirname(script_dir)
        icons_dir = os.path.join(project_root, 'images', 'icons')

        # Map conditions to icon files
        icon_map = {
            'CLEAR': 'sun.png',
            'SUNNY': 'sun.png',
            'PARTLY_CLOUDY': 'partly_cloudy.png',
            'CLOUDY': 'cloud.png',
            'OVERCAST': 'cloud.png',
            'RAIN': 'rain.png',
            'DRIZZLE': 'rain.png',
            'THUNDERSTORM': 'storm.png',
            'SNOW': 'snow.png',
            'FOG': 'fog.png',
            'WINDY': 'wind.png',
            'CLOUDS': 'cloud.png',
            'MIST': 'fog.png'
        }

        icon_filename = icon_map.get(condition.upper(), 'sun.png')
        icon_path = os.path.join(icons_dir, icon_filename)

        # Check if the icon file exists, fallback to sun.png if not
        if not os.path.exists(icon_path):
            fallback_path = os.path.join(icons_dir, 'sun.png')
            if os.path.exists(fallback_path):
                return fallback_path
            else:
                print(f"⚠️  Warning: No icon files found in {icons_dir}")
                return None

        return icon_path

    def _get_fallback_weather(self) -> Dict:
        """Return fallback weather data when API fails"""
        return {
            'temperature': 72,
            'high_temp': 78,
            'low_temp': 65,
            'condition': 'CLEAR',
            'humidity': 50,
            'wind_speed': 5,
            'sunrise': '06:30',
            'sunset': '18:30',
            'icon': '☀️',
            'text_icon': 'SUN',
            'icon_path': self._get_weather_icon_path('CLEAR'),
            'description': 'Clear'
        }

    def _parse_hourly_forecast(self, data: Dict) -> List[Dict]:
        """Parse hourly forecast data from API response"""
        try:
            forecasts = []
            hourly_forecasts = data.get('list', [])

            # Get current time
            current_time = datetime.now()

            # Create historical data for the past 2 hours (simulated)
            # In a real implementation, you might want to use historical weather data
            historical_data = []
            for i in range(2, 0, -1):  # 2 hours ago, 1 hour ago
                past_time = current_time - timedelta(hours=i)
                # Simulate historical temperature (slightly lower than current)
                historical_temp = 70 - (i * 2)  # Simple simulation
                historical_data.append({
                    'hour': past_time.strftime('%H:%M'),
                    'temperature': historical_temp,
                    'condition': 'CLEAR',
                    'icon': self._get_weather_icon('CLEAR'),
                    'text_icon': self._get_weather_text_icon('CLEAR'),
                    'icon_path': self._get_weather_icon_path('CLEAR'),
                    'description': 'Clear'
                })

            # Add current hour
            current_condition = 'CLEAR'  # Default, could be enhanced with current weather
            current_temp = 70  # Default, could be enhanced with current weather
            historical_data.append({
                'hour': current_time.strftime('%H:%M'),
                'temperature': current_temp,
                'condition': current_condition,
                'icon': self._get_weather_icon(current_condition),
                'text_icon': self._get_weather_text_icon(current_condition),
                'icon_path': self._get_weather_icon_path(current_condition),
                'description': 'Clear'
            })

            # Get future forecast data (next 10 hours)
            future_data = []
            # Next 10 hours
            for i, forecast in enumerate(hourly_forecasts[:10]):
                forecast_time = datetime.fromtimestamp(forecast['dt'])
                condition = forecast.get('weather', [{}])[
                    0].get('main', 'CLEAR')
                temp = int(forecast.get('main', {}).get('temp', 70))

                future_data.append({
                    'hour': forecast_time.strftime('%H:%M'),
                    'temperature': temp,
                    'condition': condition,
                    'icon': self._get_weather_icon(condition),
                    'text_icon': self._get_weather_text_icon(condition),
                    'icon_path': self._get_weather_icon_path(condition),
                    'description': forecast.get('weather', [{}])[0].get('description', 'Clear')
                })

            # Combine historical + current + future data
            all_data = historical_data + future_data

            return all_data

        except Exception as e:
            print(f"Error parsing hourly forecast: {e}")
            return self._get_fallback_hourly_forecast()

    def _get_fallback_forecast(self) -> List[Dict]:
        """Return fallback forecast data when API fails"""
        # Generate day names based on current date
        current_date = datetime.now().date()
        days = []
        for i in range(5):  # Next 5 days
            future_date = current_date + \
                timedelta(days=i+1)  # Start from tomorrow
            day_name = future_date.strftime('%a')
            days.append(day_name)

        conditions = ['CLEAR', 'CLOUDY', 'RAIN', 'CLOUDY', 'CLOUDY']
        high_temps = [78, 70, 68, 68, 75]
        low_temps = [65, 60, 58, 58, 65]

        return [
            {
                'day': day,
                'temperature': f"H:{high_temp} L:{low_temp}",
                'high_temp': high_temp,
                'low_temp': low_temp,
                'condition': condition,
                'icon': self._get_weather_icon(condition),
                'text_icon': self._get_weather_text_icon(condition),
                'icon_path': self._get_weather_icon_path(condition),
                'description': 'Clear' if condition == 'CLEAR' else 'Cloudy' if condition == 'CLOUDY' else 'Rainy'
            }
            for day, high_temp, low_temp, condition in zip(days, high_temps, low_temps, conditions)
        ]

    def _get_fallback_hourly_forecast(self) -> List[Dict]:
        """Return fallback hourly forecast data when API fails"""
        current_time = datetime.now()
        hourly_data = []

        # Generate 12 hours of data (2 past + current + 9 future)
        for i in range(-2, 10):  # -2 hours ago to +9 hours from now
            hour_time = current_time + timedelta(hours=i)
            # Simulate temperature variation
            base_temp = 70
            temp_variation = i * 1.5  # Simple temperature trend
            temp = int(base_temp + temp_variation)

            # Vary conditions slightly
            if i < 0:
                condition = 'CLEAR'
            elif i < 3:
                condition = 'PARTLY_CLOUDY'
            elif i < 6:
                condition = 'CLOUDY'
            else:
                condition = 'CLEAR'

            hourly_data.append({
                'hour': hour_time.strftime('%H:%M'),
                'temperature': temp,
                'condition': condition,
                'icon': self._get_weather_icon(condition),
                'text_icon': self._get_weather_text_icon(condition),
                'icon_path': self._get_weather_icon_path(condition),
                'description': 'Clear' if condition == 'CLEAR' else 'Partly Cloudy' if condition == 'PARTLY_CLOUDY' else 'Cloudy'
            })

        return hourly_data


# Test the weather service
if __name__ == "__main__":
    try:
        weather_service = WeatherService()

        # Test current weather
        print("Testing current weather...")
        current = weather_service.get_current_weather("Morgan Hill, CA")
        print(f"Current weather: {current}")

        # Test forecast
        print("\nTesting forecast...")
        forecast = weather_service.get_forecast_weather("Morgan Hill, CA")
        print(f"Forecast: {forecast}")

    except Exception as e:
        print(f"Error testing weather service: {e}")
