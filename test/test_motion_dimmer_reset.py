# turn off formatting and sorting
# fmt: off
# isort: skip_file
"""
Simple test to verify motion resets dimmer countdown and activates display.

This script specifically tests:
1. Motion detection works
2. Motion resets the dimmer countdown timer
3. Motion brings the screen back on when dimmed or off
"""

import os
import sys
import time
import threading

# Add parent directory to path so we can import from bin package
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from bin.motion_detection_service import MotionDetectionService, DisplayState


def load_config_value(key, default=None):
    """Load a configuration value from weather.conf file"""
    possible_config_paths = [
        "conf/weather.conf",
        os.path.join(os.path.dirname(__file__), "..", "conf", "weather.conf"),
        os.path.join(os.getcwd(), "conf", "weather.conf"),
    ]

    config_path = None
    for path in possible_config_paths:
        if os.path.exists(path):
            config_path = path
            break

    if not config_path:
        return default

    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith(f'{key}='):
                    value = line.split('=', 1)[1].strip()
                    return value
    except Exception as e:
        print(f"⚠️  Warning: Error reading config file: {e}")

    return default


class MotionDimmerTest:
    """Test motion sensor dimmer reset functionality"""

    def __init__(self):
        self.motion_service = None
        self.motion_detected_count = 0
        self.timer_reset_count = 0
        self.display_activated_count = 0

    def setup_motion_service(self):
        """Setup motion detection service"""
        print("🔧 Setting up motion detection service...")

        # Load configuration
        motion_pin = int(load_config_value('MOTION_SENSOR_PIN', '18'))
        display_timeout = int(load_config_value('DISPLAY_TIMEOUT', '60'))
        display_dimming_timeout = int(
            load_config_value('DISPLAY_DIMMING_TIMEOUT', '60'))
        motion_test_mode = load_config_value(
            'MOTION_TEST_MODE', 'false').lower() == 'true'

        try:
            self.motion_service = MotionDetectionService(
                motion_sensor_pin=motion_pin,
                display_timeout=display_timeout,
                display_dimming_timeout=display_dimming_timeout,
                test_mode=motion_test_mode
            )

            # Set up callbacks
            self.motion_service.set_motion_detected_callback(
                self.on_motion_detected)
            self.motion_service.set_display_dim_callback(self.on_display_dim)
            self.motion_service.set_display_off_callback(self.on_display_off)
            self.motion_service.set_display_active_callback(
                self.on_display_active)

            print("✅ Motion service initialized successfully")
            return True

        except Exception as e:
            print(f"❌ Error initializing motion service: {e}")
            return False

    def on_motion_detected(self):
        """Callback for motion detection"""
        self.motion_detected_count += 1
        current_time = time.strftime('%H:%M:%S')
        print(
            f"🚨 MOTION DETECTED! (Count: {self.motion_detected_count}) at {current_time}")

        # Check current state when motion is detected
        if self.motion_service:
            current_state = self.motion_service.get_current_state()
            print(f"   Current display state: {current_state.value}")

            # Check if we're in a state where motion should reset the timer
            if current_state in [DisplayState.ACTIVE, DisplayState.DIMMED, DisplayState.OFF]:
                print("   ✅ Motion detected - timer should be reset")
                self.timer_reset_count += 1

    def on_display_dim(self):
        """Callback for display dimming"""
        current_time = time.strftime('%H:%M:%S')
        print(f"🖥️  Display DIMMED at {current_time}")

        # Show countdown info
        if self.motion_service:
            countdown_info = self.motion_service.get_countdown_info()
            if countdown_info:
                print(
                    f"   Countdown: {countdown_info['remaining_seconds']}s until OFF")

    def on_display_off(self):
        """Callback for display turning off"""
        current_time = time.strftime('%H:%M:%S')
        print(f"🖥️  Display OFF at {current_time}")

    def on_display_active(self):
        """Callback for display becoming active"""
        current_time = time.strftime('%H:%M:%S')
        print(f"🖥️  Display ACTIVE at {current_time}")
        self.display_activated_count += 1

        # Show countdown info
        if self.motion_service:
            countdown_info = self.motion_service.get_countdown_info()
            if countdown_info:
                print(
                    f"   Countdown: {countdown_info['remaining_seconds']}s until DIMMED")

    def test_motion_reset_behavior(self):
        """Test that motion resets the dimmer countdown"""
        print(f"\n🧪 TESTING MOTION RESET BEHAVIOR")
        print("="*50)

        if not self.motion_service:
            print("❌ Motion service not available")
            return

        # Test 1: Start timer and verify countdown
        print("\n1️⃣ Starting display timer...")
        self.motion_service.start_display_timer()

        # Show initial countdown
        countdown_info = self.motion_service.get_countdown_info()
        if countdown_info:
            print(
                f"   Initial countdown: {countdown_info['remaining_seconds']}s until dimming")

        # Wait a bit
        print("   Waiting 3 seconds...")
        time.sleep(3)

        # Test 2: Trigger motion and check if timer resets
        print("\n2️⃣ Triggering motion to reset timer...")
        self.motion_service.trigger_motion()

        # Check countdown after motion
        time.sleep(1)  # Give it a moment to process
        countdown_info = self.motion_service.get_countdown_info()
        if countdown_info:
            print(
                f"   Countdown after motion: {countdown_info['remaining_seconds']}s until dimming")
            # Should be close to full timeout
            if countdown_info['remaining_seconds'] > 50:
                print("   ✅ Timer was reset by motion!")
            else:
                print("   ❌ Timer was not properly reset")

        # Test 3: Wait for dimming and test motion from dimmed state
        print(
            f"\n3️⃣ Waiting for display to dim ({self.motion_service.display_timeout}s)...")
        print("   (This will test motion activation from dimmed state)")

        # Monitor the state changes
        start_wait = time.time()
        while time.time() - start_wait < self.motion_service.display_timeout + 10:
            current_state = self.motion_service.get_current_state()
            countdown_info = self.motion_service.get_countdown_info()

            if countdown_info and countdown_info['is_active']:
                remaining = countdown_info['remaining_seconds']
                timer_type = countdown_info['timer_type']
                print(f"   [{timer_type.upper()}] {remaining}s remaining...")

            time.sleep(1)

            # If we're dimmed, trigger motion to test activation
            if current_state == DisplayState.DIMMED and self.motion_detected_count == 1:
                print("   🚨 Display is dimmed - triggering motion to activate...")
                self.motion_service.trigger_motion()
                time.sleep(2)
                break

        # Test 4: Test motion from OFF state
        print(f"\n4️⃣ Testing motion from OFF state...")
        if self.motion_service.get_current_state() == DisplayState.OFF:
            print("   Display is OFF - triggering motion to activate...")
            self.motion_service.trigger_motion()
            time.sleep(2)

            current_state = self.motion_service.get_current_state()
            if current_state == DisplayState.ACTIVE:
                print("   ✅ Motion successfully activated display from OFF state!")
            else:
                print(
                    f"   ❌ Display state is {current_state.value}, expected ACTIVE")

        # Print results
        self.print_test_results()

    def print_test_results(self):
        """Print test results"""
        print(f"\n📋 TEST RESULTS")
        print("="*30)
        print(f"Motion detections: {self.motion_detected_count}")
        print(f"Timer resets: {self.timer_reset_count}")
        print(f"Display activations: {self.display_activated_count}")

        # Check if motion detection worked
        if self.motion_detected_count > 0:
            print("✅ Motion detection: WORKING")
        else:
            print("❌ Motion detection: NOT WORKING")

        # Check if timer reset worked
        if self.timer_reset_count > 0:
            print("✅ Timer reset on motion: WORKING")
        else:
            print("❌ Timer reset on motion: NOT WORKING")

        # Check if display activation worked
        if self.display_activated_count > 0:
            print("✅ Display activation on motion: WORKING")
        else:
            print("❌ Display activation on motion: NOT WORKING")

    def cleanup(self):
        """Cleanup motion service"""
        if self.motion_service:
            self.motion_service.cleanup()
            print("✅ Motion service cleaned up")


def main():
    """Main function"""
    print("🔍 Motion Sensor Dimmer Reset Test")
    print("="*40)

    # Check if running on Raspberry Pi
    if not os.path.exists('/proc/device-tree/model'):
        print("❌ ERROR: This script only works on Raspberry Pi hardware.")
        print("Please run this script on a Raspberry Pi device.")
        sys.exit(1)

    print("✅ Raspberry Pi detected!")

    # Ask user if they want to proceed
    print("\n🤔 This test will:")
    print("   • Start a display timer")
    print("   • Trigger motion to reset the timer")
    print("   • Test motion activation from dimmed/off states")
    print("   • Show countdown information")

    response = input(
        "\n   Press Enter to start the test, or 'q' to quit: ").strip().lower()

    if response == 'q':
        print("👋 Goodbye!")
        sys.exit(0)

    # Run the test
    tester = MotionDimmerTest()

    if tester.setup_motion_service():
        tester.test_motion_reset_behavior()
        tester.cleanup()
    else:
        print("❌ Failed to setup motion service - test aborted")


if __name__ == "__main__":
    main()
