# Raspberry Pi Weather & Time Wallpaper Generator

This is a time and weather station for your Raspberry Pi. It displays the current time and weather conditions with beautiful, AI-generated wallpapers that change based on the time of day and weather.

---

## Features

- **Time × Weather combinations**: Loops through every entry in both JSON maps.
  - Time examples: `sunrise`, `morning`, `midday`, `afternoon`, `sunset`, `dusk`, `evening`, `night`
  - Weather examples: `CLEAR`, `PARTLY_CLOUDY`, `RAIN`, `SNOW`, `THUNDERSTORM`, etc.
- **Style packs**: Choose from multiple art directions (e.g., *minimal-gradient*, *flat-illustration*, *neon-glow*).
- **Prompt saving**: Each generated image has its prompt stored in `_prompts/` for audit/re-use.
- **Auto-resize/crop**: Images are automatically resized to match your configured window dimensions (default: 1000x600).
- **CLI options**: Control style, size, backoff timing, output directories, etc.

---

## Requirements

- Raspberry Pi OS (Bookworm/Bullseye) on a Pi 4 or Pi 5
- Python 3.11+ recommended 3.13
- OpenAI API key
- Dependencies: `openai`, `pillow`, `PyQt5`

---

## 🛠 Complete Raspberry Pi Setup Guide

### 1️⃣ System Preparation

Update your Raspberry Pi system and install basic dependencies:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git python3 python3-pip python3-venv
python3 --version
```

> ✅ Recommended: Python **3.13**

---

### 2️⃣ Clone and Setup Project

Navigate to your preferred project directory and clone the repository:

```bash
cd ~/repos  # or your preferred location
git clone mobjack/weatherPi
cd weatherPi
```

---

### 3️⃣ Create Virtual Environment

Create and activate a Python virtual environment:

```bash
cd <to path where clone was downloaded>
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel
```

Confirm it's active:

```bash
python -V
```

---

### 4️⃣ Install PyQt5

This project uses **PyQt5** for the on-screen user interface. Choose one of these options:

#### 🔵 Option A — Install PyQt5 via apt (Recommended)

This installs the prebuilt Qt and PyQt5 packages for Raspberry Pi OS:

```bash
sudo apt install -y python3-pyqt5 pyqt5-dev-tools qtbase5-dev qt5-qmake
```

If you want the apt-installed PyQt5 accessible inside your virtual environment, recreate it with system packages visible:

```bash
deactivate  # if your venv is active
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
```

Test that PyQt5 works:

```bash
python -c "from PyQt5 import QtCore; print(QtCore.QT_VERSION_STR)"
```

> This is the **fastest and most reliable** option on Raspberry Pi.

#### 🟢 Option B — Build PyQt5 from Source (pip only)

If you prefer PyQt5 isolated inside the virtual environment, you can build from source:

1. Install the Qt development headers and required libraries:

   ```bash
   sudo apt update
   sudo apt install -y build-essential python3-dev qtbase5-dev qtbase5-dev-tools qtchooser qt5-qmake libgl1-mesa-dev libxkbcommon-x11-0 libxcb-xinerama0
   ```

2. Activate your venv and install PyQt5:

   ```bash
   source .venv/bin/activate
   pip install --upgrade pip wheel sip
   pip install PyQt5>=5.15.11
   ```

3. Verify `qmake` exists if build errors occur:

   ```bash
   which qmake || echo "qmake missing"
   qmake -v
   ```

> ⚠️ Building may take several minutes. For Python 3.13, consider using Option A.

---

### 5️⃣ Install Project Dependencies

Install the remaining project dependencies:

If your project has a `requirements.txt` file:

```bash
pip install -r requirements.txt
```

Otherwise install manually:

```bash
pip install openai pillow
```

---

### 6️⃣ Configure Application Settings

Copy the example configuration file and update it with your settings:

```bash
cp conf/weather.conf.example conf/weather.conf
```

Edit `conf/weather.conf` and update these required settings:

**Required API Keys:**

- `OPENAI_API_KEY` - Your OpenAI API key for AI-generated wallpapers
- `OPENWEATHER_API_KEY` - Your OpenWeatherMap API key for weather data

**Location Settings:**

- `LOCATION_ZIP_CODE` - Your zip code for weather data
- `LOCATION_NAME` - Your city and state name

**Optional Settings (defaults work fine):**

- `USE_TEXT_ICONS` / `USE_IMAGE_ICONS` - Choose between text or image weather icons
- `TIME_UPDATE_INTERVAL` - How often time display updates (default: 1 minute)
- `WEATHER_UPDATE_INTERVAL` - How often weather data refreshes (default: 30 minutes)
- `WINDOW_WIDTH` / `WINDOW_HEIGHT` - Window dimensions in pixels (default: 1000x600)
- `MOTION_SENSOR_PIN` - GPIO pin for motion sensor (default: 18)
- `DISPLAY_TIMEOUT` - How long display stays on after motion (default: 60 seconds)
- `MOTION_TEST_MODE` - Set to `true` for testing without hardware

**Window Configuration:**

The application window size can be customized to match your display or preferences:

```ini
# Window Configuration
# Window dimensions (width x height)
WINDOW_WIDTH=1000
WINDOW_HEIGHT=600
```

Common display sizes:
- **Raspberry Pi 7" Touchscreen**: `WINDOW_WIDTH=800` `WINDOW_HEIGHT=480`
- **Standard Desktop**: `WINDOW_WIDTH=1000` `WINDOW_HEIGHT=600`
- **Wide Display**: `WINDOW_WIDTH=1200` `WINDOW_HEIGHT=800`
- **Full HD**: `WINDOW_WIDTH=1920` `WINDOW_HEIGHT=1080`

The wallpaper generator will automatically use these same dimensions to ensure perfect fit.

---

### 7️⃣ Test the Installation

Run your application to confirm everything works:

```bash
source .venv/bin/activate
python bin/weather_ui.py
```

You should see your PyQt5 interface display without errors.

---

## 🧠 Troubleshooting

| Problem | Fix |
|----------|-----|
| `qmake` not found | `sudo apt install -y qt5-qmake` |
| "xcb plugin" error | `sudo apt install -y libxcb-xinerama0` |
| No PyQt5 wheel for Python 3.13 | Use Option A (apt) or downgrade to Python 3.11 |
| GUI fails under Wayland | Install X11: `sudo apt install -y xserver-xorg` |
| Wrong Python version | `python3 -m venv --upgrade .venv && source .venv/bin/activate` |
| API key not found | Ensure `OPENAI_API_KEY` environment variable is set |

---

## 🚀 Running the Application

Once setup is complete, you can run the application:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the main weather application
python bin/weather_app.py

# Or run the wallpaper generator
python bin/generate_wallpapers.py
```

---

This setup ensures consistent behavior across macOS (development) and Raspberry Pi (deployment) environments using **PyQt5**.
