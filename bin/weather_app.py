from .temperature_graph import TemperatureGraph
from .weather_service_openweather import WeatherService
from .motion_detection_service import MotionDetectionService, DisplayState as MotionDisplayState
from .display_controller import DisplayController, DisplayState as ControllerDisplayState
import os
import random
import time
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QFrame)
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QPixmap, QPalette, QBrush, QFont
import datetime
from typing import Dict, List, Optional
import json

# Import the WallpaperGenerator class
import importlib.util
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
            self.wallpaper_generator = WallpaperGenerator(
                day_night_json="conf/day_night.json",
                conditions_json="conf/gcp_conditions.json",
                output_dir="images/generated_wallpapers"
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

        # Load location from environment first
        self.location = os.getenv('LOCATION_ZIP_CODE', '95037')
        self.location_name = os.getenv('LOCATION_NAME', 'Morgan Hill, CA')

        # Load icon preferences
        self.use_text_icons = os.getenv(
            'USE_TEXT_ICONS', 'false').lower() == 'true'
        self.use_image_icons = os.getenv(
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
        wallpaper_base_path = "/Users/ericparker/Documents/weatherPi/images/generated_wallpapers/photoreal-soft"

        if os.path.exists(wallpaper_base_path):
            # Get all time-of-day folders
            time_folders = [f for f in os.listdir(wallpaper_base_path)
                            if os.path.isdir(os.path.join(wallpaper_base_path, f)) and not f.startswith('_')]

            for time_folder in time_folders:
                time_path = os.path.join(wallpaper_base_path, time_folder)
                # Get all PNG files in each time folder
                png_files = [f for f in os.listdir(
                    time_path) if f.endswith('.png')]

                for png_file in png_files:
                    full_path = os.path.join(time_path, png_file)
                    wallpaper_images.append(full_path)

        print(f"Found {len(wallpaper_images)} wallpaper images")
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

            # Try to load from weather.conf file
            config_path = "conf/weather.conf"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()

                            # Check if this is a timing configuration
                            if key in default_config:
                                try:
                                    self.__dict__[key.lower()] = int(value)
                                    if key in ['WINDOW_WIDTH', 'WINDOW_HEIGHT']:
                                        print(f"✅ Loaded {key}: {value}px")
                                    else:
                                        print(f"✅ Loaded {key}: {value}ms")
                                except ValueError:
                                    print(
                                        f"⚠️  Invalid value for {key}: {value}, using default")
                                    self.__dict__[
                                        key.lower()] = default_config[key]
                            else:
                                # Set environment variable for other configs
                                os.environ[key] = value
            else:
                print(
                    f"⚠️  Config file not found: {config_path}, using defaults")

            # Set defaults for any missing values
            for key, default_value in default_config.items():
                if not hasattr(self, key.lower()):
                    self.__dict__[key.lower()] = default_value
                    if key in ['WINDOW_WIDTH', 'WINDOW_HEIGHT']:
                        print(f"📋 Using default {key}: {default_value}px")
                    else:
                        print(f"📋 Using default {key}: {default_value}ms")

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
                'DISPLAY_DIMMING_TIMEOUT': 60,
                'MOTION_TEST_MODE': False
            }

            # Try to load from weather.conf file
            config_path = "conf/weather.conf"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()

                            # Check if this is a motion configuration
                            if key in default_config:
                                try:
                                    if key == 'MOTION_TEST_MODE':
                                        self.__dict__[
                                            key.lower()] = value.lower() == 'true'
                                    else:
                                        self.__dict__[key.lower()] = int(value)
                                    print(f"✅ Loaded {key}: {value}")
                                except ValueError:
                                    print(
                                        f"⚠️  Invalid value for {key}: {value}, using default")
                                    self.__dict__[
                                        key.lower()] = default_config[key]
                            else:
                                # Set environment variable for other configs
                                os.environ[key] = value
            else:
                print(
                    f"⚠️  Config file not found: {config_path}, using defaults")

            # Set defaults for any missing values
            for key, default_value in default_config.items():
                if not hasattr(self, key.lower()):
                    self.__dict__[key.lower()] = default_value
                    print(f"📋 Using default {key}: {default_value}")

        except Exception as e:
            print(f"⚠️  Error loading motion config: {e}, using defaults")
            # Set all defaults
            self.motion_sensor_pin = 18
            self.display_timeout = 60
            self.display_dimming_timeout = 60
            self.motion_test_mode = False

    def setup_motion_detection(self):
        """Setup motion detection service"""
        try:
            self.motion_service = MotionDetectionService(
                motion_sensor_pin=self.motion_sensor_pin,
                display_timeout=self.display_timeout,
                display_dimming_timeout=self.display_dimming_timeout,
                test_mode=self.motion_test_mode
            )

            # Set up callbacks
            self.motion_service.set_motion_detected_callback(
                self.on_motion_detected)
            self.motion_service.set_display_dim_callback(self.on_display_dim)
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
        print("🔍 Motion detected - starting display timer")
        if self.motion_service:
            self.motion_service.start_display_timer()

    def on_display_dim(self):
        """Callback for when display should dim"""
        print("🖥️  Dimming display")
        if self.display_controller:
            self.display_controller.set_display_state(
                ControllerDisplayState.DIMMED)

    def on_display_off(self):
        """Callback for when display should turn off"""
        print("🖥️  Turning off display")
        if self.display_controller:
            self.display_controller.set_display_state(
                ControllerDisplayState.OFF)

    def on_display_active(self):
        """Callback for when display should become active"""
        print("🖥️  Activating display")
        if self.display_controller:
            self.display_controller.set_display_state(
                ControllerDisplayState.ACTIVE)

    def generate_current_weather_wallpaper(self):
        """Generate a wallpaper based on current real weather conditions"""
        if not self.wallpaper_generator:
            print("⚠️  WallpaperGenerator not available, skipping generation")
            return None

        try:
            print("🎨 Generating current weather wallpaper...")
            result = self.wallpaper_generator.generate_current_weather_wallpaper(
                style="photoreal-soft",  # Use photoreal-soft style for better quality
                location=self.location,  # Use zip code from environment
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
            print(f"❌ Error generating current weather wallpaper: {e}")
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

    def setup_window(self):
        """Configure the main window"""
        self.setWindowTitle("Weather App")
        # Use configurable window dimensions
        self.setGeometry(100, 100, self.window_width, self.window_height)
        # Force the window to stay at the configured size
        self.setFixedSize(self.window_width, self.window_height)
        # Background will be set by set_random_background()

    def create_widgets(self):
        """Create all UI widgets"""
        central_widget = QWidget()
        # Make central widget transparent so background shows through
        central_widget.setStyleSheet("background-color: transparent;")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        # Adjust spacing and margins based on window size - much smaller for compact displays
        # Minimum 5px, scale with window
        spacing = max(5, self.window_height // 50)
        # Minimum 5px, scale with window
        margin = max(5, self.window_width // 100)
        main_layout.setSpacing(spacing)
        main_layout.setContentsMargins(margin, margin, margin, margin)

        # Top row: Time, Current Weather, Date
        self.create_top_row(main_layout)

        # 5-day forecast section
        self.create_forecast_section(main_layout)

        # Temperature trend graph section
        self.create_temperature_graph(main_layout)

        # Location section
        self.create_location_section(main_layout)

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
        # Adjust font size based on window size - much smaller for compact displays
        time_font_size = max(16, self.window_width // 40)
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
        self.day_label.setStyleSheet(
            f"color: white; font-size: {medium_font_size}px;")
        self.day_label.setAlignment(Qt.AlignCenter)
        # Apply Inter font to day label
        if hasattr(self, 'inter_font'):
            day_font = QFont(self.inter_font)
            day_font.setPointSize(medium_font_size)
            self.day_label.setFont(day_font)
        date_layout.addWidget(self.day_label)

        self.date_label = QLabel("April 23")
        self.date_label.setStyleSheet(
            f"color: white; font-size: {medium_font_size}px;")
        self.date_label.setAlignment(Qt.AlignCenter)
        # Apply Inter font to date label
        if hasattr(self, 'inter_font'):
            date_font = QFont(self.inter_font)
            date_font.setPointSize(medium_font_size)
            self.date_label.setFont(date_font)
        date_layout.addWidget(self.date_label)
        top_layout.addWidget(date_frame)

        parent_layout.addWidget(top_frame)

    def create_forecast_section(self, parent_layout):
        """Create the 5-day forecast section"""
        forecast_frame = QFrame()
        forecast_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.2); border-radius: 10px;")
        forecast_layout = QVBoxLayout(forecast_frame)

        # Forecast title
        forecast_title = QLabel("5-Day Forecast")
        forecast_title.setStyleSheet(
            "color: white; font-size: 14px; font-weight: bold;")
        # Apply Inter font to forecast title
        if hasattr(self, 'inter_font'):
            title_font = QFont(self.inter_font)
            title_font.setPointSize(14)
            title_font.setBold(True)
            forecast_title.setFont(title_font)
        forecast_layout.addWidget(forecast_title)

        # Forecast days container
        days_frame = QFrame()
        days_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.1); border-radius: 5px;")
        days_layout = QHBoxLayout(days_frame)
        days_layout.setSpacing(20)

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
            day_layout = QVBoxLayout(day_frame)
            day_layout.setAlignment(Qt.AlignCenter)

            # Day name
            day_label = QLabel(day_name)
            day_label.setStyleSheet("color: white; font-size: 10px;")
            # Apply Inter font to day name
            if hasattr(self, 'inter_font'):
                day_name_font = QFont(self.inter_font)
                day_name_font.setPointSize(10)
                day_label.setFont(day_name_font)
            day_label.setAlignment(Qt.AlignCenter)
            day_layout.addWidget(day_label)

            # Weather icon
            weather_icon = QLabel(icon)
            weather_icon.setStyleSheet("color: lightblue; font-size: 16px;")
            weather_icon.setAlignment(Qt.AlignCenter)
            day_layout.addWidget(weather_icon)

            # Temperature
            temp_label = QLabel(temp)
            temp_label.setStyleSheet("color: white; font-size: 10px;")
            # Apply Inter font to forecast temperature
            if hasattr(self, 'inter_font'):
                forecast_temp_font = QFont(self.inter_font)
                forecast_temp_font.setPointSize(10)
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

    def create_temperature_graph(self, parent_layout):
        """Create the temperature trend graph section"""
        graph_frame = QFrame()
        graph_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.2); border-radius: 10px;")
        graph_layout = QVBoxLayout(graph_frame)

        # Graph title
        graph_title = QLabel("Temperature Trend")
        graph_title.setStyleSheet(
            "color: white; font-size: 14px; font-weight: bold;")
        # Apply Inter font to graph title
        if hasattr(self, 'inter_font'):
            graph_title_font = QFont(self.inter_font)
            graph_title_font.setPointSize(14)
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
        """Create the location display section"""
        location_frame = QFrame()
        location_frame.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.2); border-radius: 10px;")
        location_layout = QHBoxLayout(location_frame)

        self.location_label = QLabel(self.location_name)
        self.location_label.setStyleSheet("color: white; font-size: 14px;")
        # Apply Inter font to location label
        if hasattr(self, 'inter_font'):
            location_font = QFont(self.inter_font)
            location_font.setPointSize(14)
            self.location_label.setFont(location_font)
        self.location_label.setAlignment(Qt.AlignCenter)
        location_layout.addWidget(self.location_label)

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

        # Update graph after window is shown
        QTimer.singleShot(100, self.update_graph)

        # Timer for updating weather data
        self.weather_timer = QTimer()
        self.weather_timer.timeout.connect(self.load_weather_data)
        self.weather_timer.start(self.weather_update_interval)
        print(f"🌤️  Weather timer set to {self.weather_update_interval}ms")

        # Timer for updating temperature graph (more frequent updates)
        self.graph_timer = QTimer()
        self.graph_timer.timeout.connect(self.update_graph_from_weather)
        self.graph_timer.start(300000)  # Update every 5 minutes
        print(f"📊 Graph timer set to 300000ms (5 minutes)")

        # Timer for updating background based on time of day
        self.background_timer = QTimer()
        self.background_timer.timeout.connect(self.check_and_update_background)
        self.background_timer.start(self.background_update_interval)
        print(f"🎨 Background timer set to {self.background_update_interval}ms")

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

        self.day_label.setText(day_name)
        self.date_label.setText(date_str)

        print(f"📅 Updated date display: {day_name}, {date_str}")

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

            # Get hourly forecast for the temperature graph
            hourly_data = self.weather_service.get_hourly_forecast(
                self.location)
            self.update_temperature_graph(hourly_data)

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

            # Update sunrise/sunset times (separate labels now)
            sunrise = weather_data.get('sunrise', '06:30')
            sunset = weather_data.get('sunset', '18:30')
            self.sunrise_label.setText(f"↑{sunrise}")
            self.sunset_label.setText(f"↓{sunset}")

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
            for i, day_data in enumerate(forecast_data[:5]):  # Limit to 5 days
                if i < len(self.forecast_days):
                    forecast_widget = self.forecast_days[i]

                    # Update day name with real data
                    day_name = day_data.get('day', 'Day')
                    forecast_widget['day'].setText(day_name)

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
                                # Scale the icon to appropriate size (32x32 for forecast)
                                scaled_pixmap = pixmap.scaled(
                                    32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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

                    # Update temperature (now shows high/low format)
                    temp = day_data.get('temperature', "H:72 L:65")
                    forecast_widget['temp'].setText(temp)

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
