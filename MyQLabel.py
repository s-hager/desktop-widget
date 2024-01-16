from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPainter, QPainterPath, QPen, QColor, QFont

class MyQLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
    
    def paintEvent(self, event):
        # call base class paintEvent
        super().paintEvent(event)

        painter = QPainter(self)
        path = QPainterPath()

        pen = QPen()
        pen.setWidth(1)
        pen.setColor(QColor(255, 255, 255, 255))

        font = QFont("Arial", 20, 1, False)

        painter.setFont(font)
        painter.setPen(pen)

        path.addText(50, 132, font, "Hello World")

        painter.drawPath(path)