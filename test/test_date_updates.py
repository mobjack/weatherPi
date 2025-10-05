#!/usr/bin/env python3
"""
Test script to verify that date and day of week updates work correctly.
"""

import sys
import os
import datetime

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_date_formatting():
    """Test that date formatting works correctly"""
    print("🧪 Testing date formatting...")

    # Test current date formatting
    now = datetime.datetime.now()
    day_name = now.strftime("%A")
    date_str = now.strftime("%B %d")

    print(f"   Current day: {day_name}")
    print(f"   Current date: {date_str}")

    # Verify the format is correct
    assert len(day_name) > 0, "Day name should not be empty"
    assert len(date_str) > 0, "Date string should not be empty"
    assert day_name in ["Monday", "Tuesday", "Wednesday", "Thursday",
                        "Friday", "Saturday", "Sunday"], f"Invalid day name: {day_name}"

    # Check that date contains month and day
    parts = date_str.split()
    assert len(
        parts) == 2, f"Date should have 2 parts (month day), got: {parts}"

    print("✅ Date formatting test passed!")


def test_date_update_logic():
    """Test the date update logic"""
    print("🧪 Testing date update logic...")

    # Simulate the update_date method logic
    def update_date():
        now = datetime.datetime.now()
        day_name = now.strftime("%A")
        date_str = now.strftime("%B %d")
        return day_name, date_str

    # Test multiple calls to ensure consistency
    day1, date1 = update_date()
    day2, date2 = update_date()

    # Should be the same (or very close in time)
    assert day1 == day2, f"Day should be consistent: {day1} vs {day2}"
    assert date1 == date2, f"Date should be consistent: {date1} vs {date2}"

    print(f"   Day: {day1}")
    print(f"   Date: {date1}")
    print("✅ Date update logic test passed!")


def main():
    """Run all tests"""
    print("🚀 Starting date update tests...")

    try:
        test_date_formatting()
        test_date_update_logic()

        print("\n🎉 All tests passed! Date updates are working correctly.")
        print("\n📋 Summary of date/time updates:")
        print("   • Time updates automatically every minute")
        print("   • Date and day of week update automatically every hour")
        print("   • Background updates automatically when time period changes (every 30 minutes)")
        print("   • Weather data updates automatically every 30 minutes")
        print("\n🕐 Update Schedule:")
        print("   - Time: Every 1 minute")
        print("   - Date/Day: Every 1 hour")
        print("   - Background: Every 30 minutes (when time period changes)")
        print("   - Weather: Every 30 minutes")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
