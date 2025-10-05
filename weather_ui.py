import sys
from PyQt5.QtWidgets import QApplication

# Import the separated classes
from bin.weather_app import WeatherApp


def main():
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Create and show the main window
    window = WeatherApp()
    window.show()

    # Start the event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
