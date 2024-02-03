import sys
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QBrush, QColor, QRegion, QPainterPath, QPen
from PyQt6.QtWidgets import QApplication, QWidget

class TransparentWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Set the window flags to make it frameless
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Set the size of the window
        self.setGeometry(100, 100, 400, 200)

        # Round the corners of the window
        self.setMask(self.rounded_mask())

    def paintEvent(self, event):
        # Override the paint event to set the window background as transparent
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Set the background color with transparency (adjust the last value for transparency)
        painter.setBrush(QBrush(QColor(255, 255, 255, 100)))

        # Make the border transparent
        pen = QPen()
        pen.setColor(QColor(0, 0, 0, 0))  # Set border color with alpha value of 0 (fully transparent)
        painter.setPen(pen)

        # Draw the rounded rectangle with transparent border
        rect = self.rect().adjusted(1, 1, -1, -1)  # Adjusted to ensure the border is drawn inside the rectangle
        painter.drawRoundedRect(rect, 15.0, 15.0)

    def rounded_mask(self):
        # Create a rounded rectangle shape for the window mask
        radius = 15.0  # Adjust this value to control the roundness of the corners
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), radius, radius)
        return QRegion(path.toFillPolygon().toPolygon())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TransparentWindow()
    window.show()
    sys.exit(app.exec())
