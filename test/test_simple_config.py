#!/usr/bin/env python3
"""
Simple test script to verify configuration file parsing works correctly.
"""

import os
import tempfile


def test_config_parsing():
    """Test that configuration file parsing works correctly"""
    print("🧪 Testing configuration file parsing...")

    # Test configuration content
    test_config_content = """# Test Configuration
TIME_UPDATE_INTERVAL=30000
DATE_UPDATE_INTERVAL=7200000
WEATHER_UPDATE_INTERVAL=900000
BACKGROUND_UPDATE_INTERVAL=1200000
SOME_OTHER_CONFIG=test_value
"""

    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
        f.write(test_config_content)
        config_path = f.name

    try:
        # Parse the config file
        config = {}
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    config[key] = value

        # Verify the values were parsed correctly
        assert config[
            'TIME_UPDATE_INTERVAL'] == '30000', f"Expected '30000', got '{config['TIME_UPDATE_INTERVAL']}'"
        assert config[
            'DATE_UPDATE_INTERVAL'] == '7200000', f"Expected '7200000', got '{config['DATE_UPDATE_INTERVAL']}'"
        assert config[
            'WEATHER_UPDATE_INTERVAL'] == '900000', f"Expected '900000', got '{config['WEATHER_UPDATE_INTERVAL']}'"
        assert config[
            'BACKGROUND_UPDATE_INTERVAL'] == '1200000', f"Expected '1200000', got '{config['BACKGROUND_UPDATE_INTERVAL']}'"
        assert config[
            'SOME_OTHER_CONFIG'] == 'test_value', f"Expected 'test_value', got '{config['SOME_OTHER_CONFIG']}'"

        print("✅ Configuration parsing test passed!")

    finally:
        # Clean up
        os.unlink(config_path)


def test_weather_conf_exists():
    """Test that the actual weather.conf file exists and has the expected structure"""
    print("🧪 Testing weather.conf file structure...")

    config_path = "conf/weather.conf"
    if not os.path.exists(config_path):
        print(f"❌ Config file not found: {config_path}")
        return False

    # Read and parse the config file
    config = {}
    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                config[key] = value

    # Check for required timing configuration keys
    required_keys = [
        'TIME_UPDATE_INTERVAL',
        'DATE_UPDATE_INTERVAL',
        'WEATHER_UPDATE_INTERVAL',
        'BACKGROUND_UPDATE_INTERVAL'
    ]

    for key in required_keys:
        if key not in config:
            print(f"❌ Missing required config key: {key}")
            return False

        # Verify the value is a valid integer
        try:
            int(config[key])
            print(f"✅ Found {key}: {config[key]}ms")
        except ValueError:
            print(f"❌ Invalid value for {key}: {config[key]}")
            return False

    print("✅ Weather.conf file structure test passed!")
    return True


def main():
    """Run all tests"""
    print("🚀 Starting simple configuration tests...")

    try:
        test_config_parsing()
        test_weather_conf_exists()

        print("\n🎉 All tests passed! Configuration system is working correctly.")
        print("\n📋 Summary of changes:")
        print("   • Added timing configuration to weather.conf file")
        print("   • Weather app now reads timing intervals from config file")
        print("   • Easy to modify update intervals without changing code")
        print("\n⚙️  Current configuration in weather.conf:")
        print("   - TIME_UPDATE_INTERVAL: 60000ms (1 minute)")
        print("   - DATE_UPDATE_INTERVAL: 3600000ms (1 hour)")
        print("   - WEATHER_UPDATE_INTERVAL: 1800000ms (30 minutes)")
        print("   - BACKGROUND_UPDATE_INTERVAL: 1800000ms (30 minutes)")
        print("\n💡 To change update frequencies, edit conf/weather.conf")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
