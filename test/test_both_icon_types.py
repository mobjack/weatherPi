#!/usr/bin/env python3
"""
Test script to compare emoji vs text weather icons
"""

import os
import sys
import time
from dotenv import load_dotenv
from PyQt5.QtWidgets import QApplication
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from weather_app import WeatherApp


def test_both_icon_types():
    """Test both emoji and text weather icons"""
    print("🧪 Testing Both Icon Types")
    print("=" * 40)

    # Load environment variables
    load_dotenv('../conf/weather.conf')

    try:
        app = QApplication(sys.argv)

        # Test 1: Emoji icons
        print("\n1️⃣  Testing with EMOJI icons...")
        os.environ['USE_TEXT_ICONS'] = 'false'

        weather_app_emoji = WeatherApp()
        print(
            f"📍 Emoji weather icon: '{weather_app_emoji.weather_icon.text()}'")

        # Test 2: Text icons
        print("\n2️⃣  Testing with TEXT icons...")
        os.environ['USE_TEXT_ICONS'] = 'true'

        weather_app_text = WeatherApp()
        print(f"📍 Text weather icon: '{weather_app_text.weather_icon.text()}'")

        # Show the text version (more reliable)
        weather_app_text.show()
        print("✅ Weather app with TEXT icons is now visible")
        print("The weather icon should show 'CLOUD' for your current cloudy weather")

        # Keep running for a bit
        print("App will stay open for 15 seconds...")
        time.sleep(15)

        return True

    except Exception as e:
        print(f"❌ Error testing icon types: {e}")
        return False


if __name__ == "__main__":
    success = test_both_icon_types()
    if success:
        print("✅ Icon type test completed!")
    else:
        print("❌ Icon type test failed!")
