import sys
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QBrush, QColor, QRegion, QPainterPath, QPen, QGraphicsBlurEffect
from PyQt6.QtWidgets import QApplication, QWidget, QGraphicsProxyWidget, QLabel

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

        # Add a QLabel with blur effect to simulate the blurred background
        label = QLabel(self)
        label.setGeometry(0, 0, self.width(), self.height())

        # Set up blur effect for the background
        blur = QGraphicsBlurEffect(self)
        blur.setBlurRadius(10)  # Adjust the blur radius as needed
        proxy = QGraphicsProxyWidget()
        proxy.setWidget(label)
        proxy.setGraphicsEffect(blur)

    def paintEvent(self, event):
        # Override the paint event to set the window background as transparent
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Set the background color with transparency (adjust the last value for transparency)
        painter.setBrush(QBrush(QColor(255, 255, 255, 100)))
        painter.drawRect(self.rect())

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
