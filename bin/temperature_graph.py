from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPen, QColor, QBrush, QPainter
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class TemperatureGraph(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setStyleSheet(
            "background-color: rgba(26, 26, 46, 0.1); border: none; border-radius: 5px;")

        # Disable scrollbars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Ensure content fits within the view
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.NoDrag)

        # Store hourly temperature data
        self.hourly_data: List[Dict] = []
        # Index of current hour (2 hours back + current = index 2)
        self.current_hour_index = 2

    def set_hourly_data(self, hourly_data: List[Dict]):
        """Set the hourly temperature data for the graph"""
        self.hourly_data = hourly_data
        # Current hour is at index 2 (2 hours back + current)
        self.current_hour_index = 2

    def draw_graph(self, width, height):
        """Draw the temperature bar graph"""
        self.scene.clear()

        # Set the scene size to match the view size to prevent scrollbars
        self.scene.setSceneRect(0, 0, width, height)

        if not self.hourly_data:
            self._draw_placeholder_graph(width, height)
            return

        # Calculate graph dimensions
        margin_left = 50
        margin_right = 50
        margin_top = 30
        margin_bottom = 50
        graph_width = width - margin_left - margin_right
        graph_height = height - margin_top - margin_bottom

        # Draw grid lines
        pen = QPen(QColor("grey"), 1)

        # Horizontal grid lines
        for i in range(4):
            y = margin_top + (i * graph_height / 3)
            self.scene.addLine(margin_left, y, width - margin_right, y, pen)

        # Vertical grid lines (every 2 hours)
        num_bars = len(self.hourly_data)
        bar_width = graph_width / num_bars if num_bars > 0 else 0

        for i in range(0, num_bars, 2):  # Every 2 hours
            x = margin_left + (i * bar_width)
            self.scene.addLine(x, margin_top, x, height - margin_bottom, pen)

        # Calculate temperature range
        temps = [data.get('temperature', 70) for data in self.hourly_data]
        min_temp = min(temps) if temps else 60
        max_temp = max(temps) if temps else 80
        temp_range = max_temp - min_temp if max_temp != min_temp else 20

        # Add some padding to the range
        min_temp -= 5
        max_temp += 5
        temp_range = max_temp - min_temp

        # Draw temperature labels
        temp_font = QFont("Arial", 10)
        for i in range(4):
            temp = max_temp - (i * temp_range / 3)
            temp_text = f"{int(temp)}°"
            self.scene.addText(temp_text, temp_font).setPos(
                10, margin_top + (i * graph_height / 3) - 10)

        # Draw bars
        for i, data in enumerate(self.hourly_data):
            temp = data.get('temperature', 70)
            hour = data.get('hour', '12:00')

            # Calculate bar position and height
            x = margin_left + (i * bar_width)
            bar_width_actual = bar_width * 0.8  # Make bars slightly narrower
            x += (bar_width - bar_width_actual) / 2  # Center the bar

            # Calculate bar height based on temperature
            temp_normalized = (temp - min_temp) / temp_range
            bar_height = temp_normalized * graph_height
            y = margin_top + graph_height - bar_height

            # Choose color based on whether it's current hour, past, or future
            if i == self.current_hour_index:
                # Current hour - bright yellow
                bar_color = QColor("yellow")
            elif i < self.current_hour_index:
                # Past hours - darker blue
                bar_color = QColor(100, 150, 200)
            else:
                # Future hours - lighter blue
                bar_color = QColor(150, 200, 255)

            # Draw the bar
            brush = QBrush(bar_color)
            pen = QPen(bar_color, 1)
            self.scene.addRect(x, y, bar_width_actual, bar_height, pen, brush)

            # Add hour labels (every 2 hours to avoid crowding)
            if i % 2 == 0:
                time_font = QFont("Arial", 9)
                self.scene.addText(hour, time_font).setPos(
                    x - 10, height - margin_bottom + 5)

    def _draw_placeholder_graph(self, width, height):
        """Draw a placeholder graph when no data is available"""
        # Draw grid lines
        pen = QPen(QColor("grey"), 1)

        # Horizontal grid lines
        self.scene.addLine(50, height - 50, width - 50,
                           height - 50, pen)  # Bottom
        self.scene.addLine(50, height - 100, width - 50,
                           height - 100, pen)  # Middle
        self.scene.addLine(50, height - 150, width -
                           50, height - 150, pen)  # Top

        # Temperature labels
        temp_font = QFont("Arial", 10)
        self.scene.addText("60°", temp_font).setPos(10, height - 60)
        self.scene.addText("65°", temp_font).setPos(10, height - 110)
        self.scene.addText("70°", temp_font).setPos(10, height - 160)

        # Time labels
        time_font = QFont("Arial", 10)
        self.scene.addText("Loading...", time_font).setPos(
            width // 2 - 30, height - 30)
