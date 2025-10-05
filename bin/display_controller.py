"""
Display Controller for Raspberry Pi Weather Display

This controller handles display brightness, dimming, and shutdown operations
for the weather display system. It provides methods to control the display
state based on motion detection events.
"""

import os
import subprocess
import time
from typing import Optional
from enum import Enum


class DisplayState(Enum):
    """Display states for the display controller"""
    ACTIVE = "active"           # Display is fully active
    DIMMED = "dimmed"           # Display is dimmed but visible
    OFF = "off"                 # Display is turned off


class DisplayController:
    """
    Controller for managing display brightness and power states.
    
    This class handles:
    - Display brightness control
    - Display dimming
    - Display power management (on/off)
    - Backlight control for Raspberry Pi displays
    """
    
    def __init__(self, 
                 dim_brightness: int = 30,
                 full_brightness: int = 100,
                 test_mode: bool = False):
        """
        Initialize the display controller.
        
        Args:
            dim_brightness: Brightness level when dimmed (0-100)
            full_brightness: Full brightness level (0-100)
            test_mode: If True, simulates display control without actual hardware
        """
        self.dim_brightness = max(0, min(100, dim_brightness))
        self.full_brightness = max(0, min(100, full_brightness))
        self.test_mode = test_mode
        self.current_state = DisplayState.ACTIVE
        self.current_brightness = self.full_brightness
        
        # Detect display type and setup
        self.display_type = self._detect_display_type()
        self._setup_display()
        
        print(f"🖥️  DisplayController initialized:")
        print(f"   Display type: {self.display_type}")
        print(f"   Full brightness: {self.full_brightness}%")
        print(f"   Dim brightness: {self.dim_brightness}%")
        print(f"   Test mode: {self.test_mode}")
    
    def _detect_display_type(self) -> str:
        """Detect the type of display being used"""
        if self.test_mode:
            return "test"
        
        # Check for official Raspberry Pi touchscreen
        if os.path.exists("/sys/class/backlight/rpi_backlight"):
            return "rpi_touchscreen"
        
        # Check for HDMI display
        try:
            result = subprocess.run(
                ["tvservice", "-s"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode == 0 and "HDMI" in result.stdout:
                return "hdmi"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Check for DSI display
        if os.path.exists("/sys/class/backlight/10-0045"):
            return "dsi"
        
        # Default fallback
        return "unknown"
    
    def _setup_display(self):
        """Setup display based on detected type"""
        if self.test_mode:
            print("🧪 Test mode: Display control simulated")
            return
        
        if self.display_type == "rpi_touchscreen":
            self._setup_rpi_touchscreen()
        elif self.display_type == "hdmi":
            self._setup_hdmi_display()
        elif self.display_type == "dsi":
            self._setup_dsi_display()
        else:
            print(f"⚠️  Unknown display type: {self.display_type}")
            print("   Display control may not work properly")
    
    def _setup_rpi_touchscreen(self):
        """Setup Raspberry Pi official touchscreen"""
        try:
            # Check if backlight control is available
            if os.path.exists("/sys/class/backlight/rpi_backlight/brightness"):
                print("✅ Raspberry Pi touchscreen detected")
            else:
                print("⚠️  Raspberry Pi touchscreen backlight control not available")
        except Exception as e:
            print(f"⚠️  Error setting up Raspberry Pi touchscreen: {e}")
    
    def _setup_hdmi_display(self):
        """Setup HDMI display"""
        try:
            print("✅ HDMI display detected")
            # HDMI displays typically don't support brightness control
            # but we can use tvservice for power management
        except Exception as e:
            print(f"⚠️  Error setting up HDMI display: {e}")
    
    def _setup_dsi_display(self):
        """Setup DSI display"""
        try:
            print("✅ DSI display detected")
        except Exception as e:
            print(f"⚠️  Error setting up DSI display: {e}")
    
    def set_brightness(self, brightness: int):
        """
        Set display brightness.
        
        Args:
            brightness: Brightness level (0-100)
        """
        brightness = max(0, min(100, brightness))
        self.current_brightness = brightness
        
        if self.test_mode:
            print(f"🧪 [TEST] Setting brightness to {brightness}%")
            return
        
        try:
            if self.display_type == "rpi_touchscreen":
                self._set_rpi_touchscreen_brightness(brightness)
            elif self.display_type == "dsi":
                self._set_dsi_brightness(brightness)
            else:
                print(f"⚠️  Brightness control not supported for {self.display_type}")
                
        except Exception as e:
            print(f"❌ Error setting brightness: {e}")
    
    def _set_rpi_touchscreen_brightness(self, brightness: int):
        """Set brightness for Raspberry Pi touchscreen"""
        try:
            # Convert percentage to 0-255 range
            brightness_value = int((brightness / 100) * 255)
            
            with open("/sys/class/backlight/rpi_backlight/brightness", "w") as f:
                f.write(str(brightness_value))
            
            print(f"✅ Set Raspberry Pi touchscreen brightness to {brightness}%")
            
        except Exception as e:
            print(f"❌ Error setting Raspberry Pi touchscreen brightness: {e}")
    
    def _set_dsi_brightness(self, brightness: int):
        """Set brightness for DSI display"""
        try:
            # Convert percentage to 0-255 range
            brightness_value = int((brightness / 100) * 255)
            
            with open("/sys/class/backlight/10-0045/brightness", "w") as f:
                f.write(str(brightness_value))
            
            print(f"✅ Set DSI display brightness to {brightness}%")
            
        except Exception as e:
            print(f"❌ Error setting DSI display brightness: {e}")
    
    def set_display_state(self, state: DisplayState):
        """
        Set the display state.
        
        Args:
            state: The display state to set
        """
        if self.current_state == state:
            return
        
        old_state = self.current_state
        self.current_state = state
        
        print(f"🖥️  Display state: {old_state.value} -> {state.value}")
        
        if state == DisplayState.ACTIVE:
            self._activate_display()
        elif state == DisplayState.DIMMED:
            self._dim_display()
        elif state == DisplayState.OFF:
            self._turn_off_display()
    
    def _activate_display(self):
        """Activate the display (full brightness and power on)"""
        print("🖥️  Activating display...")
        
        if self.test_mode:
            print("🧪 [TEST] Display activated (full brightness)")
            return
        
        try:
            # Set full brightness
            self.set_brightness(self.full_brightness)
            
            # Turn on display if it was off
            if self.display_type == "hdmi":
                self._turn_on_hdmi_display()
            elif self.display_type in ["rpi_touchscreen", "dsi"]:
                # These displays are typically always on when powered
                pass
            
            print("✅ Display activated")
            
        except Exception as e:
            print(f"❌ Error activating display: {e}")
    
    def _dim_display(self):
        """Dim the display"""
        print("🖥️  Dimming display...")
        
        if self.test_mode:
            print(f"🧪 [TEST] Display dimmed to {self.dim_brightness}%")
            return
        
        try:
            # Set dim brightness
            self.set_brightness(self.dim_brightness)
            print("✅ Display dimmed")
            
        except Exception as e:
            print(f"❌ Error dimming display: {e}")
    
    def _turn_off_display(self):
        """Turn off the display"""
        print("🖥️  Turning off display...")
        
        if self.test_mode:
            print("🧪 [TEST] Display turned off")
            return
        
        try:
            if self.display_type == "hdmi":
                self._turn_off_hdmi_display()
            elif self.display_type in ["rpi_touchscreen", "dsi"]:
                # Set brightness to 0 for these displays
                self.set_brightness(0)
            
            print("✅ Display turned off")
            
        except Exception as e:
            print(f"❌ Error turning off display: {e}")
    
    def _turn_on_hdmi_display(self):
        """Turn on HDMI display using tvservice"""
        try:
            subprocess.run(["tvservice", "-p"], check=True, timeout=10)
            print("✅ HDMI display turned on")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"❌ Error turning on HDMI display: {e}")
    
    def _turn_off_hdmi_display(self):
        """Turn off HDMI display using tvservice"""
        try:
            subprocess.run(["tvservice", "-o"], check=True, timeout=10)
            print("✅ HDMI display turned off")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"❌ Error turning off HDMI display: {e}")
    
    def get_current_state(self) -> DisplayState:
        """Get the current display state"""
        return self.current_state
    
    def get_current_brightness(self) -> int:
        """Get the current brightness level"""
        return self.current_brightness
    
    def is_active(self) -> bool:
        """Check if display is currently active"""
        return self.current_state == DisplayState.ACTIVE
    
    def is_dimmed(self) -> bool:
        """Check if display is currently dimmed"""
        return self.current_state == DisplayState.DIMMED
    
    def is_off(self) -> bool:
        """Check if display is currently off"""
        return self.current_state == DisplayState.OFF
    
    def cleanup(self):
        """Cleanup display controller"""
        try:
            # Restore full brightness on cleanup
            if not self.test_mode:
                self.set_brightness(self.full_brightness)
            print("✅ Display controller cleanup completed")
        except Exception as e:
            print(f"⚠️  Display controller cleanup failed: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()
