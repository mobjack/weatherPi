#!/usr/bin/env python3
"""
Test script for motion detection functionality

This script demonstrates the motion detection and display control system
in test mode, allowing you to test the functionality without Raspberry Pi hardware.
"""

import sys
import time
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

# Add the bin directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bin'))

from motion_detection_service import MotionDetectionService, DisplayState as MotionDisplayState
from display_controller import DisplayController, DisplayState as ControllerDisplayState


class MotionTestWindow(QMainWindow):
    """Test window for motion detection functionality"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Motion Detection Test")
        self.setGeometry(100, 100, 600, 400)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Motion Detection Test")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Status display
        self.status_label = QLabel("Status: Initializing...")
        self.status_label.setFont(QFont("Arial", 12))
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Display state
        self.display_state_label = QLabel("Display State: Unknown")
        self.display_state_label.setFont(QFont("Arial", 12))
        self.display_state_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.display_state_label)
        
        # Brightness display
        self.brightness_label = QLabel("Brightness: Unknown")
        self.brightness_label.setFont(QFont("Arial", 12))
        self.brightness_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.brightness_label)
        
        # Test buttons
        self.trigger_motion_btn = QPushButton("Trigger Motion (Test)")
        self.trigger_motion_btn.clicked.connect(self.trigger_motion)
        layout.addWidget(self.trigger_motion_btn)
        
        self.manual_dim_btn = QPushButton("Manual Dim")
        self.manual_dim_btn.clicked.connect(self.manual_dim)
        layout.addWidget(self.manual_dim_btn)
        
        self.manual_off_btn = QPushButton("Manual Off")
        self.manual_off_btn.clicked.connect(self.manual_off)
        layout.addWidget(self.manual_off_btn)
        
        self.manual_active_btn = QPushButton("Manual Active")
        self.manual_active_btn.clicked.connect(self.manual_active)
        layout.addWidget(self.manual_active_btn)
        
        # Initialize services
        self.setup_services()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second
        
        self.update_display()
    
    def setup_services(self):
        """Setup motion detection and display control services"""
        try:
            # Initialize motion detection service in test mode
            self.motion_service = MotionDetectionService(
                motion_sensor_pin=18,
                display_timeout=10,  # Short timeout for testing
                display_dimming_timeout=5,  # Short dimming timeout for testing
                test_mode=True
            )
            
            # Set up callbacks
            self.motion_service.set_motion_detected_callback(self.on_motion_detected)
            self.motion_service.set_display_dim_callback(self.on_display_dim)
            self.motion_service.set_display_off_callback(self.on_display_off)
            self.motion_service.set_display_active_callback(self.on_display_active)
            
            # Initialize display controller in test mode
            self.display_controller = DisplayController(
                dim_brightness=30,
                full_brightness=100,
                test_mode=True
            )
            
            # Start the initial timer
            self.motion_service.start_display_timer()
            
            self.status_label.setText("Status: ✅ Services initialized successfully")
            
        except Exception as e:
            self.status_label.setText(f"Status: ❌ Error initializing services: {e}")
            print(f"Error initializing services: {e}")
    
    def on_motion_detected(self):
        """Callback for motion detection"""
        print("🔍 Motion detected!")
        self.status_label.setText("Status: 🔍 Motion detected - timer started")
    
    def on_display_dim(self):
        """Callback for display dimming"""
        print("🖥️  Display dimming")
        self.status_label.setText("Status: 🖥️  Display dimming")
    
    def on_display_off(self):
        """Callback for display off"""
        print("🖥️  Display off")
        self.status_label.setText("Status: 🖥️  Display off")
    
    def on_display_active(self):
        """Callback for display active"""
        print("🖥️  Display active")
        self.status_label.setText("Status: 🖥️  Display active")
    
    def trigger_motion(self):
        """Manually trigger motion detection"""
        if hasattr(self, 'motion_service'):
            self.motion_service.trigger_motion()
    
    def manual_dim(self):
        """Manually dim display"""
        if hasattr(self, 'display_controller'):
            self.display_controller.set_display_state(ControllerDisplayState.DIMMED)
    
    def manual_off(self):
        """Manually turn off display"""
        if hasattr(self, 'display_controller'):
            self.display_controller.set_display_state(ControllerDisplayState.OFF)
    
    def manual_active(self):
        """Manually activate display"""
        if hasattr(self, 'display_controller'):
            self.display_controller.set_display_state(ControllerDisplayState.ACTIVE)
    
    def update_display(self):
        """Update the display information"""
        if hasattr(self, 'motion_service'):
            motion_state = self.motion_service.get_current_state()
            self.display_state_label.setText(f"Motion State: {motion_state.value}")
        
        if hasattr(self, 'display_controller'):
            controller_state = self.display_controller.get_current_state()
            brightness = self.display_controller.get_current_brightness()
            self.brightness_label.setText(f"Display: {controller_state.value} (Brightness: {brightness}%)")
    
    def closeEvent(self, event):
        """Cleanup on close"""
        print("🔄 Closing test window - performing cleanup...")
        if hasattr(self, 'motion_service'):
            self.motion_service.cleanup()
        if hasattr(self, 'display_controller'):
            self.display_controller.cleanup()
        event.accept()


def main():
    """Main function"""
    print("🧪 Starting Motion Detection Test")
    print("=" * 50)
    print("This test demonstrates the motion detection system in test mode.")
    print("Features:")
    print("- Simulated motion detection every 30 seconds")
    print("- Display timeout: 10 seconds")
    print("- Display dimming timeout: 5 seconds")
    print("- Manual controls for testing")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    window = MotionTestWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
