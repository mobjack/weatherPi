#!/usr/bin/env python3
"""
Motion sensor test script for Raspberry Pi.
This script only runs on Raspberry Pi hardware.
"""

import os
import sys
import platform
import time


def detect_raspberry_pi():
    """
    Detect if the current system is a Raspberry Pi.
    Returns True if running on Raspberry Pi, False otherwise.
    """
    try:
        # Check for Raspberry Pi specific files
        if os.path.exists('/proc/device-tree/model'):
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read().strip()
                if 'Raspberry Pi' in model:
                    return True

        # Check for Raspberry Pi in cpuinfo
        if os.path.exists('/proc/cpuinfo'):
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'Raspberry Pi' in cpuinfo or 'BCM' in cpuinfo:
                    return True

        # Check system platform
        if platform.system() == 'Linux':
            # Additional check for ARM architecture (common on Raspberry Pi)
            machine = platform.machine()
            if machine.startswith('arm') or machine.startswith('aarch64'):
                # Check if it's actually a Raspberry Pi by looking for specific hardware
                if os.path.exists('/proc/device-tree/compatible'):
                    with open('/proc/device-tree/compatible', 'r') as f:
                        compatible = f.read()
                        if 'raspberrypi' in compatible:
                            return True

        return False
    except Exception as e:
        print(f"Error detecting Raspberry Pi: {e}")
        return False


def load_config_value(key, default=None):
    """Load a configuration value from weather.conf file"""
    # Try to find the config file in multiple locations
    possible_config_paths = [
        "conf/weather.conf",  # Relative to current directory
        os.path.join(os.path.dirname(__file__), "..", "conf",
                     "weather.conf"),  # Relative to script location
        # Relative to working directory
        os.path.join(os.getcwd(), "conf", "weather.conf"),
    ]

    config_path = None
    for path in possible_config_paths:
        if os.path.exists(path):
            config_path = path
            break

    if not config_path:
        print(
            f"⚠️  Warning: Could not find weather.conf, using default value for {key}")
        return default

    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith(f'{key}='):
                    value = line.split('=', 1)[1].strip()
                    return value
    except Exception as e:
        print(f"⚠️  Warning: Error reading config file {config_path}: {e}")

    return default


def display_motion_sensor_config():
    """Display motion sensor configuration with ASCII art"""
    print("\n" + "="*60)
    print("🔧 MOTION SENSOR CONFIGURATION")
    print("="*60)

    # Load motion sensor pin from config
    motion_pin = int(load_config_value('MOTION_SENSOR_PIN', '18'))

    print(f"\n📍 Motion Sensor Pin: GPIO {motion_pin} (BCM numbering)")
    print("\n🔌 Raspberry Pi GPIO Pin Layout:")
    print("   (Physical pin numbers in parentheses)")
    print()

    # ASCII art for Raspberry Pi GPIO layout
    print("    3V3  (1) (2)  5V")
    print(f"  GPIO2  (3) (4)  5V")
    print(f"  GPIO3  (5) (6)  GND")
    print(f"  GPIO4  (7) (8)  GPIO14")
    print("    GND  (9) (10) GPIO15")
    print(f" GPIO17 (11) (12) GPIO18  ← MOTION SENSOR")
    print(f" GPIO27 (13) (14) GND")
    print(f" GPIO22 (15) (16) GPIO23")
    print("    3V3 (17) (18) GPIO24")
    print(f" GPIO10 (19) (20) GND")
    print(f"  GPIO9 (21) (22) GPIO25")
    print(f" GPIO11 (23) (24) GPIO8")
    print("    GND (25) (26) GPIO7")
    print()
    print("🔌 Motion Sensor Wiring:")
    print("   ┌─────────────────┐")
    print("   │   PIR Sensor    │")
    print("   │                 │")
    print("   │  VCC  OUT  GND  │")
    print("   └─┬───┬───┬───────┘")
    print("      │   │   │")
    print("      │   │   └─── GND (Pin 6)")
    # GPIO to physical pin mapping for common pins
    gpio_to_physical = {
        2: 3, 3: 5, 4: 7, 14: 8, 15: 10, 17: 11, 18: 12, 27: 13, 22: 15, 23: 16, 24: 18, 10: 19, 9: 21, 25: 22, 11: 23, 8: 24, 7: 26
    }
    physical_pin = gpio_to_physical.get(motion_pin, f"Unknown")

    print(f"      │   └─────── GPIO{motion_pin} (Pin {physical_pin})")
    print("      └─────────── 5V (Pin 2)")
    print()
    print("📋 Connection Summary:")
    print(f"   • VCC (Red)    → 5V (Pin 2)")
    print(f"   • OUT (Yellow) → GPIO{motion_pin} (Pin {physical_pin})")
    print("   • GND (Black)  → GND (Pin 6)")
    print()
    print("⚠️  IMPORTANT:")
    print("   • Make sure the PIR sensor is powered with 5V")
    print("   • The output pin can handle 3.3V logic")
    print("   • Double-check all connections before powering on")
    print("   • Some PIR sensors have adjustable sensitivity and delay")
    print()


def test_motion_sensor():
    """Test the motion sensor functionality"""
    print("\n" + "="*60)
    print("🔍 MOTION SENSOR TEST")
    print("="*60)

    # Import RPi.GPIO only after confirming we're on Raspberry Pi
    try:
        import RPi.GPIO as GPIO
        print("✅ RPi.GPIO library imported successfully")
    except ImportError as e:
        print(f"❌ Error importing RPi.GPIO: {e}")
        print("   This library is only available on Raspberry Pi systems")
        return

    # Load motion sensor pin from config
    motion_pin = int(load_config_value('MOTION_SENSOR_PIN', '18'))

    try:
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(motion_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        print(
            f"✅ GPIO {motion_pin} configured as input with pull-down resistor")
        print("\n🔍 Motion sensor is now active!")
        print("   Wave your hand in front of the sensor to test")
        print("   Press Ctrl+C to stop the test")
        print("\n" + "-"*40)

        motion_count = 0
        last_motion_time = 0

        while True:
            # Read motion sensor
            motion_detected = GPIO.input(motion_pin)

            if motion_detected:
                current_time = time.time()
                # Only count motion if it's been more than 10 seconds since last detection
                if current_time - last_motion_time > 10:
                    motion_count += 1
                    last_motion_time = current_time
                    print(f"🚨 MOTION DETECTED! (Count: {motion_count})")
                    print(f"   Time: {time.strftime('%H:%M:%S')}")
                    print("   Waiting 10 seconds before next detection...")
                    print("-"*40)

                    # Sleep for 10 seconds as requested
                    time.sleep(10)
                else:
                    # Still motion detected but within cooldown period
                    time.sleep(0.1)
            else:
                # No motion detected, short sleep to avoid high CPU usage
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\n🛑 Test stopped by user")
        print(f"📊 Total motion detections: {motion_count}")

    except Exception as e:
        print(f"\n❌ Error during motion sensor test: {e}")
        print("   Check your wiring and GPIO configuration")

    finally:
        # Cleanup GPIO
        try:
            GPIO.cleanup()
            print("✅ GPIO cleaned up successfully")
        except:
            pass


def main():
    """
    Main function to check if running on Raspberry Pi and run motion sensor test.
    """
    print("🔍 Motion Sensor Test for Raspberry Pi")
    print("="*50)

    # Check if running on Raspberry Pi
    print("Checking system compatibility...")

    if not detect_raspberry_pi():
        print("❌ ERROR: This script only works on Raspberry Pi hardware.")
        print("Current system detected:")
        print(f"  - OS: {platform.system()}")
        print(f"  - Architecture: {platform.machine()}")
        print(f"  - Platform: {platform.platform()}")
        print("\nPlease run this script on a Raspberry Pi device.")
        sys.exit(1)

    print("✅ Raspberry Pi detected!")
    print(f"  - OS: {platform.system()}")
    print(f"  - Architecture: {platform.machine()}")
    print(f"  - Platform: {platform.platform()}")

    # Display motion sensor configuration
    display_motion_sensor_config()

    # Ask user if they want to proceed with the test
    print("🤔 Ready to test the motion sensor?")
    print("   Make sure your PIR sensor is connected according to the diagram above.")
    response = input(
        "   Press Enter to start the test, or 'q' to quit: ").strip().lower()

    if response == 'q':
        print("👋 Goodbye!")
        sys.exit(0)

    # Run the motion sensor test
    test_motion_sensor()


if __name__ == "__main__":
    main()
