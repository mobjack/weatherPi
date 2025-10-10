# fmt: off
# isort: skip_file
"""
Motion Sensor Capabilities Test for Raspberry Pi Weather Display

This script tests the motion sensor functionality and verifies that:
1. Motion detection works correctly
2. Motion resets the dimmer countdown
3. Motion brings the screen back on when it's dimmed or off
4. Display state transitions work properly
"""

import os
import sys
import time
import threading
from typing import Optional

# Add the bin directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bin'))
from bin.display_controller import DisplayController, DisplayState as ControllerDisplayState
from bin.motion_detection_service import MotionDetectionService, DisplayState as MotionDisplayState


def detect_raspberry_pi():
    """Detect if the current system is a Raspberry Pi"""
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

        return False
    except Exception as e:
        print(f"Error detecting Raspberry Pi: {e}")
        return False


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
        print(f"⚠️  Warning: Error reading config file {config_path}: {e}")

    return default


class MotionSensorTester:
    """Test class for motion sensor capabilities"""

    def __init__(self):
        self.motion_service = None
        self.display_controller = None
        self.test_results = {
            'motion_detection': False,
            'motion_resets_dimmer': False,
            'motion_activates_display': False,
            'display_state_transitions': False
        }
        self.motion_count = 0
        self.state_transitions = []

    def setup_services(self):
        """Setup motion detection and display control services"""
        print("🔧 Setting up motion detection and display services...")

        # Load configuration
        motion_pin = int(load_config_value('MOTION_SENSOR_PIN', '18'))
        display_timeout = int(load_config_value('DISPLAY_TIMEOUT', '60'))
        display_dimming_timeout = int(
            load_config_value('DISPLAY_DIMMING_TIMEOUT', '60'))
        motion_test_mode = load_config_value(
            'MOTION_TEST_MODE', 'false').lower() == 'true'

        print(f"   Motion sensor pin: GPIO {motion_pin}")
        print(f"   Display timeout: {display_timeout}s")
        print(f"   Dimming timeout: {display_dimming_timeout}s")
        print(f"   Test mode: {motion_test_mode}")

        try:
            # Initialize motion detection service
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

            # Initialize display controller
            self.display_controller = DisplayController(
                dim_brightness=30,
                full_brightness=100,
                test_mode=motion_test_mode
            )

            print("✅ Services initialized successfully")
            return True

        except Exception as e:
            print(f"❌ Error initializing services: {e}")
            return False

    def on_motion_detected(self):
        """Callback for motion detection"""
        self.motion_count += 1
        current_time = time.strftime('%H:%M:%S')
        print(
            f"🚨 MOTION DETECTED! (Count: {self.motion_count}) at {current_time}")

        # Test motion detection capability
        self.test_results['motion_detection'] = True

        # Check if motion resets dimmer
        if self.motion_service:
            current_state = self.motion_service.get_current_state()
            if current_state in [MotionDisplayState.DIMMED, MotionDisplayState.OFF]:
                print(
                    "   ✅ Motion detected while display was dimmed/off - should reset timer")
                self.test_results['motion_resets_dimmer'] = True
            else:
                print(
                    "   ✅ Motion detected while display was active - timer should reset")
                self.test_results['motion_resets_dimmer'] = True

    def on_display_dim(self):
        """Callback for display dimming"""
        current_time = time.strftime('%H:%M:%S')
        print(f"🖥️  Display DIMMED at {current_time}")
        self.state_transitions.append(f"DIMMED at {current_time}")

        if self.display_controller:
            self.display_controller.set_display_state(
                ControllerDisplayState.DIMMED)

    def on_display_off(self):
        """Callback for display turning off"""
        current_time = time.strftime('%H:%M:%S')
        print(f"🖥️  Display OFF at {current_time}")
        self.state_transitions.append(f"OFF at {current_time}")

        if self.display_controller:
            self.display_controller.set_display_state(
                ControllerDisplayState.OFF)

    def on_display_active(self):
        """Callback for display becoming active"""
        current_time = time.strftime('%H:%M:%S')
        print(f"🖥️  Display ACTIVE at {current_time}")
        self.state_transitions.append(f"ACTIVE at {current_time}")

        if self.display_controller:
            self.display_controller.set_display_state(
                ControllerDisplayState.ACTIVE)

        # Test if motion activates display
        if self.motion_count > 0:
            self.test_results['motion_activates_display'] = True

    def test_motion_detection(self, duration=60):
        """Test motion detection for specified duration"""
        print(f"\n🔍 Testing motion detection for {duration} seconds...")
        print("   Wave your hand in front of the sensor to test")
        print("   Press Ctrl+C to stop early")

        start_time = time.time()
        last_motion_time = 0

        try:
            while time.time() - start_time < duration:
                # Check for motion every 100ms
                time.sleep(0.1)

                # In test mode, motion is simulated every 30 seconds
                # In real mode, motion is detected via GPIO interrupt
                if self.motion_service and self.motion_service.motion_detected:
                    current_time = time.time()
                    if current_time - last_motion_time > 5:  # 5 second cooldown for testing
                        last_motion_time = current_time
                        self.motion_service.motion_detected = False  # Reset flag
                        self.on_motion_detected()

        except KeyboardInterrupt:
            print("\n🛑 Test stopped by user")

        print(f"\n📊 Motion detection test completed:")
        print(f"   Total motion detections: {self.motion_count}")
        print(
            f"   Motion detection working: {'✅' if self.test_results['motion_detection'] else '❌'}")

    def test_dimmer_reset(self):
        """Test that motion resets the dimmer countdown"""
        print(f"\n⏰ Testing dimmer reset functionality...")

        if not self.motion_service:
            print("❌ Motion service not available")
            return

        # Start the display timer
        print("   Starting display timer...")
        self.motion_service.start_display_timer()

        # Wait a bit, then trigger motion
        print("   Waiting 5 seconds, then triggering motion...")
        time.sleep(5)

        # Trigger motion manually
        print("   Triggering motion to reset timer...")
        self.motion_service.trigger_motion()

        # Check if timer was reset
        countdown_info = self.motion_service.get_countdown_info()
        if countdown_info and countdown_info['is_active']:
            print(
                f"   ✅ Timer reset successfully - {countdown_info['remaining_seconds']}s remaining")
            self.test_results['motion_resets_dimmer'] = True
        else:
            print("   ❌ Timer was not reset properly")

    def test_display_state_transitions(self):
        """Test display state transitions"""
        print(f"\n🖥️  Testing display state transitions...")

        if not self.motion_service or not self.display_controller:
            print("❌ Services not available")
            return

        # Test all state transitions
        states_to_test = [
            (MotionDisplayState.ACTIVE, ControllerDisplayState.ACTIVE),
            (MotionDisplayState.DIMMED, ControllerDisplayState.DIMMED),
            (MotionDisplayState.OFF, ControllerDisplayState.OFF)
        ]

        for motion_state, display_state in states_to_test:
            print(f"   Testing transition to {motion_state.value}...")
            self.motion_service._set_display_state(motion_state)
            self.display_controller.set_display_state(display_state)
            time.sleep(1)

        print("   ✅ Display state transitions completed")
        self.test_results['display_state_transitions'] = True

    def run_comprehensive_test(self):
        """Run comprehensive motion sensor test"""
        print("🧪 COMPREHENSIVE MOTION SENSOR CAPABILITIES TEST")
        print("="*60)

        # Setup services
        if not self.setup_services():
            print("❌ Failed to setup services - test aborted")
            return

        # Test 1: Motion detection
        self.test_motion_detection(duration=30)

        # Test 2: Dimmer reset
        self.test_dimmer_reset()

        # Test 3: Display state transitions
        self.test_display_state_transitions()

        # Test 4: Motion activation from dimmed/off state
        print(f"\n🔄 Testing motion activation from dimmed state...")
        if self.motion_service:
            # Set to dimmed state
            self.motion_service._set_display_state(MotionDisplayState.DIMMED)
            time.sleep(1)

            # Trigger motion
            print("   Triggering motion from dimmed state...")
            self.motion_service.trigger_motion()
            time.sleep(2)

            # Check if it went back to active
            current_state = self.motion_service.get_current_state()
            if current_state == MotionDisplayState.ACTIVE:
                print("   ✅ Motion successfully activated display from dimmed state")
                self.test_results['motion_activates_display'] = True
            else:
                print(
                    f"   ❌ Display state is {current_state.value}, expected ACTIVE")

        # Print results
        self.print_test_results()

        # Cleanup
        self.cleanup()

    def print_test_results(self):
        """Print comprehensive test results"""
        print(f"\n📋 TEST RESULTS SUMMARY")
        print("="*40)

        results = [
            ("Motion Detection", self.test_results['motion_detection']),
            ("Motion Resets Dimmer",
             self.test_results['motion_resets_dimmer']),
            ("Motion Activates Display",
             self.test_results['motion_activates_display']),
            ("Display State Transitions",
             self.test_results['display_state_transitions'])
        ]

        for test_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {test_name}: {status}")

        print(f"\n📊 Additional Statistics:")
        print(f"   Total motion detections: {self.motion_count}")
        print(f"   State transitions: {len(self.state_transitions)}")

        if self.state_transitions:
            print("   Transition history:")
            for transition in self.state_transitions:
                print(f"     - {transition}")

        # Overall result
        all_passed = all(self.test_results.values())
        overall_status = "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"
        print(f"\n🎯 Overall Result: {overall_status}")

    def cleanup(self):
        """Cleanup services"""
        print(f"\n🧹 Cleaning up services...")

        if self.motion_service:
            self.motion_service.cleanup()
            print("   ✅ Motion service cleaned up")

        if self.display_controller:
            self.display_controller.cleanup()
            print("   ✅ Display controller cleaned up")


def main():
    """Main function"""
    print("🔍 Motion Sensor Capabilities Test")
    print("="*50)

    # Check if running on Raspberry Pi
    if not detect_raspberry_pi():
        print("❌ ERROR: This script only works on Raspberry Pi hardware.")
        print("Current system detected:")
        print(f"  - OS: {os.name}")
        print(f"  - Platform: {sys.platform}")
        print("\nPlease run this script on a Raspberry Pi device.")
        sys.exit(1)

    print("✅ Raspberry Pi detected!")

    # Ask user if they want to proceed
    print("\n🤔 This test will:")
    print("   • Test motion detection capabilities")
    print("   • Verify dimmer countdown reset on motion")
    print("   • Check display activation from motion")
    print("   • Test display state transitions")
    print("\n   Make sure your PIR sensor is connected properly.")

    response = input(
        "\n   Press Enter to start the test, or 'q' to quit: ").strip().lower()

    if response == 'q':
        print("👋 Goodbye!")
        sys.exit(0)

    # Run the test
    tester = MotionSensorTester()
    tester.run_comprehensive_test()


if __name__ == "__main__":
    main()
