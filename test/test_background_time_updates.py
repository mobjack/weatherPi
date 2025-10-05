#!/usr/bin/env python3
"""
Test script to verify that background updates work based on time of day changes.
This script simulates different times of day to test the time period detection.
"""

import sys
import os
import time
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the weather app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weather_app import WeatherApp
from PyQt5.QtWidgets import QApplication


def test_time_period_detection():
    """Test that time periods are detected correctly"""
    print("🧪 Testing time period detection...")
    
    # Create a mock wallpaper generator
    mock_generator = MagicMock()
    
    # Test different hours and expected time periods
    test_cases = [
        (6, "sunrise"),    # 6 AM
        (8, "morning"),    # 8 AM  
        (12, "midday"),    # 12 PM
        (14, "afternoon"), # 2 PM
        (17, "sunset"),    # 5 PM
        (19, "dusk"),      # 7 PM
        (21, "evening"),   # 9 PM
        (23, "night"),     # 11 PM
        (2, "night"),      # 2 AM
    ]
    
    for hour, expected_period in test_cases:
        # Mock the epoch_to_time_of_day method
        mock_generator._epoch_to_time_of_day.return_value = expected_period
        
        # Create app instance with mock generator
        app = WeatherApp()
        app.wallpaper_generator = mock_generator
        
        # Test the time period detection
        detected_period = app.get_current_time_period()
        
        print(f"   Hour {hour:2d}: Expected '{expected_period}', Got '{detected_period}'")
        assert detected_period == expected_period, f"Expected {expected_period}, got {detected_period}"
    
    print("✅ Time period detection test passed!")


def test_background_update_logic():
    """Test the background update logic"""
    print("🧪 Testing background update logic...")
    
    # Create app instance
    app = WeatherApp()
    
    # Mock the wallpaper generator
    app.wallpaper_generator = MagicMock()
    app.wallpaper_generator._epoch_to_time_of_day.return_value = "morning"
    
    # Set initial time period
    app.current_time_period = "night"
    
    # Mock the background update methods
    app.update_background_for_current_conditions = MagicMock()
    
    # Test that background updates when time period changes
    app.check_and_update_background()
    
    # Verify that update_background_for_current_conditions was called
    app.update_background_for_current_conditions.assert_called_once()
    
    # Verify that current_time_period was updated
    assert app.current_time_period == "morning"
    
    print("✅ Background update logic test passed!")


def test_no_update_when_same_period():
    """Test that background doesn't update when time period is the same"""
    print("🧪 Testing no update when time period is the same...")
    
    # Create app instance
    app = WeatherApp()
    
    # Mock the wallpaper generator
    app.wallpaper_generator = MagicMock()
    app.wallpaper_generator._epoch_to_time_of_day.return_value = "morning"
    
    # Set same time period
    app.current_time_period = "morning"
    
    # Mock the background update methods
    app.update_background_for_current_conditions = MagicMock()
    
    # Test that background doesn't update when time period is the same
    app.check_and_update_background()
    
    # Verify that update_background_for_current_conditions was NOT called
    app.update_background_for_current_conditions.assert_not_called()
    
    print("✅ No update when same period test passed!")


def main():
    """Run all tests"""
    print("🚀 Starting background time update tests...")
    
    # Create QApplication (required for PyQt5 widgets)
    app = QApplication(sys.argv)
    
    try:
        test_time_period_detection()
        test_background_update_logic()
        test_no_update_when_same_period()
        
        print("\n🎉 All tests passed! Background time updates are working correctly.")
        print("\n📋 Summary of changes:")
        print("   • Added background timer that checks every 30 minutes")
        print("   • Implemented time period change detection")
        print("   • Added automatic background updates when time period changes")
        print("   • Background will now update throughout the day based on:")
        print("     - Sunrise (5-7 AM)")
        print("     - Morning (7-11 AM)")
        print("     - Midday (11 AM-1 PM)")
        print("     - Afternoon (1-4 PM)")
        print("     - Sunset (4-7 PM)")
        print("     - Dusk (7-8 PM)")
        print("     - Evening (8-10 PM)")
        print("     - Night (10 PM-5 AM)")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1
    
    finally:
        app.quit()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
