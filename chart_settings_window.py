from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QCheckBox, QLineEdit, QDialog, QMessageBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSignal
import logging

# own variables:
from config import *
from constants import *

class ChartSettingsWindow(QDialog):
  close_chart_settings_signal = pyqtSignal()
  def __init__(self, window):
    super().__init__()
    self.window = window
    self.window_id = window.window_id
    self.stock_symbol = window.stock_symbol
    self.setWindowTitle(f"{self.stock_symbol} Settings")
    self.setWindowIcon(QIcon(app_icon))
    layout = QVBoxLayout()

    self.bought_line = QHBoxLayout()
    self.bought_line_value = QLineEdit(self)
    self.bought_line_value.setPlaceholderText("Bought Line Value e.g. 56.78")
    self.bought_line_checkbox = QCheckBox("Show \"Bought\" Line")
    self.bought_line_checkbox.clicked.connect(self.toggleBoughtLine)
    self.bought_line.addWidget(self.bought_line_value)
    self.bought_line.addWidget(self.bought_line_checkbox)
    # display current values if bought line is activated
    if self.window.bought_line:
      self.bought_line_checkbox.setChecked(True)
      self.bought_line_value.setText(f"{self.window.value_to_highlight}")
    layout.addLayout(self.bought_line)

    self.placeholder = QHBoxLayout()
    self.placeholder_value = QLineEdit(self)
    self.placeholder_value.setPlaceholderText("Placeholder")
    self.placeholder_checkbox = QCheckBox("Placeholder")
    self.placeholder.addWidget(self.placeholder_value)
    self.placeholder.addWidget(self.placeholder_checkbox)
    layout.addLayout(self.placeholder)

    self.setLayout(layout)

  def toggleBoughtLine(self, state):
    if state: # if checkbox was set to checked
      bought_line_value = self.bought_line_value.text().strip()
      if not bought_line_value:
        QMessageBox.critical(self, "Error", "Bought Line Value cannot be empty.")
        self.bought_line_checkbox.setChecked(False)
        return
      else:
        try:
          bought_line_value = float(bought_line_value)
        except ValueError:
          QMessageBox.critical(self, "Error", "Bought Line Value has to be floating point number.")
          self.bought_line_checkbox.setChecked(False)
          self.bought_line_value.clear()
          return
        logging.info(f"Enable bought line at {bought_line_value} for {self.window_id}")
        self.window.value_to_highlight = bought_line_value
        settings.setValue(f"{self.window_id}_bought_line_value", bought_line_value)
    else:
      logging.info(f"Disable bought line for {self.window_id}")
      settings.remove(f"{self.window_id}_bought_line_value")
    settings.setValue(f"{self.window_id}_bought_line", state)
    self.window.setBoughtLine(state)

  def closeEvent(self, event):
    self.destroy()
    # event.ignore() # ignore close event (would cause program to exit)
    logging.info(f"Closed Chart Settings Window for {self.window_id}")
    self.close_chart_settings_signal.emit()  # Emit custom signal