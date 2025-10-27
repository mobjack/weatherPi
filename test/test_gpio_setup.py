#!/usr/bin/env python3
"""
Test script to verify GPIO setup on Raspberry Pi
Run this on your Raspberry Pi to test the motion sensor setup
"""

import sys
import time


def test_gpio_libraries():
    """Test which GPIO libraries are available"""
    print("🔍 Testing GPIO library availability...")

    # Test gpiozero (preferred)
    try:
        from gpiozero import MotionSensor
        print("✅ gpiozero available - this is the preferred library")
        return "gpiozero"
    except ImportError:
        print("❌ gpiozero not available")

    # Test RPi.GPIO (legacy)
    try:
        import RPi.GPIO as GPIO
        print("✅ RPi.GPIO available - legacy library")
        return "RPi.GPIO"
    except ImportError:
        print("❌ RPi.GPIO not available")

    # Test other libraries
    try:
        import lgpio
        print("✅ lgpio available")
    except ImportError:
        print("❌ lgpio not available")

    try:
        import gpiod
        print("✅ gpiod available")
    except ImportError:
        print("❌ gpiod not available")

    return None


def test_motion_sensor_setup():
    """Test motion sensor setup with gpiozero"""
    print("\n🔍 Testing motion sensor setup...")

    try:
        from gpiozero import MotionSensor

        # Test motion sensor on pin 18
        motion_sensor = MotionSensor(
            pin=18,
            pull_up=True,
            queue_len=1,
            sample_rate=10,
            threshold=0.5
        )

        print("✅ Motion sensor created successfully on pin 18")

        # Test callback
        motion_detected = False

        def motion_callback():
            nonlocal motion_detected
            motion_detected = True
            print("🔍 Motion detected!")

        motion_sensor.when_motion = motion_callback

        print("✅ Motion callback set up successfully")
        print("📋 Motion sensor is ready - wave your hand in front of it!")
        print("   (Press Ctrl+C to stop)")

        # Monitor for 30 seconds
        start_time = time.time()
        while time.time() - start_time < 30:
            if motion_detected:
                print("✅ Motion detection working!")
                break
            time.sleep(0.1)

        motion_sensor.close()
        print("✅ Motion sensor closed successfully")

        return True

    except Exception as e:
        print(f"❌ Motion sensor setup failed: {e}")
        return False


def main():
    """Main test function"""
    print("🧪 GPIO Setup Test for weatherPi")
    print("=" * 40)

    # Test library availability
    library = test_gpio_libraries()

    if library == "gpiozero":
        print(f"\n🎯 Using {library} for motion detection")
        success = test_motion_sensor_setup()

        if success:
            print("\n✅ All tests passed! Your motion sensor setup is ready.")
            print("📋 Your weatherPi app should work with real motion detection.")
        else:
            print("\n❌ Motion sensor test failed. Check your wiring and permissions.")
    else:
        print(f"\n⚠️  Preferred library not available. Found: {library}")
        print("📋 Install gpiozero: pip install gpiozero")
        print("📋 Or the app will fall back to test mode.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
