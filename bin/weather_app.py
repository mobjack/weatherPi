import os
import sys
import json
import time
import random
import datetime
import importlib.util

from typing import Dict, List, Optional
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QPixmap, QPalette, QBrush, QFont, QMouseEvent
from .temperature_graph import TemperatureGraph
from .weather_service_openweather import WeatherService
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QFrame, QPushButton)
from .motion_detection_service import MotionDetectionService, DisplayState as MotionDisplayState
from .display_controller import DisplayController, DisplayState as ControllerDisplayState

# Load configuration from weather.conf file


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

    # Get BASE_DIR from config
    config_path = None
    for path in possible_config_paths:
        if os.path.exists(path):
            config_path = path
            break

    if not config_path:
        print(f"⚠️  Warning: Could not find weather.conf in any of these locations:")
        for path in possible_config_paths:
            print(f"    - {path}")
        return default

    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith(f'{key}='):
                    value = line.split('=', 1)[1].strip()
                    # Handle BASE_DIR specially - resolve relative paths
                    if key == 'BASE_DIR' and value and not os.path.isabs(value):
                        # If BASE_DIR is relative, make it relative to the config file location
                        value = os.path.abspath(os.path.join(
                            os.path.dirname(config_path), value))
                    return value
    except Exception as e:
        print(f"⚠️  Warning: Error reading config file {config_path}: {e}")

    return default


def resolve_config_path(path, base_dir=None):
    """Resolve a path relative to the base directory or config file location"""
    if not path:
        return path

    # If it's already absolute, return as-is
    if os.path.isabs(path):
        return path

    # Get base directory
    if not base_dir:
        base_dir = load_config_value("BASE_DIR")

    # If no base_dir configured, try to find it from config file location
    if not base_dir:
        # Find the config file to determine base directory
        possible_config_paths = [
            "conf/weather.conf",
            os.path.join(os.path.dirname(__file__),
                         "..", "conf", "weather.conf"),
            os.path.join(os.getcwd(), "conf", "weather.conf"),
        ]

        for config_path in possible_config_paths:
            if os.path.exists(config_path):
                # Go up from conf/ to project root
                base_dir = os.path.dirname(os.path.dirname(config_path))
                break

    if base_dir:
        return os.path.join(base_dir, path)
    else:
        # Fallback to relative path
        return path


def load_sunrise_sunset_icon(icon_name, size):
    """Load sunrise or sunset icon from images/icons directory"""
    # Try multiple possible paths (check project directory first)
    possible_paths = [
        os.path.join("images", "icons", f"{icon_name}.png"),
        os.path.join(os.path.dirname(__file__), "..",
                     "images", "icons", f"{icon_name}.png"),
        os.path.join(os.path.expanduser("~"), "images",
                     "icons", f"{icon_name}.png"),
        os.path.join(os.getcwd(), "images", "icons", f"{icon_name}.png"),
    ]

    icon_path = None
    for path in possible_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            icon_path = abs_path
            print(f"✅ Found {icon_name} icon at: {icon_path}")
            break

    if icon_path:
        try:
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                return scaled_pixmap
        except Exception as e:
            print(f"⚠️  Failed to load {icon_name} icon: {e}")

    # Return None if icon couldn't be loaded
    print(f"⚠️  Could not find {icon_name} icon at any of the checked paths")
    return None


# Import the WallpaperGenerator class
spec = importlib.util.spec_from_file_location(
    "generate_wallpapers_v3", os.path.join(os.path.dirname(__file__), "generate_wallpapers.py"))
generate_wallpapers_v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_wallpapers_v3)
WallpaperGenerator = generate_wallpapers_v3.WallpaperGenerator

# Import the TemperatureGraph class


class WeatherApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Initialize the wallpaper generator
        try:
            # Use config-based paths instead of hardcoded ones
            day_night_json = resolve_config_path(
                load_config_value("DAY_NIGHT_JSON", "conf/day_night.json"))
            conditions_json = resolve_config_path(load_config_value(
                "CONDITIONS_JSON", "conf/gcp_conditions.json"))
            output_dir = resolve_config_path(load_config_value(
                "OUTPUT_DIR", "images/generated_wallpapers"))

            self.wallpaper_generator = WallpaperGenerator(
                day_night_json=day_night_json,
                conditions_json=conditions_json,
                output_dir=output_dir
            )
            print("✅ WallpaperGenerator initialized successfully")
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize WallpaperGenerator: {e}")
            self.wallpaper_generator = None

        # Initialize the weather service
        try:
            self.weather_service = WeatherService()
            print("✅ WeatherService initialized successfully")
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize WeatherService: {e}")
            self.weather_service = None

        # Load location from config file
        self.location = load_config_value('LOCATION_ZIP_CODE')
        if not self.location:
            print("❌ ERROR: LOCATION_ZIP_CODE not found in weather.conf")
            sys.exit(1)
        self.location_name = load_config_value(
            'LOCATION_NAME', 'Unknown Location')

        # Load icon preferences from config file
        self.use_text_icons = load_config_value(
            'USE_TEXT_ICONS', 'false').lower() == 'true'
        self.use_image_icons = load_config_value(
            'USE_IMAGE_ICONS', 'true').lower() == 'true'

        # Load timing configuration
        self.load_timing_config()

        # Load motion detection configuration
        self.load_motion_config()

        # Initialize motion detection and display control
        self.setup_motion_detection()
        self.setup_display_control()

        self.wallpaper_images = self.collect_wallpaper_images()
        self.setup_fonts()
        self.setup_window()
        self.create_widgets()
        self.setup_timers()
        self.set_random_background()

        # Load initial weather data immediately
        print("🌤️  Loading initial weather data...")
        self.load_weather_data()

        # Force a UI update after weather data is loaded
        if hasattr(self, 'weather_icon'):
            self.weather_icon.repaint()
            self.weather_icon.update()
            print(
                f"🔍 Initial weather icon after load: '{self.weather_icon.text()}'")

        # Start motion detection timer after everything is initialized
        if self.motion_service:
            print("🔍 Starting initial motion detection timer")
            self.motion_service.start_display_timer()

    def collect_wallpaper_images(self):
        """Collect all available wallpaper images from the generated_wallpapers folder"""
        wallpaper_images = []
        wallpaper_base_path = resolve_config_path(
            load_config_value("OUTPUT_DIR", "images/generated_wallpapers"))

        if os.path.exists(wallpaper_base_path):
            # Get all style folders (not just photoreal-soft)
            style_folders = [f for f in os.listdir(wallpaper_base_path)
                             if os.path.isdir(os.path.join(wallpaper_base_path, f)) and not f.startswith('_')]

            for style_folder in style_folders:
                style_path = os.path.join(wallpaper_base_path, style_folder)
                print(f"🔍 Scanning style folder: {style_folder}")

                # Get all time-of-day folders within each style
                time_folders = [f for f in os.listdir(style_path)
                                if os.path.isdir(os.path.join(style_path, f)) and not f.startswith('_')]

                for time_folder in time_folders:
                    time_path = os.path.join(style_path, time_folder)
                    # Get all PNG files in each time folder
                    png_files = [f for f in os.listdir(
                        time_path) if f.endswith('.png')]

                    for png_file in png_files:
                        full_path = os.path.join(time_path, png_file)
                        wallpaper_images.append(full_path)

        print(
            f"Found {len(wallpaper_images)} wallpaper images across all styles")
        return wallpaper_images

    def setup_fonts(self):
        """Setup Inter font for the application"""
        # Try to load Inter font, fallback to system default if not available
        try:
            # Try different possible Inter font names
            inter_font_names = [
                "Inter",
                "Inter-Regular",
                "Inter Regular",
                "Inter-Medium",
                "Inter Medium"
            ]

            self.inter_font = None
            for font_name in inter_font_names:
                font = QFont(font_name)
                if font.exactMatch():
                    self.inter_font = font
                    print(f"✅ Using Inter font: {font_name}")
                    break

            if not self.inter_font:
                # Fallback to system default
                self.inter_font = QFont()
                self.inter_font.setFamily("Arial")  # Fallback font
                print("⚠️  Inter font not found, using Arial as fallback")

        except Exception as e:
            print(f"⚠️  Error setting up fonts: {e}")
            self.inter_font = QFont()

    def load_timing_config(self):
        """Load timing configuration from weather.conf file"""
        try:
            # Default values (in milliseconds)
            default_config = {
                'TIME_UPDATE_INTERVAL': 60000,      # 1 minute
                'DATE_UPDATE_INTERVAL': 3600000,    # 1 hour
                'WEATHER_UPDATE_INTERVAL': 1800000,  # 30 minutes
                'BACKGROUND_UPDATE_INTERVAL': 1800000,  # 30 minutes
                'WINDOW_WIDTH': 1000,               # Window width
                'WINDOW_HEIGHT': 600                # Window height
            }

            # Load each config value using the robust config loader
            for key in default_config:
                value = load_config_value(key, str(default_config[key]))
                try:
                    self.__dict__[key.lower()] = int(value)
                    if key in ['WINDOW_WIDTH', 'WINDOW_HEIGHT']:
                        print(f"✅ Loaded {key}: {value}px")
                    else:
                        print(f"✅ Loaded {key}: {value}ms")
                except ValueError:
                    print(
                        f"⚠️  Invalid value for {key}: {value}, using default")
                    self.__dict__[key.lower()] = default_config[key]

        except Exception as e:
            print(f"⚠️  Error loading timing config: {e}, using defaults")
            # Set all defaults
            self.time_update_interval = 60000
            self.date_update_interval = 3600000
            self.weather_update_interval = 1800000
            self.background_update_interval = 1800000
            self.window_width = 1000
            self.window_height = 600

    def load_motion_config(self):
        """Load motion detection configuration from weather.conf file"""
        try:
            # Default values
            default_config = {
                'MOTION_SENSOR_PIN': 18,
                'DISPLAY_TIMEOUT': 60,
                'MOTION_TEST_MODE': False
            }

            # Load each config value using the robust config loader
            for key in default_config:
                value = load_config_value(key, str(default_config[key]))
                try:
                    if key == 'MOTION_TEST_MODE':
                        self.__dict__[key.lower()] = value.lower() == 'true'
                    else:
                        self.__dict__[key.lower()] = int(value)
                    print(f"✅ Loaded {key}: {value}")
                except ValueError:
                    print(
                        f"⚠️  Invalid value for {key}: {value}, using default")
                    self.__dict__[key.lower()] = default_config[key]

        except Exception as e:
            print(f"⚠️  Error loading motion config: {e}, using defaults")
            # Set all defaults
            self.motion_sensor_pin = 18
            self.display_timeout = 60
            self.motion_test_mode = False

    def setup_motion_detection(self):
        """Setup motion detection service"""
        try:
            self.motion_service = MotionDetectionService(
                motion_sensor_pin=self.motion_sensor_pin,
                display_timeout=self.display_timeout,
                test_mode=self.motion_test_mode
            )

            # Set up callbacks
            self.motion_service.set_motion_detected_callback(
                self.on_motion_detected)
            self.motion_service.set_display_off_callback(self.on_display_off)
            self.motion_service.set_display_active_callback(
                self.on_display_active)

            print("✅ Motion detection service initialized")

        except Exception as e:
            print(f"❌ Error initializing motion detection service: {e}")
            self.motion_service = None

    def setup_display_control(self):
        """Setup display controller"""
        try:
            from bin.display_controller import DisplayController

            self.display_controller = DisplayController(
                dim_brightness=30,
                full_brightness=100,
                test_mode=self.motion_test_mode
            )
            print("✅ Display controller initialized")
        except Exception as e:
            print(f"❌ Error initializing display controller: {e}")
            self.display_controller = None

    def on_motion_detected(self):
        """Callback for when motion is detected"""
        print("🔍 Motion detected - resetting display timer")
        if self.motion_service:
            self.motion_service.reset_dimming_timer()

    def on_display_off(self):
        """Callback for when display should turn off"""
        print("🖥️  Turning off display")
        if self.display_controller:
            from bin.display_controller import DisplayState
            self.display_controller.set_display_state(DisplayState.OFF)

    def on_display_active(self):
        """Callback for when display should become active"""
        print("🖥️  Activating display")
        if self.display_controller:
            from bin.display_controller import DisplayState
            self.display_controller.set_display_state(DisplayState.ACTIVE)

    def generate_current_weather_wallpaper(self):
        """Generate a wallpaper based on current real weather conditions"""
        if not self.wallpaper_generator:
            print("⚠️  WallpaperGenerator not available, skipping generation")
            return None

        try:
            print("🎨 Generating current weather wallpaper...")
            result = self.wallpaper_generator.generate_current_weather_wallpaper(
                style="random",  # Randomly select from available styles
                location=self.location,  # Use zip code from config
                # Use configurable window size
                target_size=(self.window_width, self.window_height),
                try_resize=True,
                save_prompt=False
            )

            print(
                f"✅ Generated current weather wallpaper: {result['filename']}")
            print(f"   Path: {result['path']}")
            return result['path']

        except Exception as e:
            print(f"❌ Error in weather_app generating weather wallpaper: {e}")
            return None

    def set_random_background(self):
        """Set a random background image from the collected wallpapers or generate a new one"""
        # First try to generate a current weather wallpaper
        generated_wallpaper = self.generate_current_weather_wallpaper()

        if generated_wallpaper and os.path.exists(generated_wallpaper):
            print(
                f"Using generated current weather wallpaper: {os.path.basename(generated_wallpaper)}")
            self.set_background_image(generated_wallpaper)
        elif self.wallpaper_images:
            # Fallback to existing wallpapers
            random_wallpaper = random.choice(self.wallpaper_images)
            print(
                f"Using existing wallpaper: {os.path.basename(random_wallpaper)}")
            self.set_background_image(random_wallpaper)
        else:
            print("No wallpaper images found, using default background")

    def set_background_image(self, image_path):
        """Set the background image for the main window"""
        if os.path.exists(image_path):
            # Create a pixmap from the image
            pixmap = QPixmap(image_path)

            # Scale the image to fill the entire window
            scaled_pixmap = pixmap.scaled(
                self.size(),
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )

            # Set the background using a palette
            palette = QPalette()
            palette.setBrush(QPalette.Window, QBrush(scaled_pixmap))
            self.setPalette(palette)

            # Track the current background path
            self.current_background_path = image_path

    def setup_window(self):
        """Configure the main window"""
        self.setWindowTitle("Weather App")
        # Use configurable window dimensions
        self.setGeometry(100, 100, self.window_width, self.window_height)
        # Force the window to stay at the configured size
        self.setFixedSize(self.window_width, self.window_height)
        # Enable mouse tracking for motion detection
        self.setMouseTracking(True)
        # Background will be set by set_random_background()

    def create_widgets(self):
        """Create all UI widgets for portrait layout with single background container"""
        # Create the main container directly as central widget
        main_container = QFrame()
        main_container.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.2); border-radius: 15px;")
        self.setCentralWidget(main_container)

        # Create layout directly on the main container
        main_layout = QVBoxLayout(main_container)
        # Adjust spacing and margins for portrait layout
        spacing = max(8, self.window_height // 60)  # Reduced spacing
        margin = max(15, self.window_width // 25)
        main_layout.setSpacing(spacing)
        main_layout.setContentsMargins(margin, margin, margin, margin)

        # Create all content within the single container
        self.create_portrait_content(main_layout)

    def create_portrait_content(self, parent_layout):
        """Create all portrait content within a single background container - matching original design"""

        # 1. Top row: Time (left) and Current Temperature with icon (right)
        top_row = QHBoxLayout()
        top_row.setSpacing(20)

        # Time (left side)
        self.time_label = QLabel("10:56")
        time_font_size = max(48, self.window_width // 6)
        self.time_label.setStyleSheet(
            f"color: white; font-size: {time_font_size}px; font-weight: bold;")
        if hasattr(self, 'inter_font'):
            time_font = QFont(self.inter_font)
            time_font.setPointSize(time_font_size)
            time_font.setBold(True)
            self.time_label.setFont(time_font)
        self.time_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        top_row.addWidget(self.time_label)

        # Add stretch to push temperature to the right
        top_row.addStretch()

        # Current Temperature with weather icon (right side)
        temp_container = QHBoxLayout()
        temp_container.setSpacing(8)

        # Weather icon
        self.weather_icon = QLabel("☀️")
        icon_font_size = max(32, self.window_width // 10)
        self.weather_icon.setStyleSheet(
            f"color: yellow; font-size: {icon_font_size}px;")
        self.weather_icon.setAlignment(Qt.AlignCenter)
        temp_container.addWidget(self.weather_icon)

        # Current Temperature
        self.temp_label = QLabel("58°")
        temp_font_size = max(36, self.window_width // 8)
        self.temp_label.setStyleSheet(
            f"color: white; font-size: {temp_font_size}px; font-weight: bold;")
        if hasattr(self, 'inter_font'):
            temp_font = QFont(self.inter_font)
            temp_font.setPointSize(temp_font_size)
            temp_font.setBold(True)
            self.temp_label.setFont(temp_font)
        self.temp_label.setAlignment(Qt.AlignCenter)
        temp_container.addWidget(self.temp_label)

        # Add temp container to top row
        temp_widget = QWidget()
        temp_widget.setLayout(temp_container)
        top_row.addWidget(temp_widget)

        parent_layout.addLayout(top_row)

        # 2. Date and Day of Week (combined with comma)
        self.day_date_label = QLabel("Wednesday, October 15")
        day_date_font_size = max(22, self.window_width // 14)
        self.day_date_label.setStyleSheet(
            f"color: white; font-size: {day_date_font_size}px; font-weight: bold; background: transparent;")
        if hasattr(self, 'inter_font'):
            day_date_font = QFont(self.inter_font)
            day_date_font.setPointSize(day_date_font_size)
            day_date_font.setBold(True)
            self.day_date_label.setFont(day_date_font)
        self.day_date_label.setAlignment(Qt.AlignCenter)
        parent_layout.addWidget(self.day_date_label)

        # 3. Sunrise/Sunset row
        sun_row = QHBoxLayout()
        sun_row.setSpacing(20)

        # Sunrise (left side) - no container widget
        sunrise_container = QVBoxLayout()
        sunrise_container.setSpacing(5)
        sunrise_container.setAlignment(Qt.AlignCenter)

        # Sunrise title
        sunrise_title = QLabel("Sunrise")
        sunrise_title_font_size = max(14, self.window_width // 25)
        sunrise_title.setStyleSheet(
            f"color: white; font-size: {sunrise_title_font_size}px; font-weight: bold; background: transparent;")
        if hasattr(self, 'inter_font'):
            sunrise_title_font = QFont(self.inter_font)
            sunrise_title_font.setPointSize(sunrise_title_font_size)
            sunrise_title_font.setBold(True)
            sunrise_title.setFont(sunrise_title_font)
        sunrise_title.setAlignment(Qt.AlignCenter)
        sunrise_container.addWidget(sunrise_title)

        sunrise_icon = QLabel()
        sunrise_icon_size = max(40, self.window_width //
                                8)  # Much larger icons
        sunrise_pixmap = load_sunrise_sunset_icon("sunrise", sunrise_icon_size)
        if sunrise_pixmap:
            sunrise_icon.setPixmap(sunrise_pixmap)
            sunrise_icon.setStyleSheet("background: transparent;")
        else:
            sunrise_icon.setText("🌅")
            sunrise_icon.setStyleSheet(
                f"color: orange; font-size: {sunrise_icon_size}px; background: transparent;")
        sunrise_icon.setAlignment(Qt.AlignCenter)
        sunrise_container.addWidget(sunrise_icon)

        self.sunrise_label = QLabel("6:48am")
        sunrise_font_size = max(16, self.window_width // 20)
        self.sunrise_label.setStyleSheet(
            f"color: white; font-size: {sunrise_font_size}px; background: transparent;")
        if hasattr(self, 'inter_font'):
            sunrise_font = QFont(self.inter_font)
            sunrise_font.setPointSize(sunrise_font_size)
            self.sunrise_label.setFont(sunrise_font)
        self.sunrise_label.setAlignment(Qt.AlignCenter)
        sunrise_container.addWidget(self.sunrise_label)

        # Add sunrise layout directly (no widget container)
        sun_row.addWidget(QWidget())  # Left spacer - minimal
        sun_row.addLayout(sunrise_container)

        # Minimal stretch to bring icons closer to center
        sun_row.addStretch()

        # Sunset (right side) - no container widget
        sunset_container = QVBoxLayout()
        sunset_container.setSpacing(5)
        sunset_container.setAlignment(Qt.AlignCenter)

        # Sunset title
        sunset_title = QLabel("Sunset")
        sunset_title_font_size = max(14, self.window_width // 25)
        sunset_title.setStyleSheet(
            f"color: white; font-size: {sunset_title_font_size}px; font-weight: bold; background: transparent;")
        if hasattr(self, 'inter_font'):
            sunset_title_font = QFont(self.inter_font)
            sunset_title_font.setPointSize(sunset_title_font_size)
            sunset_title_font.setBold(True)
            sunset_title.setFont(sunset_title_font)
        sunset_title.setAlignment(Qt.AlignCenter)
        sunset_container.addWidget(sunset_title)

        sunset_icon = QLabel()
        sunset_icon_size = max(40, self.window_width // 8)  # Much larger icons
        sunset_pixmap = load_sunrise_sunset_icon("sunset", sunset_icon_size)
        if sunset_pixmap:
            sunset_icon.setPixmap(sunset_pixmap)
            sunset_icon.setStyleSheet("background: transparent;")
        else:
            sunset_icon.setText("🌇")
            sunset_icon.setStyleSheet(
                f"color: orange; font-size: {sunset_icon_size}px; background: transparent;")
        sunset_icon.setAlignment(Qt.AlignCenter)
        sunset_container.addWidget(sunset_icon)

        self.sunset_label = QLabel("7:13pm")
        sunset_font_size = max(16, self.window_width // 20)
        self.sunset_label.setStyleSheet(
            f"color: white; font-size: {sunset_font_size}px; background: transparent;")
        if hasattr(self, 'inter_font'):
            sunset_font = QFont(self.inter_font)
            sunset_font.setPointSize(sunset_font_size)
            self.sunset_label.setFont(sunset_font)
        self.sunset_label.setAlignment(Qt.AlignCenter)
        sunset_container.addWidget(self.sunset_label)

        # Add sunset layout directly (no widget container)
        sun_row.addLayout(sunset_container)
        sun_row.addWidget(QWidget())  # Right spacer - minimal

        parent_layout.addLayout(sun_row)

        # 4. 3-day forecast section - integrated title and forecast in one container
        forecast_container = QVBoxLayout()
        forecast_container.setSpacing(8)
        forecast_container.setAlignment(Qt.AlignCenter)

        # Forecast title (smaller H3 size)
        forecast_title = QLabel("3 Day Forecast")
        forecast_title_font_size = max(
            14, self.window_width // 25)  # Smaller H3 size
        forecast_title.setStyleSheet(
            f"color: white; font-size: {forecast_title_font_size}px; font-weight: bold;")
        if hasattr(self, 'inter_font'):
            title_font = QFont(self.inter_font)
            title_font.setPointSize(forecast_title_font_size)
            title_font.setBold(True)
            forecast_title.setFont(title_font)
        forecast_title.setAlignment(Qt.AlignCenter)
        forecast_container.addWidget(forecast_title)

        # Forecast days - horizontal layout
        forecast_row = QHBoxLayout()
        forecast_row.setSpacing(20)

        self.forecast_days = []
        day_data = [
            ("THU", "☀️"),
            ("FRI", "☀️"),
            ("SAT", "☀️")
        ]

        for day_name, icon in day_data:
            # Create vertical layout for each forecast item (no container widget)
            forecast_item = QVBoxLayout()
            forecast_item.setSpacing(5)
            forecast_item.setAlignment(Qt.AlignCenter)

            # Weather icon (top)
            weather_icon = QLabel(icon)
            forecast_icon_font_size = max(28, self.window_width // 12)
            weather_icon.setStyleSheet(
                f"color: yellow; font-size: {forecast_icon_font_size}px; background: transparent;")
            weather_icon.setAlignment(Qt.AlignCenter)
            forecast_item.addWidget(weather_icon)

            # Day name (bottom)
            day_label = QLabel(day_name)
            day_name_font_size = max(16, self.window_width // 20)
            day_label.setStyleSheet(
                f"color: white; font-size: {day_name_font_size}px; font-weight: bold; background: transparent;")
            if hasattr(self, 'inter_font'):
                day_name_font = QFont(self.inter_font)
                day_name_font.setPointSize(day_name_font_size)
                day_name_font.setBold(True)
                day_label.setFont(day_name_font)
            day_label.setAlignment(Qt.AlignCenter)
            forecast_item.addWidget(day_label)

            # Add forecast item layout directly to horizontal row (no widget container)
            forecast_row.addLayout(forecast_item)

            self.forecast_days.append({
                'day': day_label,
                'icon': weather_icon
            })

        # Add forecast row directly to container (no widget wrapper)
        forecast_container.addLayout(forecast_row)

        # Add the entire forecast container to parent layout
        forecast_widget = QWidget()
        forecast_widget.setLayout(forecast_container)
        parent_layout.addWidget(forecast_widget)

        # 5. High/Low temperature row (moved to bottom left) - vertical stack
        high_low_row = QHBoxLayout()
        high_low_row.setSpacing(15)

        # Thermometer icon with high/low temperatures stacked vertically
        temp_container = QHBoxLayout()
        temp_container.setSpacing(10)

        # Thermometer icon
        thermometer_icon = QLabel("🌡️")
        thermometer_icon.setStyleSheet(
            f"color: orange; font-size: {max(28, self.window_width // 12)}px; background: transparent;")
        thermometer_icon.setAlignment(Qt.AlignCenter)
        temp_container.addWidget(thermometer_icon)

        # High/Low temperatures stacked vertically
        temps_vertical = QVBoxLayout()
        temps_vertical.setSpacing(5)

        # High temperature (top)
        self.high_temp_label = QLabel("H: 92")
        high_font_size = max(20, self.window_width // 15)
        self.high_temp_label.setStyleSheet(
            f"color: white; font-size: {high_font_size}px; font-weight: bold; background: transparent;")
        if hasattr(self, 'inter_font'):
            high_font = QFont(self.inter_font)
            high_font.setPointSize(high_font_size)
            high_font.setBold(True)
            self.high_temp_label.setFont(high_font)
        self.high_temp_label.setAlignment(Qt.AlignCenter)
        temps_vertical.addWidget(self.high_temp_label)

        # Low temperature (bottom)
        self.low_temp_label = QLabel("L: 55")
        low_font_size = max(20, self.window_width // 15)
        self.low_temp_label.setStyleSheet(
            f"color: white; font-size: {low_font_size}px; font-weight: bold; background: transparent;")
        if hasattr(self, 'inter_font'):
            low_font = QFont(self.inter_font)
            low_font.setPointSize(low_font_size)
            low_font.setBold(True)
            self.low_temp_label.setFont(low_font)
        self.low_temp_label.setAlignment(Qt.AlignCenter)
        temps_vertical.addWidget(self.low_temp_label)

        temps_widget = QWidget()
        temps_widget.setLayout(temps_vertical)
        temp_container.addWidget(temps_widget)

        # Add the combined container to the row
        combined_widget = QWidget()
        combined_widget.setLayout(temp_container)
        high_low_row.addWidget(combined_widget)

        # Add stretch to push high/low to the left
        high_low_row.addStretch()

        parent_layout.addLayout(high_low_row)

        # 6. Location and controls row
        location_row = QHBoxLayout()

        # Location
        self.location_label = QLabel(self.location_name)
        location_font_size = max(14, self.window_width // 25)
        self.location_label.setStyleSheet(
            f"color: white; font-size: {location_font_size}px;")
        if hasattr(self, 'inter_font'):
            location_font = QFont(self.inter_font)
            location_font.setPointSize(location_font_size)
            self.location_label.setFont(location_font)
        self.location_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        location_row.addWidget(self.location_label)

        # Add stretch to push controls to the right
        location_row.addStretch()

        # Countdown display
        self.countdown_label = QLabel("Dim: 49s")
        countdown_font_size = max(12, self.window_width // 30)
        self.countdown_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.8);
                font-size: {countdown_font_size}px;
                font-weight: 600;
                padding: 4px 8px;
                background-color: rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                min-width: 40px;
            }}
        """)
        if hasattr(self, 'inter_font'):
            countdown_font = QFont(self.inter_font)
            countdown_font.setPointSize(countdown_font_size)
            countdown_font.setBold(True)
            self.countdown_label.setFont(countdown_font)
        self.countdown_label.setAlignment(Qt.AlignCenter)
        location_row.addWidget(self.countdown_label)

        # BG Scrap button
        self.bg_scrap_button = QPushButton("BG Scrap")
        button_font_size = max(12, self.window_width // 30)
        self.bg_scrap_button.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 100, 100, 0.85);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 6px 12px;
                font-size: {button_font_size}px;
                font-weight: 600;
                min-width: 60px;
                min-height: 24px;
                max-height: 28px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 120, 120, 0.95);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 80, 80, 1.0);
            }}
        """)
        if hasattr(self, 'inter_font'):
            button_font = QFont(self.inter_font)
            button_font.setPointSize(button_font_size)
            button_font.setBold(True)
            self.bg_scrap_button.setFont(button_font)
        self.bg_scrap_button.clicked.connect(self.on_bg_scrap_clicked)
        location_row.addWidget(self.bg_scrap_button)

        parent_layout.addLayout(location_row)

    def create_top_row(self, parent_layout):
        """Create the top row with 5 columns: time, sunrise/sunset, current weather, high/low, date"""
        top_frame = QFrame()
        top_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.2); border-radius: 10px;")
        top_layout = QHBoxLayout(top_frame)
        # Adjust spacing based on window width - much smaller for compact displays
        top_spacing = max(2, self.window_width // 200)
        top_layout.setSpacing(top_spacing)

        # Column 1: Current Time
        time_frame = QFrame()
        # Adjust padding based on window size - much smaller for compact displays
        padding = max(4, self.window_width // 120)
        time_frame.setStyleSheet(
            f"background-color: rgba(26, 26, 46, 0.2); border-radius: 10px; padding: {padding}px;")
        time_layout = QVBoxLayout(time_frame)
        time_layout.setAlignment(Qt.AlignCenter)

        self.time_label = QLabel("10:23")
        # Increase font size to better fill the available space
        time_font_size = max(24, self.window_width // 25)
        self.time_label.setStyleSheet(
            f"color: white; font-size: {time_font_size}px; font-weight: bold;")
        # Apply Inter font to time label
        if hasattr(self, 'inter_font'):
            time_font = QFont(self.inter_font)
            time_font.setPointSize(time_font_size)
            time_font.setBold(True)
            self.time_label.setFont(time_font)
        self.time_label.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(self.time_label)
        top_layout.addWidget(time_frame)

        # Column 2: Sunrise/Sunset Times
        sun_frame = QFrame()
        sun_frame.setStyleSheet(
            f"background-color: rgba(26, 26, 46, 0.2); border-radius: 10px; padding: {padding}px;")
        sun_layout = QVBoxLayout(sun_frame)
        sun_layout.setAlignment(Qt.AlignCenter)
        sun_layout.setSpacing(5)

        # Sunrise
        self.sunrise_label = QLabel("↑06:30")
        # Adjust font size based on window size - much smaller for compact displays
        small_font_size = max(10, self.window_width // 80)
        self.sunrise_label.setStyleSheet(
            f"color: white; font-size: {small_font_size}px;")
        # Apply Inter font to sunrise label
        if hasattr(self, 'inter_font'):
            sunrise_font = QFont(self.inter_font)
            sunrise_font.setPointSize(small_font_size)
            self.sunrise_label.setFont(sunrise_font)
        self.sunrise_label.setAlignment(Qt.AlignCenter)
        sun_layout.addWidget(self.sunrise_label)

        # Sunset
        self.sunset_label = QLabel("↓18:30")
        self.sunset_label.setStyleSheet(
            f"color: white; font-size: {small_font_size}px;")
        # Apply Inter font to sunset label
        if hasattr(self, 'inter_font'):
            sunset_font = QFont(self.inter_font)
            sunset_font.setPointSize(small_font_size)
            self.sunset_label.setFont(sunset_font)
        self.sunset_label.setAlignment(Qt.AlignCenter)
        sun_layout.addWidget(self.sunset_label)
        top_layout.addWidget(sun_frame)

        # Column 3: Current Weather (Icon + Temperature)
        weather_frame = QFrame()
        weather_frame.setStyleSheet(
            f"background-color: rgba(26, 26, 46, 0.2); border-radius: 10px; padding: {padding}px;")
        weather_layout = QVBoxLayout(weather_frame)
        weather_layout.setAlignment(Qt.AlignCenter)
        weather_layout.setSpacing(8)

        # Weather icon
        self.weather_icon = QLabel("☀️")
        # Adjust icon size based on window size - much smaller for compact displays
        icon_font_size = max(16, self.window_width // 50)
        self.weather_icon.setStyleSheet(
            f"color: yellow; font-size: {icon_font_size}px;")
        self.weather_icon.setAlignment(Qt.AlignCenter)
        weather_layout.addWidget(self.weather_icon)

        # Current Temperature
        self.temp_label = QLabel("55°")
        # Adjust font size based on window size - much smaller for compact displays
        temp_font_size = max(12, self.window_width // 60)
        self.temp_label.setStyleSheet(
            f"color: white; font-size: {temp_font_size}px; font-weight: bold;")
        # Apply Inter font to temperature label
        if hasattr(self, 'inter_font'):
            temp_font = QFont(self.inter_font)
            temp_font.setPointSize(temp_font_size)
            temp_font.setBold(True)
            self.temp_label.setFont(temp_font)
        self.temp_label.setAlignment(Qt.AlignCenter)
        weather_layout.addWidget(self.temp_label)
        top_layout.addWidget(weather_frame)

        # Column 4: High/Low Temperatures
        high_low_frame = QFrame()
        high_low_frame.setStyleSheet(
            f"background-color: rgba(26, 26, 46, 0.2); border-radius: 10px; padding: {padding}px;")
        high_low_layout = QVBoxLayout(high_low_frame)
        high_low_layout.setAlignment(Qt.AlignCenter)
        high_low_layout.setSpacing(5)

        # High temperature
        self.high_temp_label = QLabel("H:78")
        # Adjust font size based on window size - much smaller for compact displays
        medium_font_size = max(10, self.window_width // 70)
        self.high_temp_label.setStyleSheet(
            f"color: white; font-size: {medium_font_size}px; font-weight: bold;")
        # Apply Inter font to high temp label
        if hasattr(self, 'inter_font'):
            high_font = QFont(self.inter_font)
            high_font.setPointSize(medium_font_size)
            high_font.setBold(True)
            self.high_temp_label.setFont(high_font)
        self.high_temp_label.setAlignment(Qt.AlignCenter)
        high_low_layout.addWidget(self.high_temp_label)

        # Low temperature
        self.low_temp_label = QLabel("L:65")
        self.low_temp_label.setStyleSheet(
            f"color: white; font-size: {medium_font_size}px; font-weight: bold;")
        # Apply Inter font to low temp label
        if hasattr(self, 'inter_font'):
            low_font = QFont(self.inter_font)
            low_font.setPointSize(medium_font_size)
            low_font.setBold(True)
            self.low_temp_label.setFont(low_font)
        self.low_temp_label.setAlignment(Qt.AlignCenter)
        high_low_layout.addWidget(self.low_temp_label)
        top_layout.addWidget(high_low_frame)

        # Column 5: Date and Day
        date_frame = QFrame()
        date_frame.setStyleSheet(
            f"background-color: rgba(26, 26, 46, 0.2); border-radius: 10px; padding: {padding}px;")
        date_layout = QVBoxLayout(date_frame)
        date_layout.setAlignment(Qt.AlignCenter)
        date_layout.setSpacing(8)

        self.day_label = QLabel("Tuesday")
        # Increase font size for day of week to better fill available space
        day_font_size = max(14, self.window_width // 50)
        self.day_label.setStyleSheet(
            f"color: white; font-size: {day_font_size}px; font-weight: bold;")
        self.day_label.setAlignment(Qt.AlignCenter)
        # Apply Inter font to day label
        if hasattr(self, 'inter_font'):
            day_font = QFont(self.inter_font)
            day_font.setPointSize(day_font_size)
            day_font.setBold(True)
            self.day_label.setFont(day_font)
        date_layout.addWidget(self.day_label)

        self.date_label = QLabel("April 23")
        # Increase font size for date to better fill available space
        date_font_size = max(14, self.window_width // 50)
        self.date_label.setStyleSheet(
            f"color: white; font-size: {date_font_size}px; font-weight: bold;")
        self.date_label.setAlignment(Qt.AlignCenter)
        # Apply Inter font to date label
        if hasattr(self, 'inter_font'):
            date_font = QFont(self.inter_font)
            date_font.setPointSize(date_font_size)
            date_font.setBold(True)
            self.date_label.setFont(date_font)
        date_layout.addWidget(self.date_label)
        top_layout.addWidget(date_frame)

        parent_layout.addWidget(top_frame)

    def create_top_row_portrait(self, parent_layout):
        """Create the top row for portrait layout: Time (left) and Current Temperature (right)"""
        top_frame = QFrame()
        top_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.2); border-radius: 10px;")
        top_layout = QHBoxLayout(top_frame)
        top_layout.setSpacing(10)

        # Left side: Current Time (bigger in portrait)
        time_frame = QFrame()
        padding = max(8, self.window_width // 30)
        time_frame.setStyleSheet(
            f"background-color: rgba(26, 26, 46, 0.2); border-radius: 10px; padding: {padding}px;")
        time_layout = QVBoxLayout(time_frame)
        time_layout.setAlignment(Qt.AlignCenter)

        self.time_label = QLabel("10:56")
        # Much bigger font for portrait mode
        time_font_size = max(36, self.window_width // 8)
        self.time_label.setStyleSheet(
            f"color: white; font-size: {time_font_size}px; font-weight: bold;")
        if hasattr(self, 'inter_font'):
            time_font = QFont(self.inter_font)
            time_font.setPointSize(time_font_size)
            time_font.setBold(True)
            self.time_label.setFont(time_font)
        self.time_label.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(self.time_label)
        top_layout.addWidget(time_frame)

        # Add stretch to push temperature to the right
        top_layout.addStretch()

        # Right side: Current Temperature with weather icon (horizontal layout)
        temp_frame = QFrame()
        temp_frame.setStyleSheet(
            f"background-color: rgba(26, 26, 46, 0.2); border-radius: 10px; padding: {padding}px;")
        temp_layout = QHBoxLayout(temp_frame)
        temp_layout.setAlignment(Qt.AlignCenter)
        temp_layout.setSpacing(8)

        # Weather icon
        self.weather_icon = QLabel("☀️")
        icon_font_size = max(24, self.window_width // 12)
        self.weather_icon.setStyleSheet(
            f"color: yellow; font-size: {icon_font_size}px;")
        self.weather_icon.setAlignment(Qt.AlignCenter)
        temp_layout.addWidget(self.weather_icon)

        # Current Temperature
        self.temp_label = QLabel("58°")
        temp_font_size = max(20, self.window_width // 15)
        self.temp_label.setStyleSheet(
            f"color: white; font-size: {temp_font_size}px; font-weight: bold;")
        if hasattr(self, 'inter_font'):
            temp_font = QFont(self.inter_font)
            temp_font.setPointSize(temp_font_size)
            temp_font.setBold(True)
            self.temp_label.setFont(temp_font)
        self.temp_label.setAlignment(Qt.AlignCenter)
        temp_layout.addWidget(self.temp_label)
        top_layout.addWidget(temp_frame)

        parent_layout.addWidget(top_frame)

    def create_date_section_portrait(self, parent_layout):
        """Create the date and day of week section for portrait layout"""
        date_frame = QFrame()
        date_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.2); border-radius: 10px;")
        date_layout = QVBoxLayout(date_frame)
        date_layout.setAlignment(Qt.AlignCenter)
        date_layout.setSpacing(8)

        # Day of week
        self.day_label = QLabel("Wednesday")
        day_font_size = max(18, self.window_width // 15)
        self.day_label.setStyleSheet(
            f"color: white; font-size: {day_font_size}px; font-weight: bold;")
        if hasattr(self, 'inter_font'):
            day_font = QFont(self.inter_font)
            day_font.setPointSize(day_font_size)
            day_font.setBold(True)
            self.day_label.setFont(day_font)
        self.day_label.setAlignment(Qt.AlignCenter)
        date_layout.addWidget(self.day_label)

        # Date
        self.date_label = QLabel("Oct 12")
        date_font_size = max(16, self.window_width // 18)
        self.date_label.setStyleSheet(
            f"color: white; font-size: {date_font_size}px; font-weight: bold;")
        if hasattr(self, 'inter_font'):
            date_font = QFont(self.inter_font)
            date_font.setPointSize(date_font_size)
            date_font.setBold(True)
            self.date_label.setFont(date_font)
        self.date_label.setAlignment(Qt.AlignCenter)
        date_layout.addWidget(self.date_label)

        parent_layout.addWidget(date_frame)

    def create_date_sunrise_sunset_section_portrait(self, parent_layout):
        """Create the combined date and sunrise/sunset section for portrait layout"""
        main_frame = QFrame()
        main_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.2); border-radius: 10px;")
        main_layout = QVBoxLayout(main_frame)
        main_layout.setSpacing(8)

        # Date row (day and date)
        date_row_frame = QFrame()
        date_row_layout = QHBoxLayout(date_row_frame)
        date_row_layout.setSpacing(10)

        # Day of week
        self.day_label = QLabel("Wednesday")
        day_font_size = max(18, self.window_width // 15)
        self.day_label.setStyleSheet(
            f"color: white; font-size: {day_font_size}px; font-weight: bold;")
        if hasattr(self, 'inter_font'):
            day_font = QFont(self.inter_font)
            day_font.setPointSize(day_font_size)
            day_font.setBold(True)
            self.day_label.setFont(day_font)
        self.day_label.setAlignment(Qt.AlignCenter)
        date_row_layout.addWidget(self.day_label)

        # Add stretch to center
        date_row_layout.addStretch()

        # Date
        self.date_label = QLabel("Oct 12")
        date_font_size = max(16, self.window_width // 18)
        self.date_label.setStyleSheet(
            f"color: white; font-size: {date_font_size}px; font-weight: bold;")
        if hasattr(self, 'inter_font'):
            date_font = QFont(self.inter_font)
            date_font.setPointSize(date_font_size)
            date_font.setBold(True)
            self.date_label.setFont(date_font)
        self.date_label.setAlignment(Qt.AlignCenter)
        date_row_layout.addWidget(self.date_label)

        main_layout.addWidget(date_row_frame)

        # Sunrise/Sunset row
        sun_row_frame = QFrame()
        sun_row_layout = QHBoxLayout(sun_row_frame)
        sun_row_layout.setSpacing(20)

        # Sunrise (left side)
        sunrise_frame = QFrame()
        sunrise_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.1); border-radius: 8px;")
        sunrise_layout = QVBoxLayout(sunrise_frame)
        sunrise_layout.setSpacing(5)
        sunrise_layout.setAlignment(Qt.AlignCenter)

        # Sunrise title
        sunrise_title = QLabel("Sunrise")
        sunrise_title_font_size = max(12, self.window_width // 30)
        sunrise_title.setStyleSheet(
            f"color: white; font-size: {sunrise_title_font_size}px; font-weight: bold;")
        if hasattr(self, 'inter_font'):
            sunrise_title_font = QFont(self.inter_font)
            sunrise_title_font.setPointSize(sunrise_title_font_size)
            sunrise_title_font.setBold(True)
            sunrise_title.setFont(sunrise_title_font)
        sunrise_title.setAlignment(Qt.AlignCenter)
        sunrise_layout.addWidget(sunrise_title)

        sunrise_icon = QLabel()
        sunrise_icon_size = max(30, self.window_width // 10)  # Larger icons
        sunrise_pixmap = load_sunrise_sunset_icon("sunrise", sunrise_icon_size)
        if sunrise_pixmap:
            sunrise_icon.setPixmap(sunrise_pixmap)
            sunrise_icon.setStyleSheet("background: transparent;")
        else:
            sunrise_icon.setText("🌅")
            sunrise_icon.setStyleSheet(
                f"color: orange; font-size: {sunrise_icon_size}px;")
        sunrise_icon.setAlignment(Qt.AlignCenter)
        sunrise_layout.addWidget(sunrise_icon)

        self.sunrise_label = QLabel("6:48am")
        sunrise_font_size = max(12, self.window_width // 25)
        self.sunrise_label.setStyleSheet(
            f"color: white; font-size: {sunrise_font_size}px;")
        if hasattr(self, 'inter_font'):
            sunrise_font = QFont(self.inter_font)
            sunrise_font.setPointSize(sunrise_font_size)
            self.sunrise_label.setFont(sunrise_font)
        self.sunrise_label.setAlignment(Qt.AlignCenter)
        sunrise_layout.addWidget(self.sunrise_label)
        sun_row_layout.addWidget(sunrise_frame)

        # Minimal stretch to bring icons closer to center
        sun_row_layout.addStretch()

        # Sunset (right side)
        sunset_frame = QFrame()
        sunset_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.1); border-radius: 8px;")
        sunset_layout = QVBoxLayout(sunset_frame)
        sunset_layout.setSpacing(5)
        sunset_layout.setAlignment(Qt.AlignCenter)

        # Sunset title
        sunset_title = QLabel("Sunset")
        sunset_title_font_size = max(12, self.window_width // 30)
        sunset_title.setStyleSheet(
            f"color: white; font-size: {sunset_title_font_size}px; font-weight: bold;")
        if hasattr(self, 'inter_font'):
            sunset_title_font = QFont(self.inter_font)
            sunset_title_font.setPointSize(sunset_title_font_size)
            sunset_title_font.setBold(True)
            sunset_title.setFont(sunset_title_font)
        sunset_title.setAlignment(Qt.AlignCenter)
        sunset_layout.addWidget(sunset_title)

        sunset_icon = QLabel()
        sunset_icon_size = max(30, self.window_width // 10)  # Larger icons
        sunset_pixmap = load_sunrise_sunset_icon("sunset", sunset_icon_size)
        if sunset_pixmap:
            sunset_icon.setPixmap(sunset_pixmap)
            sunset_icon.setStyleSheet("background: transparent;")
        else:
            sunset_icon.setText("🌇")
            sunset_icon.setStyleSheet(
                f"color: orange; font-size: {sunset_icon_size}px;")
        sunset_icon.setAlignment(Qt.AlignCenter)
        sunset_layout.addWidget(sunset_icon)

        self.sunset_label = QLabel("7:13pm")
        sunset_font_size = max(12, self.window_width // 25)
        self.sunset_label.setStyleSheet(
            f"color: white; font-size: {sunset_font_size}px;")
        if hasattr(self, 'inter_font'):
            sunset_font = QFont(self.inter_font)
            sunset_font.setPointSize(sunset_font_size)
            self.sunset_label.setFont(sunset_font)
        self.sunset_label.setAlignment(Qt.AlignCenter)
        sunset_layout.addWidget(self.sunset_label)
        sun_row_layout.addWidget(sunset_frame)

        main_layout.addWidget(sun_row_frame)
        parent_layout.addWidget(main_frame)

    def create_sunrise_sunset_section_portrait(self, parent_layout):
        """Create the sunrise/sunset section for portrait layout"""
        sun_frame = QFrame()
        sun_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.2); border-radius: 10px;")
        sun_layout = QHBoxLayout(sun_frame)
        sun_layout.setSpacing(20)

        # Sunrise
        sunrise_frame = QFrame()
        sunrise_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.1); border-radius: 8px;")
        sunrise_layout = QVBoxLayout(sunrise_frame)
        sunrise_layout.setAlignment(Qt.AlignCenter)
        sunrise_layout.setSpacing(5)

        # Sunrise title
        sunrise_title = QLabel("Sunrise")
        sunrise_title_font_size = max(12, self.window_width // 30)
        sunrise_title.setStyleSheet(
            f"color: white; font-size: {sunrise_title_font_size}px; font-weight: bold;")
        if hasattr(self, 'inter_font'):
            sunrise_title_font = QFont(self.inter_font)
            sunrise_title_font.setPointSize(sunrise_title_font_size)
            sunrise_title_font.setBold(True)
            sunrise_title.setFont(sunrise_title_font)
        sunrise_title.setAlignment(Qt.AlignCenter)
        sunrise_layout.addWidget(sunrise_title)

        sunrise_icon = QLabel()
        sunrise_icon_size = max(30, self.window_width // 10)  # Larger icons
        sunrise_pixmap = load_sunrise_sunset_icon("sunrise", sunrise_icon_size)
        if sunrise_pixmap:
            sunrise_icon.setPixmap(sunrise_pixmap)
            sunrise_icon.setStyleSheet("background: transparent;")
        else:
            sunrise_icon.setText("🌅")
            sunrise_icon.setStyleSheet(
                f"color: orange; font-size: {sunrise_icon_size}px;")
        sunrise_icon.setAlignment(Qt.AlignCenter)
        sunrise_layout.addWidget(sunrise_icon)

        self.sunrise_label = QLabel("6:48am")
        sunrise_font_size = max(12, self.window_width // 25)
        self.sunrise_label.setStyleSheet(
            f"color: white; font-size: {sunrise_font_size}px;")
        if hasattr(self, 'inter_font'):
            sunrise_font = QFont(self.inter_font)
            sunrise_font.setPointSize(sunrise_font_size)
            self.sunrise_label.setFont(sunrise_font)
        self.sunrise_label.setAlignment(Qt.AlignCenter)
        sunrise_layout.addWidget(self.sunrise_label)
        sun_layout.addWidget(sunrise_frame)

        # Minimal stretch to bring icons closer to center
        sun_layout.addStretch()

        # Sunset
        sunset_frame = QFrame()
        sunset_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.1); border-radius: 8px;")
        sunset_layout = QVBoxLayout(sunset_frame)
        sunset_layout.setAlignment(Qt.AlignCenter)
        sunset_layout.setSpacing(5)

        # Sunset title
        sunset_title = QLabel("Sunset")
        sunset_title_font_size = max(12, self.window_width // 30)
        sunset_title.setStyleSheet(
            f"color: white; font-size: {sunset_title_font_size}px; font-weight: bold;")
        if hasattr(self, 'inter_font'):
            sunset_title_font = QFont(self.inter_font)
            sunset_title_font.setPointSize(sunset_title_font_size)
            sunset_title_font.setBold(True)
            sunset_title.setFont(sunset_title_font)
        sunset_title.setAlignment(Qt.AlignCenter)
        sunset_layout.addWidget(sunset_title)

        sunset_icon = QLabel()
        sunset_icon_size = max(30, self.window_width // 10)  # Larger icons
        sunset_pixmap = load_sunrise_sunset_icon("sunset", sunset_icon_size)
        if sunset_pixmap:
            sunset_icon.setPixmap(sunset_pixmap)
            sunset_icon.setStyleSheet("background: transparent;")
        else:
            sunset_icon.setText("🌇")
            sunset_icon.setStyleSheet(
                f"color: orange; font-size: {sunset_icon_size}px;")
        sunset_icon.setAlignment(Qt.AlignCenter)
        sunset_layout.addWidget(sunset_icon)

        self.sunset_label = QLabel("7:13pm")
        sunset_font_size = max(12, self.window_width // 25)
        self.sunset_label.setStyleSheet(
            f"color: white; font-size: {sunset_font_size}px;")
        if hasattr(self, 'inter_font'):
            sunset_font = QFont(self.inter_font)
            sunset_font.setPointSize(sunset_font_size)
            self.sunset_label.setFont(sunset_font)
        self.sunset_label.setAlignment(Qt.AlignCenter)
        sunset_layout.addWidget(self.sunset_label)
        sun_layout.addWidget(sunset_frame)

        parent_layout.addWidget(sun_frame)

    def create_high_low_section_portrait(self, parent_layout):
        """Create the high/low temperature section with thermometer for portrait layout"""
        high_low_frame = QFrame()
        high_low_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.2); border-radius: 10px;")
        high_low_layout = QHBoxLayout(high_low_frame)
        high_low_layout.setSpacing(15)

        # Thermometer icon
        thermometer_frame = QFrame()
        thermometer_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.1); border-radius: 8px;")
        thermometer_layout = QVBoxLayout(thermometer_frame)
        thermometer_layout.setAlignment(Qt.AlignCenter)

        thermometer_icon = QLabel("🌡️")
        thermometer_icon.setStyleSheet(
            f"color: orange; font-size: {max(20, self.window_width // 15)}px;")
        thermometer_icon.setAlignment(Qt.AlignCenter)
        thermometer_layout.addWidget(thermometer_icon)
        high_low_layout.addWidget(thermometer_frame)

        # High/Low temperatures
        temps_frame = QFrame()
        temps_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.1); border-radius: 8px;")
        temps_layout = QVBoxLayout(temps_frame)
        temps_layout.setAlignment(Qt.AlignCenter)
        temps_layout.setSpacing(8)

        # High temperature
        self.high_temp_label = QLabel("H: 92")
        high_font_size = max(16, self.window_width // 18)
        self.high_temp_label.setStyleSheet(
            f"color: white; font-size: {high_font_size}px; font-weight: bold;")
        if hasattr(self, 'inter_font'):
            high_font = QFont(self.inter_font)
            high_font.setPointSize(high_font_size)
            high_font.setBold(True)
            self.high_temp_label.setFont(high_font)
        self.high_temp_label.setAlignment(Qt.AlignCenter)
        temps_layout.addWidget(self.high_temp_label)

        # Low temperature
        self.low_temp_label = QLabel("L: 55")
        low_font_size = max(16, self.window_width // 18)
        self.low_temp_label.setStyleSheet(
            f"color: white; font-size: {low_font_size}px; font-weight: bold;")
        if hasattr(self, 'inter_font'):
            low_font = QFont(self.inter_font)
            low_font.setPointSize(low_font_size)
            low_font.setBold(True)
            self.low_temp_label.setFont(low_font)
        self.low_temp_label.setAlignment(Qt.AlignCenter)
        temps_layout.addWidget(self.low_temp_label)
        high_low_layout.addWidget(temps_frame)

        parent_layout.addWidget(high_low_frame)

    def create_forecast_section_portrait(self, parent_layout):
        """Create the 3-day forecast section for portrait layout (bigger and more prominent)"""
        forecast_frame = QFrame()
        forecast_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.2); border-radius: 10px;")
        forecast_layout = QVBoxLayout(forecast_frame)

        # Forecast title
        forecast_title = QLabel("3 Day Forecast")
        forecast_title_font_size = max(16, self.window_width // 20)
        forecast_title.setStyleSheet(
            f"color: white; font-size: {forecast_title_font_size}px; font-weight: bold;")
        if hasattr(self, 'inter_font'):
            title_font = QFont(self.inter_font)
            title_font.setPointSize(forecast_title_font_size)
            title_font.setBold(True)
            forecast_title.setFont(title_font)
        forecast_title.setAlignment(Qt.AlignCenter)
        forecast_layout.addWidget(forecast_title)

        # Forecast days container - vertical layout for portrait
        days_frame = QFrame()
        days_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.1); border-radius: 5px;")
        days_layout = QVBoxLayout(days_frame)
        days_layout.setSpacing(8)

        # Create 3 forecast day widgets (vertical layout)
        self.forecast_days = []
        day_data = [
            ("THU", "☀️", "H:78 L:65"),
            ("FRI", "☁️", "H:70 L:60"),
            ("SAT", "🌧️", "H:68 L:58")
        ]

        for day_name, icon, temp in day_data:
            day_frame = QFrame()
            day_frame.setStyleSheet(
                "background-color: rgba(26, 26, 46, 0.1); border-radius: 5px;")
            day_layout = QHBoxLayout(day_frame)
            day_layout.setAlignment(Qt.AlignCenter)
            day_layout.setSpacing(15)

            # Day name
            day_label = QLabel(day_name)
            day_name_font_size = max(14, self.window_width // 25)
            day_label.setStyleSheet(
                f"color: white; font-size: {day_name_font_size}px; font-weight: bold;")
            if hasattr(self, 'inter_font'):
                day_name_font = QFont(self.inter_font)
                day_name_font.setPointSize(day_name_font_size)
                day_name_font.setBold(True)
                day_label.setFont(day_name_font)
            day_label.setAlignment(Qt.AlignCenter)
            day_layout.addWidget(day_label)

            # Weather icon (bigger in portrait)
            weather_icon = QLabel(icon)
            forecast_icon_font_size = max(24, self.window_width // 15)
            weather_icon.setStyleSheet(
                f"color: lightblue; font-size: {forecast_icon_font_size}px;")
            weather_icon.setAlignment(Qt.AlignCenter)
            day_layout.addWidget(weather_icon)

            # Temperature
            temp_label = QLabel(temp)
            forecast_temp_font_size = max(12, self.window_width // 30)
            temp_label.setStyleSheet(
                f"color: white; font-size: {forecast_temp_font_size}px;")
            if hasattr(self, 'inter_font'):
                forecast_temp_font = QFont(self.inter_font)
                forecast_temp_font.setPointSize(forecast_temp_font_size)
                temp_label.setFont(forecast_temp_font)
            temp_label.setAlignment(Qt.AlignCenter)
            day_layout.addWidget(temp_label)

            days_layout.addWidget(day_frame)

            self.forecast_days.append({
                'frame': day_frame,
                'day': day_label,
                'icon': weather_icon,
                'temp': temp_label
            })

        forecast_layout.addWidget(days_frame)
        parent_layout.addWidget(forecast_frame)

    def create_forecast_section(self, parent_layout):
        """Create the 5-day forecast section"""
        forecast_frame = QFrame()
        forecast_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.2); border-radius: 10px;")
        forecast_layout = QVBoxLayout(forecast_frame)

        # Forecast title
        forecast_title = QLabel("5-Day Forecast")
        # Adjust font size based on window size - much smaller for compact displays
        forecast_title_font_size = max(10, self.window_width // 80)
        forecast_title.setStyleSheet(
            f"color: white; font-size: {forecast_title_font_size}px; font-weight: bold;")
        # Apply Inter font to forecast title
        if hasattr(self, 'inter_font'):
            title_font = QFont(self.inter_font)
            title_font.setPointSize(forecast_title_font_size)
            title_font.setBold(True)
            forecast_title.setFont(title_font)
        forecast_layout.addWidget(forecast_title)

        # Forecast days container
        days_frame = QFrame()
        days_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.1); border-radius: 5px;")
        days_layout = QHBoxLayout(days_frame)
        # Adjust spacing based on window width - much smaller for compact displays
        forecast_spacing = max(5, self.window_width // 50)
        days_layout.setSpacing(forecast_spacing)

        # Create 5 forecast day widgets
        self.forecast_days = []
        day_data = [
            ("Wed", "☀️", "H:78 L:65"),
            ("Thu", "☁️", "H:70 L:60"),
            ("Fri", "🌧️", "H:68 L:58"),
            ("Sat", "☁️", "H:68 L:58"),
            ("Sun", "☁️", "H:75 L:65")
        ]

        for day_name, icon, temp in day_data:
            day_frame = QFrame()
            day_frame.setStyleSheet(
                "background-color: rgba(26, 26, 46, 0.1); border-radius: 5px;")
            # Use horizontal layout instead of vertical
            day_layout = QHBoxLayout(day_frame)
            day_layout.setAlignment(Qt.AlignCenter)
            day_layout.setSpacing(8)

            # Left side: Day name and temperature
            left_info_layout = QVBoxLayout()
            left_info_layout.setAlignment(Qt.AlignCenter)
            left_info_layout.setSpacing(2)

            # Day name
            day_label = QLabel(day_name)
            # Adjust font size based on window size - much smaller for compact displays
            day_name_font_size = max(8, self.window_width // 100)
            day_label.setStyleSheet(
                f"color: white; font-size: {day_name_font_size}px; font-weight: bold;")
            # Apply Inter font to day name
            if hasattr(self, 'inter_font'):
                day_name_font = QFont(self.inter_font)
                day_name_font.setPointSize(day_name_font_size)
                day_name_font.setBold(True)
                day_label.setFont(day_name_font)
            day_label.setAlignment(Qt.AlignCenter)
            left_info_layout.addWidget(day_label)

            # Temperature
            temp_label = QLabel(temp)
            # Adjust font size based on window size - much smaller for compact displays
            forecast_temp_font_size = max(8, self.window_width // 100)
            temp_label.setStyleSheet(
                f"color: white; font-size: {forecast_temp_font_size}px;")
            # Apply Inter font to forecast temperature
            if hasattr(self, 'inter_font'):
                forecast_temp_font = QFont(self.inter_font)
                forecast_temp_font.setPointSize(forecast_temp_font_size)
                temp_label.setFont(forecast_temp_font)
            temp_label.setAlignment(Qt.AlignCenter)
            left_info_layout.addWidget(temp_label)

            # Add left info to main layout
            day_layout.addLayout(left_info_layout)

            # Right side: Weather icon (bigger now)
            weather_icon = QLabel(icon)
            # Increase icon size since we have more space now
            forecast_icon_font_size = max(18, self.window_width // 40)
            weather_icon.setStyleSheet(
                f"color: lightblue; font-size: {forecast_icon_font_size}px;")
            weather_icon.setAlignment(Qt.AlignCenter)
            day_layout.addWidget(weather_icon)

            days_layout.addWidget(day_frame)

            self.forecast_days.append({
                'frame': day_frame,
                'day': day_label,
                'icon': weather_icon,
                'temp': temp_label
            })

        forecast_layout.addWidget(days_frame)
        parent_layout.addWidget(forecast_frame)

    def create_temperature_graph(self, parent_layout):
        """Create the temperature trend graph section"""
        graph_frame = QFrame()
        graph_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.2); border-radius: 10px;")
        graph_layout = QVBoxLayout(graph_frame)

        # Graph title
        graph_title = QLabel("Temperature Trend")
        # Adjust font size based on window size - much smaller for compact displays
        graph_title_font_size = max(10, self.window_width // 80)
        graph_title.setStyleSheet(
            f"color: white; font-size: {graph_title_font_size}px; font-weight: bold;")
        # Apply Inter font to graph title
        if hasattr(self, 'inter_font'):
            graph_title_font = QFont(self.inter_font)
            graph_title_font.setPointSize(graph_title_font_size)
            graph_title_font.setBold(True)
            graph_title.setFont(graph_title_font)
        graph_layout.addWidget(graph_title)

        # Temperature graph
        self.temp_graph = TemperatureGraph()
        # Set minimum height based on window size (about 1/3 of window height)
        min_height = max(100, self.window_height // 3)
        self.temp_graph.setMinimumHeight(min_height)
        graph_layout.addWidget(self.temp_graph)

        parent_layout.addWidget(graph_frame)

    def create_location_section(self, parent_layout):
        """Create the location display section with BG Scrap button"""
        location_frame = QFrame()
        location_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.2); border-radius: 10px;")
        location_layout = QHBoxLayout(location_frame)

        # Location label (left side)
        self.location_label = QLabel(self.location_name)
        # Adjust font size based on window size - much smaller for compact displays
        location_font_size = max(10, self.window_width // 80)
        self.location_label.setStyleSheet(
            f"color: white; font-size: {location_font_size}px;")
        # Apply Inter font to location label
        if hasattr(self, 'inter_font'):
            location_font = QFont(self.inter_font)
            location_font.setPointSize(location_font_size)
            self.location_label.setFont(location_font)
        self.location_label.setAlignment(Qt.AlignCenter)
        location_layout.addWidget(self.location_label)

        # Add stretch to push button to the right
        location_layout.addStretch()

        # Countdown display (right side, before button)
        self.countdown_label = QLabel("")
        # Style the countdown label
        countdown_font_size = max(8, self.window_width // 120)
        self.countdown_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.8);
                font-size: {countdown_font_size}px;
                font-weight: 600;
                padding: 4px 8px;
                background-color: rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                min-width: 40px;
            }}
        """)

        # Apply Inter font to countdown label
        if hasattr(self, 'inter_font'):
            countdown_font = QFont(self.inter_font)
            countdown_font.setPointSize(countdown_font_size)
            countdown_font.setBold(True)
            self.countdown_label.setFont(countdown_font)

        self.countdown_label.setAlignment(Qt.AlignCenter)
        location_layout.addWidget(self.countdown_label)

        # BG Scrap button (right side)
        self.bg_scrap_button = QPushButton("BG Scrap")
        # Style the button with modern, compact design
        button_font_size = max(9, self.window_width // 120)
        self.bg_scrap_button.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 100, 100, 0.85);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 6px 12px;
                font-size: {button_font_size}px;
                font-weight: 600;
                min-width: 60px;
                min-height: 24px;
                max-height: 28px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 120, 120, 0.95);
                transform: scale(1.02);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 80, 80, 1.0);
                transform: scale(0.98);
            }}
        """)

        # Apply Inter font to button
        if hasattr(self, 'inter_font'):
            button_font = QFont(self.inter_font)
            button_font.setPointSize(button_font_size)
            button_font.setBold(True)
            self.bg_scrap_button.setFont(button_font)

        # Connect button click to handler
        self.bg_scrap_button.clicked.connect(self.on_bg_scrap_clicked)
        location_layout.addWidget(self.bg_scrap_button)

        parent_layout.addWidget(location_frame)

    def setup_timers(self):
        """Setup timers for updating time and other dynamic content"""
        # Timer for updating time
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(self.time_update_interval)
        print(f"⏰ Time timer set to {self.time_update_interval}ms")

        # Timer for updating date and day of week
        self.date_timer = QTimer()
        self.date_timer.timeout.connect(self.update_date)
        self.date_timer.start(self.date_update_interval)
        print(f"📅 Date timer set to {self.date_update_interval}ms")

        # Initial updates
        self.update_time()
        self.update_date()

        # Update graph after window is shown (only for landscape layout)
        # QTimer.singleShot(100, self.update_graph)  # Disabled for portrait layout

        # Timer for updating weather data
        self.weather_timer = QTimer()
        self.weather_timer.timeout.connect(self.load_weather_data)
        self.weather_timer.start(self.weather_update_interval)
        print(f"🌤️  Weather timer set to {self.weather_update_interval}ms")

        # Timer for updating temperature graph (disabled for portrait layout)
        # self.graph_timer = QTimer()
        # self.graph_timer.timeout.connect(self.update_graph_from_weather)
        # self.graph_timer.start(300000)  # Update every 5 minutes
        # print(f"📊 Graph timer set to 300000ms (5 minutes)")

        # Timer for updating background based on time of day
        self.background_timer = QTimer()
        self.background_timer.timeout.connect(self.check_and_update_background)
        self.background_timer.start(self.background_update_interval)
        print(f"🎨 Background timer set to {self.background_update_interval}ms")

        # Timer for updating countdown display
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown_display)
        self.countdown_timer.start(1000)  # Update every second
        print(f"⏰ Countdown timer set to 1000ms (1 second)")

        # Store current time period to detect changes
        self.current_time_period = self.get_current_time_period()

    def update_time(self):
        """Update the current time display"""
        current_time = datetime.datetime.now().strftime("%H:%M")
        self.time_label.setText(current_time)

    def update_date(self):
        """Update the current date display"""
        now = datetime.datetime.now()
        day_name = now.strftime("%A")
        date_str = now.strftime("%B %d")

        # Update combined day and date label
        self.day_date_label.setText(f"{day_name}, {date_str}")

        print(f"📅 Updated date display: {day_name}, {date_str}")

    def update_countdown_display(self):
        """Update the countdown display with remaining time"""
        if not self.motion_service:
            self.countdown_label.setText("")
            return

        countdown_info = self.motion_service.get_countdown_info()
        if countdown_info and countdown_info['is_active']:
            remaining = countdown_info['remaining_seconds']
            self.countdown_label.setText(f"Off: {remaining}s")
        else:
            self.countdown_label.setText("")

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse movement events to reset display timer"""
        if self.motion_service:
            self.motion_service.reset_dimming_timer()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events to reset display timer"""
        if self.motion_service:
            self.motion_service.reset_dimming_timer()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events to reset display timer"""
        if self.motion_service:
            self.motion_service.reset_dimming_timer()
        super().mouseReleaseEvent(event)

    def update_graph(self):
        """Update the temperature graph"""
        # Get the graph widget size
        size = self.temp_graph.size()
        self.temp_graph.draw_graph(size.width(), size.height())

    def update_temperature_graph(self, hourly_data: List[Dict]):
        """Update the temperature graph with hourly data"""
        try:
            print(
                f"📊 Updating temperature graph with {len(hourly_data)} hourly data points")

            # Set the hourly data in the graph
            self.temp_graph.set_hourly_data(hourly_data)

            # Redraw the graph
            self.update_graph()

            print("✅ Temperature graph updated successfully")

        except Exception as e:
            print(f"❌ Error updating temperature graph: {e}")

    def update_graph_from_weather(self):
        """Update the temperature graph with fresh weather data"""
        if not self.weather_service:
            print("⚠️  Weather service not available for graph update")
            return

        try:
            print("📊 Updating temperature graph with fresh weather data...")

            # Get fresh hourly forecast data
            hourly_data = self.weather_service.get_hourly_forecast(
                self.location)

            # Update the graph
            self.update_temperature_graph(hourly_data)

        except Exception as e:
            print(f"❌ Error updating graph from weather: {e}")

    def get_current_time_period(self):
        """Get the current time period (sunrise, morning, etc.)"""
        if not self.wallpaper_generator:
            return "morning"  # Default fallback

        try:
            current_epoch = time.time()
            return self.wallpaper_generator._epoch_to_time_of_day(current_epoch)
        except Exception as e:
            print(f"⚠️  Error getting time period: {e}")
            return "morning"  # Default fallback

    def check_and_update_background(self):
        """Check if time period has changed and update background if needed"""
        if not self.wallpaper_generator:
            print("⚠️  WallpaperGenerator not available, skipping background check")
            return

        try:
            new_time_period = self.get_current_time_period()

            if new_time_period != self.current_time_period:
                print(
                    f"🕐 Time period changed: {self.current_time_period} → {new_time_period}")
                print("🎨 Updating background for new time period...")

                # Update the stored time period
                self.current_time_period = new_time_period

                # Generate and set new background
                self.update_background_for_current_conditions()
            else:
                print(f"🕐 Time period unchanged: {self.current_time_period}")

        except Exception as e:
            print(f"❌ Error checking time period: {e}")

    def update_background_for_current_conditions(self):
        """Update the background based on current weather and time conditions"""
        if not self.wallpaper_generator:
            print("⚠️  WallpaperGenerator not available, skipping background update")
            return

        try:
            print("🎨 Generating new background for current conditions...")
            generated_wallpaper = self.generate_current_weather_wallpaper()

            if generated_wallpaper and os.path.exists(generated_wallpaper):
                print(
                    f"✅ Updated background: {os.path.basename(generated_wallpaper)}")
                self.set_background_image(generated_wallpaper)
            else:
                print("⚠️  Failed to generate new background, keeping current one")

        except Exception as e:
            print(f"❌ Error updating background: {e}")

    def on_bg_scrap_clicked(self):
        """Handle BG Scrap button click - generate new random background"""
        print("🎨 BG Scrap button clicked - generating new random background...")

        # Log user feedback that they don't like the current image
        self.log_user_feedback_dislike()

        # Disable button temporarily to prevent multiple clicks
        self.bg_scrap_button.setEnabled(False)
        self.bg_scrap_button.setText("Generating...")

        try:
            # Store current background path for potential removal
            current_background = getattr(self, 'current_background_path', None)

            # Generate new random background
            new_background = self.generate_random_background()

            if new_background and os.path.exists(new_background):
                # Set new background
                self.set_background_image(new_background)
                self.current_background_path = new_background

                # Remove old background if it exists and is different
                if current_background and current_background != new_background and os.path.exists(current_background):
                    try:
                        os.remove(current_background)
                        print(
                            f"🗑️  Removed old background: {os.path.basename(current_background)}")
                    except Exception as e:
                        print(f"⚠️  Could not remove old background: {e}")

                print(
                    f"✅ New background set: {os.path.basename(new_background)}")
            else:
                print("⚠️  Failed to generate new background")

        except Exception as e:
            print(f"❌ Error generating new background: {e}")
        finally:
            # Re-enable button
            self.bg_scrap_button.setEnabled(True)
            self.bg_scrap_button.setText("BG Scrap")

    def generate_random_background(self):
        """Generate a completely random background (not based on current weather)"""
        if not self.wallpaper_generator:
            print("⚠️  WallpaperGenerator not available, using existing wallpapers")
            if self.wallpaper_images:
                return random.choice(self.wallpaper_images)
            return None

        try:
            print("🎨 Generating completely random background...")

            # Load conditions map to get random weather condition
            conditions_map = self.wallpaper_generator._load_maps()[1]
            random_condition = random.choice(list(conditions_map.keys()))

            # Use current time for time of day
            current_epoch = time.time()

            # Generate with random style and random conditions
            result = self.wallpaper_generator.generate_wallpaper(
                style="random",  # Randomly select from available styles
                epoch_time=current_epoch,
                weather_condition=random_condition,
                target_size=(self.window_width, self.window_height),
                try_resize=True,
                save_prompt=False
            )

            print(f"✅ Generated random background: {result['filename']}")
            print(f"   Style: random, Condition: {random_condition}")
            print(f"   Path: {result['path']}")
            return result['path']

        except Exception as e:
            print(f"❌ Error generating random background: {e}")
            # Fallback to existing wallpapers
            if self.wallpaper_images:
                return random.choice(self.wallpaper_images)
            return None

    def log_user_feedback_dislike(self):
        """Log user feedback that they don't like the current background image"""
        try:
            current_background = getattr(self, 'current_background_path', None)
            if current_background:
                # Create feedback directory if it doesn't exist
                feedback_dir = "feedback"
                os.makedirs(feedback_dir, exist_ok=True)

                # Create feedback file with timestamp and image info
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                feedback_file = os.path.join(
                    feedback_dir, f"disliked_images_{timestamp}.json")

                # Load existing feedback or create new
                feedback_data = []
                if os.path.exists(feedback_file):
                    try:
                        with open(feedback_file, 'r') as f:
                            feedback_data = json.load(f)
                    except:
                        feedback_data = []

                # Add current feedback
                feedback_entry = {
                    "timestamp": timestamp,
                    "image_path": current_background,
                    "image_filename": os.path.basename(current_background),
                    "action": "disliked",
                    "user_action": "bg_scrap_clicked"
                }
                feedback_data.append(feedback_entry)

                # Save feedback
                with open(feedback_file, 'w') as f:
                    json.dump(feedback_data, f, indent=2)

                print(
                    f"📝 Logged user dislike for: {os.path.basename(current_background)}")
                print(f"   Feedback saved to: {feedback_file}")

                # TODO: In the future, this feedback could be used to:
                # 1. Train a local model to avoid similar images
                # 2. Send feedback to OpenAI for model improvement
                # 3. Adjust generation parameters based on user preferences
                # 4. Create a "blacklist" of image characteristics to avoid

            else:
                print("⚠️  No current background to log feedback for")

        except Exception as e:
            print(f"⚠️  Error logging user feedback: {e}")

    def load_weather_data(self):
        """Load current weather and forecast data from the weather service"""
        if not self.weather_service:
            print("⚠️  Weather service not available, using fallback data")
            return

        try:
            print("🌤️  Loading weather data...")

            # Get current weather using zip code
            current_weather = self.weather_service.get_current_weather(
                self.location)
            self.update_current_weather_display(current_weather)

            # Get forecast using zip code
            forecast_data = self.weather_service.get_forecast_weather(
                self.location)
            self.update_forecast_display(forecast_data)

            # Get hourly forecast for the temperature graph (disabled for portrait layout)
            # hourly_data = self.weather_service.get_hourly_forecast(
            #     self.location)
            # self.update_temperature_graph(hourly_data)

            print("✅ Weather data loaded successfully")

        except Exception as e:
            print(f"❌ Error loading weather data: {e}")

    def update_current_weather_display(self, weather_data: Dict):
        """Update the current weather display with real data"""
        try:
            # Update current temperature
            temp = weather_data.get('temperature', 72)
            self.temp_label.setText(f"{temp}°")

            # Update high/low temperatures (separate labels now)
            high_temp = weather_data.get('high_temp', 78)
            low_temp = weather_data.get('low_temp', 65)
            self.high_temp_label.setText(f"H:{high_temp}")
            self.low_temp_label.setText(f"L:{low_temp}")

            # Update sunrise/sunset times (formatted for portrait layout)
            sunrise = weather_data.get('sunrise', '06:30')
            sunset = weather_data.get('sunset', '18:30')
            # Format times to include am/pm
            try:
                sunrise_time = datetime.datetime.strptime(
                    sunrise, '%H:%M').strftime('%I:%M%p').lower()
                sunset_time = datetime.datetime.strptime(
                    sunset, '%H:%M').strftime('%I:%M%p').lower()
                self.sunrise_label.setText(sunrise_time)
                self.sunset_label.setText(sunset_time)
            except:
                # Fallback if time parsing fails
                self.sunrise_label.setText(f"{sunrise}am")
                self.sunset_label.setText(f"{sunset}pm")

            # Get icon path for image-based icons
            icon_path = weather_data.get('icon_path')
            emoji_icon = weather_data.get('icon', '☀️')
            text_icon = weather_data.get('text_icon', 'SUN')
            condition = weather_data.get('condition', 'CLEAR')
            description = weather_data.get('description', 'Clear')

            # Try to use image icon first if enabled, fallback to text/emoji
            if self.use_image_icons and icon_path and os.path.exists(icon_path):
                try:
                    # Load and display the icon image
                    pixmap = QPixmap(icon_path)
                    if not pixmap.isNull():
                        # Scale the icon to appropriate size (64x64)
                        scaled_pixmap = pixmap.scaled(
                            64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.weather_icon.setPixmap(scaled_pixmap)
                        self.weather_icon.setText("")  # Clear any text
                        print(f"🌤️  Using image icon: {icon_path}")
                    else:
                        raise Exception("Failed to load pixmap")
                except Exception as e:
                    print(f"⚠️  Failed to load image icon: {e}")
                    # Fallback to text/emoji
                    self._set_text_or_emoji_icon(
                        weather_data, self.weather_icon)
            else:
                if not self.use_image_icons:
                    print(f"🌤️  Image icons disabled, using text/emoji")
                else:
                    print(f"⚠️  Icon path not found or invalid: {icon_path}")
                # Fallback to text/emoji
                self._set_text_or_emoji_icon(weather_data, self.weather_icon)

            # Force UI refresh
            self.weather_icon.repaint()
            self.weather_icon.update()

            # Log the update with more detail
            print(
                f"🌤️  Updated current weather: {temp}°F ({condition}: {description})")
            print(
                f"🔍 Debug: Weather icon text is now: '{self.weather_icon.text()}'")
            print(
                f"🔍 Available options - Emoji: {emoji_icon}, Text: {text_icon}")

        except Exception as e:
            print(f"❌ Error updating current weather display: {e}")

    def _set_text_or_emoji_icon(self, weather_data: Dict, icon_widget: QLabel):
        """Set text or emoji icon as fallback for any weather icon widget"""
        emoji_icon = weather_data.get('icon', '☀️')
        text_icon = weather_data.get('text_icon', 'SUN')

        # Choose icon type based on configuration
        if self.use_text_icons:
            icon_to_use = text_icon
            print(f"🌤️  Using text icon fallback: {text_icon}")
        else:
            icon_to_use = emoji_icon
            print(f"🌤️  Using emoji icon fallback: {emoji_icon}")

        # Clear any pixmap and set text
        icon_widget.setPixmap(QPixmap())
        icon_widget.setText(icon_to_use)

    def update_forecast_display(self, forecast_data: List[Dict]):
        """Update the forecast display with real data"""
        try:
            # For portrait layout, limit to 3 days
            # Limit to 3 days for portrait
            for i, day_data in enumerate(forecast_data[:3]):
                if i < len(self.forecast_days):
                    forecast_widget = self.forecast_days[i]

                    # Update day name with real data (short format for portrait)
                    day_name = day_data.get('day', 'Day')
                    # Convert to short format (e.g., "Wednesday" -> "WED")
                    try:
                        day_obj = datetime.datetime.strptime(day_name, '%A')
                        short_day = day_obj.strftime('%a').upper()
                    except:
                        short_day = day_name[:3].upper()
                    forecast_widget['day'].setText(short_day)

                    # Update weather icon using same logic as current weather
                    icon_path = day_data.get('icon_path')
                    emoji_icon = day_data.get('icon', '☀️')
                    text_icon = day_data.get('text_icon', 'SUN')
                    condition = day_data.get('condition', 'CLEAR')
                    description = day_data.get('description', 'Clear')

                    # Try to use image icon first if enabled, fallback to text/emoji
                    if self.use_image_icons and icon_path and os.path.exists(icon_path):
                        try:
                            # Load and display the icon image
                            pixmap = QPixmap(icon_path)
                            if not pixmap.isNull():
                                # Scale the icon to larger size since we have more space now
                                forecast_icon_size = max(
                                    32, self.window_width // 25)
                                scaled_pixmap = pixmap.scaled(
                                    forecast_icon_size, forecast_icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                                forecast_widget['icon'].setPixmap(
                                    scaled_pixmap)
                                forecast_widget['icon'].setText(
                                    "")  # Clear any text
                                print(
                                    f"🌤️  Using forecast image icon: {icon_path}")
                            else:
                                raise Exception("Failed to load pixmap")
                        except Exception as e:
                            print(
                                f"⚠️  Failed to load forecast image icon: {e}")
                            # Fallback to text/emoji
                            self._set_text_or_emoji_icon(
                                day_data, forecast_widget['icon'])
                    else:
                        if not self.use_image_icons:
                            print(
                                f"🌤️  Image icons disabled for forecast, using text/emoji")
                        else:
                            print(
                                f"⚠️  Forecast icon path not found or invalid: {icon_path}")
                        # Fallback to text/emoji
                        self._set_text_or_emoji_icon(
                            day_data, forecast_widget['icon'])

                    # No temperature display in forecast for portrait layout
                    pass

            print(f"Updated forecast for {len(forecast_data)} days")

        except Exception as e:
            print(f"Error updating forecast display: {e}")

    def cleanup(self):
        """Cleanup motion detection and display control services"""
        try:
            if hasattr(self, 'motion_service') and self.motion_service:
                self.motion_service.cleanup()
                print("✅ Motion detection service cleaned up")

            if hasattr(self, 'display_controller') and self.display_controller:
                self.display_controller.cleanup()
                print("✅ Display controller cleaned up")

        except Exception as e:
            print(f"⚠️  Error during cleanup: {e}")

    def closeEvent(self, event):
        """Override closeEvent to ensure proper cleanup"""
        print("🔄 Closing weather app - performing cleanup...")
        self.cleanup()
        event.accept()
