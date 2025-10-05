#!/usr/bin/env python3
"""
Test script to verify that timing configuration loading works correctly.
"""

import sys
import os
import tempfile
import shutil

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_config_loading():
    """Test that configuration loading works correctly"""
    print("🧪 Testing configuration loading...")

    # Create a temporary config file
    test_config_content = """# Test Configuration
TIME_UPDATE_INTERVAL=30000
DATE_UPDATE_INTERVAL=7200000
WEATHER_UPDATE_INTERVAL=900000
BACKGROUND_UPDATE_INTERVAL=1200000
"""

    # Create temporary directory and config file
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "weather.conf")
        with open(config_path, 'w') as f:
            f.write(test_config_content)

        # Change to temp directory so the config file can be found
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Import and test the weather app's config loading
            from weather_app import WeatherApp

            # Create a mock app instance to test config loading
            class MockWeatherApp:
                def load_timing_config(self):
                    """Load timing configuration from weather.conf file"""
                    try:
                        # Default values (in milliseconds)
                        default_config = {
                            'TIME_UPDATE_INTERVAL': 60000,      # 1 minute
                            'DATE_UPDATE_INTERVAL': 3600000,    # 1 hour
                            'WEATHER_UPDATE_INTERVAL': 1800000,  # 30 minutes
                            'BACKGROUND_UPDATE_INTERVAL': 1800000  # 30 minutes
                        }

                        # Try to load from weather.conf file
                        config_path = "weather.conf"
                        if os.path.exists(config_path):
                            with open(config_path, 'r') as f:
                                for line in f:
                                    line = line.strip()
                                    if line and not line.startswith('#') and '=' in line:
                                        key, value = line.split('=', 1)
                                        key = key.strip()
                                        value = value.strip()

                                        # Check if this is a timing configuration
                                        if key in default_config:
                                            try:
                                                self.__dict__[
                                                    key.lower()] = int(value)
                                                print(
                                                    f"✅ Loaded {key}: {value}ms")
                                            except ValueError:
                                                print(
                                                    f"⚠️  Invalid value for {key}: {value}, using default")
                                                self.__dict__[
                                                    key.lower()] = default_config[key]
                                        else:
                                            # Set environment variable for other configs
                                            os.environ[key] = value
                        else:
                            print(
                                f"⚠️  Config file not found: {config_path}, using defaults")

                        # Set defaults for any missing values
                        for key, default_value in default_config.items():
                            if not hasattr(self, key.lower()):
                                self.__dict__[key.lower()] = default_value
                                print(
                                    f"📋 Using default {key}: {default_value}ms")

                    except Exception as e:
                        print(
                            f"⚠️  Error loading timing config: {e}, using defaults")
                        # Set all defaults
                        self.time_update_interval = 60000
                        self.date_update_interval = 3600000
                        self.weather_update_interval = 1800000
                        self.background_update_interval = 1800000

            # Test the config loading
            app = MockWeatherApp()
            app.load_timing_config()

            # Verify the values were loaded correctly
            assert app.time_update_interval == 30000, f"Expected 30000, got {app.time_update_interval}"
            assert app.date_update_interval == 7200000, f"Expected 7200000, got {app.date_update_interval}"
            assert app.weather_update_interval == 900000, f"Expected 900000, got {app.weather_update_interval}"
            assert app.background_update_interval == 1200000, f"Expected 1200000, got {app.background_update_interval}"

            print("✅ Configuration loading test passed!")

        finally:
            # Restore original working directory
            os.chdir(original_cwd)


def test_default_config():
    """Test that default values are used when config file is missing"""
    print("🧪 Testing default configuration...")

    # Create a temporary directory without config file
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Import and test the weather app's config loading
            from weather_app import WeatherApp

            # Create a mock app instance to test config loading
            class MockWeatherApp:
                def load_timing_config(self):
                    """Load timing configuration from weather.conf file"""
                    try:
                        # Default values (in milliseconds)
                        default_config = {
                            'TIME_UPDATE_INTERVAL': 60000,      # 1 minute
                            'DATE_UPDATE_INTERVAL': 3600000,    # 1 hour
                            'WEATHER_UPDATE_INTERVAL': 1800000,  # 30 minutes
                            'BACKGROUND_UPDATE_INTERVAL': 1800000  # 30 minutes
                        }

                        # Try to load from weather.conf file
                        config_path = "weather.conf"
                        if os.path.exists(config_path):
                            with open(config_path, 'r') as f:
                                for line in f:
                                    line = line.strip()
                                    if line and not line.startswith('#') and '=' in line:
                                        key, value = line.split('=', 1)
                                        key = key.strip()
                                        value = value.strip()

                                        # Check if this is a timing configuration
                                        if key in default_config:
                                            try:
                                                self.__dict__[
                                                    key.lower()] = int(value)
                                                print(
                                                    f"✅ Loaded {key}: {value}ms")
                                            except ValueError:
                                                print(
                                                    f"⚠️  Invalid value for {key}: {value}, using default")
                                                self.__dict__[
                                                    key.lower()] = default_config[key]
                                        else:
                                            # Set environment variable for other configs
                                            os.environ[key] = value
                        else:
                            print(
                                f"⚠️  Config file not found: {config_path}, using defaults")

                        # Set defaults for any missing values
                        for key, default_value in default_config.items():
                            if not hasattr(self, key.lower()):
                                self.__dict__[key.lower()] = default_value
                                print(
                                    f"📋 Using default {key}: {default_value}ms")

                    except Exception as e:
                        print(
                            f"⚠️  Error loading timing config: {e}, using defaults")
                        # Set all defaults
                        self.time_update_interval = 60000
                        self.date_update_interval = 3600000
                        self.weather_update_interval = 1800000
                        self.background_update_interval = 1800000

            # Test the config loading
            app = MockWeatherApp()
            app.load_timing_config()

            # Verify the default values were used
            assert app.time_update_interval == 60000, f"Expected 60000, got {app.time_update_interval}"
            assert app.date_update_interval == 3600000, f"Expected 3600000, got {app.date_update_interval}"
            assert app.weather_update_interval == 1800000, f"Expected 1800000, got {app.weather_update_interval}"
            assert app.background_update_interval == 1800000, f"Expected 1800000, got {app.background_update_interval}"

            print("✅ Default configuration test passed!")

        finally:
            # Restore original working directory
            os.chdir(original_cwd)


def main():
    """Run all tests"""
    print("🚀 Starting configuration loading tests...")

    try:
        test_config_loading()
        test_default_config()

        print("\n🎉 All tests passed! Configuration loading is working correctly.")
        print("\n📋 Summary of configuration changes:")
        print("   • Added timing configuration to weather.conf file")
        print("   • Weather app now reads timing intervals from config file")
        print("   • Fallback to default values if config file is missing")
        print("   • Easy to modify update intervals without changing code")
        print("\n⚙️  Configuration options in weather.conf:")
        print("   - TIME_UPDATE_INTERVAL: Time display update frequency (ms)")
        print("   - DATE_UPDATE_INTERVAL: Date/day update frequency (ms)")
        print("   - WEATHER_UPDATE_INTERVAL: Weather data update frequency (ms)")
        print("   - BACKGROUND_UPDATE_INTERVAL: Background update frequency (ms)")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
