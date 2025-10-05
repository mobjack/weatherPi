#!/usr/bin/env python3
"""
Test script using text-based weather icons instead of emoji
"""

import os
import sys
import time
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QMainWindow
from PyQt5.QtCore import Qt


def test_text_weather_icon():
    """Test text-based weather icons"""
    print("🧪 Testing text-based weather icons...")

    try:
        app = QApplication(sys.argv)

        # Create a simple test window
        window = QMainWindow()
        window.setWindowTitle("Text Weather Icon Test")
        window.setGeometry(100, 100, 400, 300)

        central_widget = QWidget()
        window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Test text-based weather icons
        weather_icon = QLabel("CLOUD")
        weather_icon.setStyleSheet(
            "color: white; font-size: 32px; font-weight: bold; background-color: rgba(26, 26, 46, 0.2); border-radius: 10px; padding: 20px;")
        weather_icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(weather_icon)

        # Add some test buttons to change the icon
        test_icons = ['SUN', 'CLOUD', 'RAIN', 'SNOW', 'STORM']
        current_index = 1  # Start with CLOUD

        def change_icon():
            nonlocal current_index
            current_index = (current_index + 1) % len(test_icons)
            new_icon = test_icons[current_index]
            weather_icon.setText(new_icon)
            print(f"🔄 Changed weather icon to: {new_icon}")

        # Show the window
        window.show()

        print("✅ Test window created with text-based weather icon")
        print("Current icon: CLOUD")
        print("Icons will cycle through: SUN, CLOUD, RAIN, SNOW, STORM")

        # Cycle through icons every 3 seconds
        for i in range(10):  # 10 cycles
            time.sleep(3)
            change_icon()

        return True

    except Exception as e:
        print(f"❌ Error testing text weather icon: {e}")
        return False


if __name__ == "__main__":
    success = test_text_weather_icon()
    if success:
        print("✅ Text weather icon test completed!")
    else:
        print("❌ Text weather icon test failed!")
