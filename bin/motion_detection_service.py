"""
Motion Detection Service for Raspberry Pi Weather Display

This service handles motion detection using a PIR sensor connected to GPIO
and provides callbacks for motion events. It includes a test mode for
development without actual hardware.
"""

import os
import time
import threading
from typing import Callable, Optional
from enum import Enum


class DisplayState(Enum):
    """Display states for the motion detection system"""
    ACTIVE = "active"           # Display is fully active
    DIMMED = "dimmed"           # Display is dimmed but visible
    OFF = "off"                 # Display is turned off


class MotionDetectionService:
    """
    Service for handling motion detection and display state management.

    This class manages:
    - GPIO-based motion detection (when not in test mode)
    - Display timeout timers
    - Display state transitions (active -> dimmed -> off)
    - Callbacks for state changes
    """

    def __init__(self,
                 motion_sensor_pin: int = 18,
                 display_timeout: int = 60,
                 display_dimming_timeout: int = 60,
                 test_mode: bool = False):
        """
        Initialize the motion detection service.

        Args:
            motion_sensor_pin: GPIO pin number for motion sensor (BCM numbering)
            display_timeout: Time in seconds before display dims
            display_dimming_timeout: Time in seconds before display turns off after dimming
            test_mode: If True, simulates motion detection without GPIO
        """
        self.motion_sensor_pin = motion_sensor_pin
        self.display_timeout = display_timeout
        self.display_dimming_timeout = display_dimming_timeout
        self.test_mode = test_mode

        # State management
        self.current_state = DisplayState.ACTIVE
        self.motion_detected = False
        self.last_motion_time = time.time()

        # Timers
        self.display_timer = None
        self.dimming_timer = None

        # Timer tracking for countdown display
        self.timer_start_time = None
        self.current_timer_duration = None
        self.timer_type = None  # 'dimming' or 'off'

        # Callbacks
        self.on_motion_detected: Optional[Callable] = None
        self.on_display_dim: Optional[Callable] = None
        self.on_display_off: Optional[Callable] = None
        self.on_display_active: Optional[Callable] = None
        self.on_countdown_update: Optional[Callable] = None

        # GPIO setup (only if not in test mode)
        self.gpio_available = False
        if not self.test_mode:
            self._setup_gpio()

        # Start the motion detection thread
        self._start_motion_detection()

        print(f"🔍 MotionDetectionService initialized:")
        print(f"   Pin: {self.motion_sensor_pin}")
        print(f"   Display timeout: {self.display_timeout}s")
        print(f"   Dimming timeout: {self.display_dimming_timeout}s")
        print(f"   Test mode: {self.test_mode}")
        print(f"   GPIO available: {self.gpio_available}")

    def _setup_gpio(self):
        """Setup GPIO for motion sensor (Raspberry Pi only)"""
        try:
            import RPi.GPIO as GPIO

            # Set GPIO mode to BCM
            GPIO.setmode(GPIO.BCM)

            # Setup motion sensor pin as input with pull-down resistor
            GPIO.setup(self.motion_sensor_pin, GPIO.IN,
                       pull_up_down=GPIO.PUD_DOWN)

            # Add interrupt for motion detection
            GPIO.add_event_detect(
                self.motion_sensor_pin,
                GPIO.RISING,
                callback=self._motion_callback,
                bouncetime=200  # 200ms debounce
            )

            self.gpio_available = True
            print(f"✅ GPIO setup successful on pin {self.motion_sensor_pin}")

        except ImportError:
            print("⚠️  RPi.GPIO not available - running in test mode")
            self.test_mode = True
            self.gpio_available = False
        except Exception as e:
            print(f"⚠️  GPIO setup failed: {e} - running in test mode")
            self.test_mode = True
            self.gpio_available = False

    def _motion_callback(self, channel):
        """GPIO callback for motion detection"""
        if not self.motion_detected:  # Avoid duplicate triggers
            self.motion_detected = True
            self.last_motion_time = time.time()
            print("🔍 Motion detected via GPIO!")

            # Trigger motion detected callback
            if self.on_motion_detected:
                self.on_motion_detected()

            # Reset the flag after a short delay to allow for new motion detection
            def reset_motion_flag():
                time.sleep(1)  # Wait 1 second
                self.motion_detected = False

            import threading
            threading.Thread(target=reset_motion_flag, daemon=True).start()

    def _start_motion_detection(self):
        """Start the motion detection thread"""
        if self.test_mode:
            # In test mode, simulate motion every 30 seconds for testing
            def test_motion_simulator():
                try:
                    while True:
                        time.sleep(30)  # Simulate motion every 30 seconds
                        if not self.motion_detected:
                            self.motion_detected = True
                            self.last_motion_time = time.time()
                            print("🔍 [TEST] Simulated motion detected!")

                            # Trigger motion detected callback
                            if self.on_motion_detected:
                                try:
                                    self.on_motion_detected()
                                except Exception as e:
                                    print(f"⚠️  Error in motion callback: {e}")

                            # Reset the flag after a short delay to allow for new motion detection
                            def reset_motion_flag():
                                time.sleep(1)  # Wait 1 second
                                self.motion_detected = False

                            threading.Thread(
                                target=reset_motion_flag, daemon=True).start()
                except Exception as e:
                    print(f"⚠️  Error in motion simulator thread: {e}")

            test_thread = threading.Thread(
                target=test_motion_simulator, daemon=True, name="MotionSimulator")
            test_thread.start()
            print("🧪 Test mode motion simulator started")

    def set_motion_detected_callback(self, callback: Callable):
        """Set callback for when motion is detected"""
        self.on_motion_detected = callback

    def set_display_dim_callback(self, callback: Callable):
        """Set callback for when display should dim"""
        self.on_display_dim = callback

    def set_display_off_callback(self, callback: Callable):
        """Set callback for when display should turn off"""
        self.on_display_off = callback

    def set_display_active_callback(self, callback: Callable):
        """Set callback for when display should become active"""
        self.on_display_active = callback

    def set_countdown_update_callback(self, callback: Callable):
        """Set callback for countdown updates"""
        self.on_countdown_update = callback

    def trigger_motion(self):
        """
        Manually trigger motion detection (useful for testing or external triggers)
        """
        self.motion_detected = True
        self.last_motion_time = time.time()
        print("🔍 Motion manually triggered!")

        # Trigger motion detected callback
        if self.on_motion_detected:
            self.on_motion_detected()

    def reset_dimming_timer(self):
        """Reset the dimming timer (called on mouse movement or touch)"""
        print("🔄 Resetting dimming timer due to user interaction")
        if self.current_state == DisplayState.ACTIVE:
            # Only reset if we're in active state
            self.start_display_timer()
        elif self.current_state == DisplayState.DIMMED:
            # If dimmed, go back to active and restart timer
            self._set_display_state(DisplayState.ACTIVE)
            self.start_display_timer()
        elif self.current_state == DisplayState.OFF:
            # If off, turn back on and restart timer
            self._set_display_state(DisplayState.ACTIVE)
            self.start_display_timer()

    def get_countdown_info(self):
        """Get current countdown information for display"""
        if not self.timer_start_time or not self.current_timer_duration:
            return None

        elapsed = time.time() - self.timer_start_time
        remaining = max(0, self.current_timer_duration - elapsed)

        return {
            'remaining_seconds': int(remaining),
            'timer_type': self.timer_type,
            'is_active': remaining > 0
        }

    def start_display_timer(self):
        """Start the display timeout timer"""
        self._cancel_timers()

        if self.current_state == DisplayState.OFF:
            # If display is off, turn it back on
            self._set_display_state(DisplayState.ACTIVE)

        # Track timer information for countdown display
        self.timer_start_time = time.time()
        self.current_timer_duration = self.display_timeout
        self.timer_type = 'dimming'

        # Start timer for dimming
        self.display_timer = threading.Timer(
            self.display_timeout,
            self._on_display_timeout
        )
        self.display_timer.start()

        print(
            f"⏰ Display timer started ({self.display_timeout}s until dimming)")

    def _on_display_timeout(self):
        """Called when display timeout is reached"""
        print("⏰ Display timeout reached - dimming display")
        self._set_display_state(DisplayState.DIMMED)

        # Track timer information for countdown display
        self.timer_start_time = time.time()
        self.current_timer_duration = self.display_dimming_timeout
        self.timer_type = 'off'

        # Start timer for turning off
        self.dimming_timer = threading.Timer(
            self.display_dimming_timeout,
            self._on_dimming_timeout
        )
        self.dimming_timer.start()

        print(
            f"⏰ Dimming timer started ({self.display_dimming_timeout}s until off)")

    def _on_dimming_timeout(self):
        """Called when dimming timeout is reached"""
        print("⏰ Dimming timeout reached - turning off display")
        self._set_display_state(DisplayState.OFF)

    def _set_display_state(self, new_state: DisplayState):
        """Set the display state and trigger appropriate callbacks"""
        if self.current_state == new_state:
            return

        old_state = self.current_state
        self.current_state = new_state

        print(f"🖥️  Display state: {old_state.value} -> {new_state.value}")

        # Trigger appropriate callback
        if new_state == DisplayState.ACTIVE and self.on_display_active:
            self.on_display_active()
        elif new_state == DisplayState.DIMMED and self.on_display_dim:
            self.on_display_dim()
        elif new_state == DisplayState.OFF and self.on_display_off:
            self.on_display_off()

    def _cancel_timers(self):
        """Cancel all active timers"""
        if self.display_timer:
            self.display_timer.cancel()
            self.display_timer = None

        if self.dimming_timer:
            self.dimming_timer.cancel()
            self.dimming_timer = None

        # Clear countdown tracking
        self.timer_start_time = None
        self.current_timer_duration = None
        self.timer_type = None

    def get_current_state(self) -> DisplayState:
        """Get the current display state"""
        return self.current_state

    def is_display_active(self) -> bool:
        """Check if display is currently active"""
        return self.current_state == DisplayState.ACTIVE

    def is_display_dimmed(self) -> bool:
        """Check if display is currently dimmed"""
        return self.current_state == DisplayState.DIMMED

    def is_display_off(self) -> bool:
        """Check if display is currently off"""
        return self.current_state == DisplayState.OFF

    def cleanup(self):
        """Cleanup GPIO and timers"""
        self._cancel_timers()

        if self.gpio_available:
            try:
                import RPi.GPIO as GPIO
                GPIO.cleanup()
                print("✅ GPIO cleanup completed")
            except Exception as e:
                print(f"⚠️  GPIO cleanup failed: {e}")

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()
