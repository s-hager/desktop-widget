from PyQt6.QtWidgets import QMainWindow, QVBoxLayout
from PyQt6.QtGui import QIcon

# own variables:
from constants import *

class ChartSettingsWindow(QMainWindow):
  def __init__(self, window, parent=None):
    super().__init__(parent)
    self.window = window
    self.window_id = window.window_id
    self.stock_symbol = window.stock_symbol
    self.setWindowTitle(f"{self.stock_symbol}")
    self.setWindowIcon(QIcon(app_icon))
    self.window_layout = QVBoxLayout()