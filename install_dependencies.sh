#!/bin/bash
# WeatherPi Dependency Installation Script for Raspberry Pi
# Run this script on your Raspberry Pi to install all required dependencies

echo "🚀 Installing WeatherPi dependencies on Raspberry Pi..."
echo "=================================================="

# Update package lists
echo "📦 Updating package lists..."
sudo apt update

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-pyqt5 \
    python3-pyqt5.qtwidgets \
    python3-pyqt5.qtcore \
    python3-pyqt5.qtgui \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev

# Install Python packages
echo "🐍 Installing Python packages..."
pip3 install --user \
    requests>=2.28.0 \
    python-dotenv>=1.0.0 \
    openai>=1.0.0 \
    Pillow>=9.0.0 \
    typing-extensions>=4.0.0 \
    gpiozero \
    numpy

# Verify installation
echo "✅ Verifying installation..."
python3 -c "
import sys
try:
    import PyQt5
    print('✅ PyQt5: OK')
except ImportError:
    print('❌ PyQt5: FAILED')

try:
    import requests
    print('✅ requests: OK')
except ImportError:
    print('❌ requests: FAILED')

try:
    import openai
    print('✅ openai: OK')
except ImportError:
    print('❌ openai: FAILED')

try:
    import PIL
    print('✅ Pillow: OK')
except ImportError:
    print('❌ Pillow: FAILED')

try:
    import gpiozero
    print('✅ gpiozero: OK')
except ImportError:
    print('❌ gpiozero: FAILED')

try:
    import numpy
    print('✅ numpy: OK')
except ImportError:
    print('❌ numpy: FAILED')
"

echo ""
echo "🎉 Installation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Copy your weatherPi code to the Raspberry Pi"
echo "2. Run: python3 test_gpio_setup.py (to test motion sensor)"
echo "3. Run: python3 weather_ui.py (to start the app)"
echo ""
echo "⚠️  Note: Make sure your motion sensor is connected to GPIO pin 18"
