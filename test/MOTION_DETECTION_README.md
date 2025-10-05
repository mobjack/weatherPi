# Motion Detection System for Weather Display

This document describes the motion detection and display timer system implemented for the Raspberry Pi weather display.

## Overview

The motion detection system automatically manages the display state based on motion sensor input:

1. **Motion Detected** → Display timer starts (60 seconds by default)
2. **Timer Expires** → Display dims (30% brightness)
3. **Dimming Timer Expires** → Display turns off completely
4. **Motion Detected Again** → Display turns back on at full brightness

## Hardware Requirements

### Raspberry Pi Setup
- Raspberry Pi (any model with GPIO)
- PIR (Passive Infrared) motion sensor
- Display (HDMI, DSI, or official Raspberry Pi touchscreen)

### Wiring
Connect the PIR sensor to GPIO pin 18 (configurable):
- VCC → 5V or 3.3V (check sensor specifications)
- GND → Ground
- OUT → GPIO 18 (BCM numbering)

## Configuration

Edit `conf/weather.conf` to configure the motion detection system:

```ini
# Motion Detection and Display Timer Configuration
# Motion sensor GPIO pin (BCM numbering)
MOTION_SENSOR_PIN=18

# Display timer settings (in seconds)
DISPLAY_TIMEOUT=60
DISPLAY_DIMMING_TIMEOUT=60

# Test mode for development without Raspberry Pi hardware
MOTION_TEST_MODE=false
```

### Configuration Options

- **MOTION_SENSOR_PIN**: GPIO pin number for the motion sensor (default: 18)
- **DISPLAY_TIMEOUT**: Time in seconds before display dims after motion stops (default: 60)
- **DISPLAY_DIMMING_TIMEOUT**: Time in seconds before display turns off after dimming (default: 60)
- **MOTION_TEST_MODE**: Set to `true` for development without hardware (default: false)

## Software Components

### 1. MotionDetectionService (`bin/motion_detection_service.py`)
- Handles GPIO-based motion detection
- Manages display timeout timers
- Provides callbacks for state changes
- Includes test mode for development

### 2. DisplayController (`bin/display_controller.py`)
- Controls display brightness and power states
- Supports multiple display types (HDMI, DSI, Raspberry Pi touchscreen)
- Handles display dimming and shutdown

### 3. WeatherApp Integration
- Motion detection is automatically integrated into the main weather app
- Services are initialized during app startup
- Proper cleanup on app shutdown

## Testing

### Test Mode
For development without Raspberry Pi hardware, enable test mode:

```ini
MOTION_TEST_MODE=true
```

In test mode:
- Motion is simulated every 30 seconds
- Display control is simulated (no actual hardware changes)
- All functionality can be tested on any computer

### Test Script
Run the test script to verify functionality:

```bash
python test_motion_detection.py
```

This opens a test window with:
- Real-time status display
- Manual motion trigger button
- Manual display state controls
- Live display state and brightness information

## Display Types Supported

### 1. Raspberry Pi Official Touchscreen
- Full brightness control via `/sys/class/backlight/rpi_backlight/`
- Automatic detection and setup

### 2. HDMI Display
- Power control via `tvservice` command
- Limited brightness control (depends on display)

### 3. DSI Display
- Brightness control via `/sys/class/backlight/10-0045/`
- Automatic detection

### 4. Unknown/Generic Display
- Graceful fallback with warnings
- Basic functionality may still work

## Usage

### Running the Weather App
The motion detection system is automatically enabled when running the weather app:

```bash
python weather_ui.py
```

### Manual Testing
You can manually trigger motion detection for testing:

```python
# In the weather app, you can call:
self.motion_service.trigger_motion()
```

## Troubleshooting

### Common Issues

1. **GPIO Permission Denied**
   ```bash
   sudo usermod -a -G gpio $USER
   # Then logout and login again
   ```

2. **RPi.GPIO Not Available**
   - Install: `pip install RPi.GPIO`
   - Or the system will automatically fall back to test mode

3. **Display Control Not Working**
   - Check display type detection in logs
   - Verify display permissions
   - Try different display types

4. **Motion Sensor Not Detecting**
   - Check wiring connections
   - Verify GPIO pin configuration
   - Test sensor with simple GPIO script

### Debug Mode
Enable verbose logging by checking the console output. The system provides detailed status messages for all operations.

## Dependencies

### Required Python Packages
- `RPi.GPIO` (for Raspberry Pi GPIO control)
- `PyQt5` (for the weather app UI)
- Standard library modules: `threading`, `time`, `subprocess`, `os`

### System Requirements
- Raspberry Pi OS (or compatible Linux distribution)
- `tvservice` command (for HDMI display control)
- Proper GPIO permissions

## Future Enhancements

Potential improvements for the motion detection system:

1. **Multiple Motion Sensors**: Support for multiple PIR sensors
2. **Light Sensor Integration**: Adjust brightness based on ambient light
3. **Scheduling**: Different timeouts for different times of day
4. **Remote Control**: Web interface for manual control
5. **Energy Monitoring**: Track power usage and savings
6. **Advanced Display Control**: Support for more display types and features

## Support

For issues or questions about the motion detection system:

1. Check the console output for error messages
2. Verify configuration settings
3. Test with the provided test script
4. Check hardware connections and permissions
