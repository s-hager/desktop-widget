from PyQt6.QtWidgets import (QMainWindow, QApplication, QSizeGrip, QLabel, QWidget, 
                             QVBoxLayout, QSizePolicy)
from PyQt6.QtCore import Qt, QSize, QPoint, QTimer
from PyQt6.QtGui import QGuiApplication, QFont
from BlurWindow.blurWindow import GlobalBlur
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from datetime import datetime
import numpy as np
import pandas as pd
import yfinance as yf
import logging
import time

# own variables:
from config import *
from constants import *

class ChartWindow(QMainWindow):
  def __init__(self, stock_symbol, window_id=None):
    super(ChartWindow, self).__init__(parent=None)
    self.first_resize = True
    self.stock_symbol = stock_symbol
    self.drag_start_position = None
    self.bought_line = False
    if not window_id:
      window_id = window_id_counter
    # self.value_to_highlight = 68.82
    self.value_to_highlight = 0

    logging.info(f"Start Creating Window with id {window_id}")
    if window_id:
      self.window_id = f"window_{window_id}"
    else:
      self.window_id = f"window_{window_id}"
    # Call move with an invalid position to prevent default positioning
    # self.move(-1000, -1000)

    # Set the window's size to a fraction of the screen's size
    screen_size = QApplication.primaryScreen().size()  # Get the screen's size
    fraction_of_screen = 0.2  # Set the fraction of the screen size you want the window to occupy
    size_relative_to_screen = QSize(int(screen_size.width() * fraction_of_screen),
                                    int(screen_size.height() * fraction_of_screen))
    # self.resize(self.sizeHint().expandedTo(size_relative_to_screen))

    self.drag_resize = False
    # disable resizing

    # Load settings from config file and move window
    self.settings_position = settings.value(f"{self.window_id}_pos", type=QPoint)
    self.settings_size = settings.value(f"{self.window_id}_size", type=QSize)
    if self.settings_position.isNull() or self.settings_size.isEmpty():
      # Center the window on the screen
      self.resize(size_relative_to_screen)
      self.centerWindow() # order matters -> after resize
      settings.setValue(f"{self.window_id}_pos", QPoint(self.centered_position))
      settings.setValue(f"{self.window_id}_size", QSize(size_relative_to_screen))
      self.setFixedSize(size_relative_to_screen)
    else:
      self.resize(self.settings_size)
      self.move(self.settings_position)
      self.setFixedSize(self.settings_size)
    self.setWindowTitle(f"{self.window_id}")
    self.setWindowFlag(Qt.WindowType.WindowStaysOnBottomHint | Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)

    logging.info("Blurring Background...")
    self.blurBackground()
    logging.info("Done Blurring Background")
    # self.roundCorners() # TODO

    # Create plot
    self.graphWidget = pg.PlotWidget()
    self.graphWidget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    self.graphWidget.setBackground(pg.mkColor(0, 0, 0, 0))
    # self.graphWidget.patch.set_alpha(0)
    # self.canvas.setStyleSheet("QWidget { border: 1px solid red; }") # canvas is a widget
    
    self.plotItem = self.graphWidget.plotItem

    self.downloadStockData()

    # Get stock currency
    self.currency_symbol = self.replaceCurrencySymbols(yf.Ticker(self.stock_symbol).info["currency"])

    # Add the title bar and canvas to a vertical layout

    self.title_widget = self.titleWidget()
    self.title_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
    self.graphWidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    # Call the method to plot the stock graph on the canvas
    # is now called in main.py
    # self.plotStock()

    layout = QVBoxLayout()
    layout.addWidget(self.title_widget)
    layout.addWidget(self.graphWidget)
    if display_refresh_time:
      layout.addWidget(self.refreshTimeLabel())
    layout.setSpacing(0)
    layout.setContentsMargins(*window_margins)
    # layout.setContentsMargins(0, 0, 0, 0)

    # Create a central widget to hold the layout
    self.central_widget = QWidget()
    self.central_widget.setObjectName("central_widget")
    self.central_widget.setLayout(layout)
    self.setCentralWidget(self.central_widget)
    if debug:
      self.central_widget.setStyleSheet("border: 1px solid red;")

    self.graphWidget.installEventFilter(self)

    self.addResizeGrips()
    self.startRefreshTimer()

  # def paintEvent(self, event):
  #   rounded_rect_path = QPainterPath()
  #   rounded_rect_path.addRoundedRect(QRectF(self.rect()), 10.0, 10.0)
  #   region_ = QRegion(rounded_rect_path.toFillPolygon().toPolygon())
  #   self.setMask(region_)

  # def roundCorners(self):
  #   # Create a QPainterPath with rounded corners
  #   path = QPainterPath()
  #   rectf = QRectF(self.rect())
  #   path.addRoundedRect(rectf, 100, 100)

  #   # Create a QRegion with the QPainterPath and set it as the widget's mask
  #   region_ = QRegion(path.toFillPolygon().toPolygon())
  #   self.setMask(region_)

  # lag workaround for blurred background (makes window stutter):
  # def moveEvent(self, event) -> None:
  #   time.sleep(0.01)  # sleep for 10ms

  # def resizeEvent(self, event) -> None:
  #   time.sleep(0.01)  # sleep for 10ms

  def applyConfig(self):
    logging.info(f"Applying config to {self.window_id}")
    if settings.value(f"{self.window_id}_bought_line", type=bool):
      self.value_to_highlight = float(settings.value(f"{self.window_id}_bought_line_value"))
      self.bought_line = True

  def setBoughtLine(self, state):
    self.bought_line = state
    self.plotStock()

  def addResizeGrips(self):
    # Add resize grips
    self.gripSize = 16
    self.grips = []
    for i in range(4):
      grip = QSizeGrip(self)
      grip.resize(self.gripSize, self.gripSize)
      self.grips.append(grip)
      if debug:
        grip.setStyleSheet("background-color: red;")
      grip.setVisible(False)

  def showResizeGrips(self):
    for i, grip in enumerate(self.grips):
      grip.setVisible(True)

  def hideResizeGrips(self):
    for i, grip in enumerate(self.grips):
      grip.setVisible(False)

  # def moveEvent(self, event):
  #   # This method is called when the window is moved
  #   # logging.info(f"Move Event on window {window_id}")
  #   self.savePositionAndSize()
  #   super().moveEvent(event)

  def savePositionAndSize(self):
    settings.setValue(f"{self.window_id}_pos", self.pos())
    settings.setValue(f"{self.window_id}_size", self.size())

  def downloadStockData(self):
    # Get stock data and convert index Datetime to its own column (['Datetime', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])
    logging.info("Downloading Stock Data...")
      # self.data = yf.download(self.stock_symbol, interval="1h", period="1mo", prepost=True, progress=True) # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
    # else:
    while True:
      try:
        self.data = yf.download(self.stock_symbol, interval="1h", period="1mo", prepost=True, progress=False) # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
        self.update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.data = self.data.reset_index().rename({'index': 'Datetime'}, axis=1, copy=False)
        self.data['Datetime'] = pd.to_datetime(self.data['Datetime'])
        break
      except Exception as e:
        logging.info(f"An exception occured: {e}")
        logging.info("Retrying in 5 seconds...")
        time.sleep(1)

  def replaceCurrencySymbols(self, text):
    currency_symbols = {
        "USD": "$",
        "EUR": "€",
        "JPY": "¥",
        "GBP": "£",
    }
    for currency_code, currency_symbol in currency_symbols.items():
        text = text.replace(currency_code, currency_symbol)
    return text

  def refreshTimeLabel(self):
    self.refresh_time_label = QLabel(f"{self.update_time}") # self.update_time is set by downloadStockData()
    if debug:
      self.refresh_time_label.setStyleSheet(f"color:{legend_color}; border: 1px solid red;")
    else:
      self.refresh_time_label.setStyleSheet(f"color:{legend_color};")
    font = QFont()
    font.setPointSize(update_font_size)
    self.refresh_time_label.setFont(font)
    self.refresh_time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
    return self.refresh_time_label

  def updateRefreshTimeLabel(self):
    self.refresh_time_label.setText(self.update_time)
    logging.info(f"Updated Refresh Time to {self.update_time}")

  def titleWidget(self):
    if debug:
      title = QLabel(f"{self.stock_symbol.upper()} {self.currency_symbol}{self.data['Close'].iloc[-1]:.2f} {self.window_id}")
      title.setStyleSheet(f"color:{legend_color}; border: 1px solid red;")
    else:
      title = QLabel(f"{self.stock_symbol.upper()} {self.currency_symbol}{self.data['Close'].iloc[-1]:.2f}")
      title.setStyleSheet(f"color:{legend_color};")
    font = QFont()
    font.setPointSize(title_font_size)
    title.setFont(font)
    title.setContentsMargins(0, 0, 0, 0)
    return title

  def startRefreshTimer(self):
    # Create a QTimer object
    self.refresh_timer = QTimer(self)
    # Connect the timer's timeout signal to the plot_stock method
    self.refresh_timer.timeout.connect(lambda: logging.info("Refreshing Plot..."))
    self.refresh_timer.timeout.connect(self.downloadStockData)
    self.refresh_timer.timeout.connect(self.plotStock)
    self.refresh_timer.timeout.connect(self.updateRefreshTimeLabel)
    self.refresh_timer.timeout.connect(lambda: logging.info("Done"))
    # Start the timer with the specified refresh_interval in milliseconds
    self.refresh_timer.start(refresh_interval * 1000)

  def resizeEvent(self, event):
    # Dont plot stock on first default resize event
    if self.first_resize:
      self.first_resize = False
      return
    else:
      self.plotStock() # replot stock to adjust to new window size
      logging.info(f"Resize Event")
    # QMainWindow.resizeEvent(self, event)
    if self.drag_resize:
      self.positionGrips()

  def positionGrips(self):
    rect = self.rect()
    # top left grip doesn't need to be moved...
    # top right
    self.grips[1].move(rect.right() - self.gripSize, 0)
    # bottom right
    self.grips[2].move(
        rect.right() - self.gripSize, rect.bottom() - self.gripSize)
    # bottom left
    self.grips[3].move(0, rect.bottom() - self.gripSize)
    # time.sleep(0.01)

  def centerWindow(self):
    # Get the center position of the primary screen
    center_point = QGuiApplication.primaryScreen().availableGeometry().center()
    # Calculate the top-left position for the window
    window_geometry = self.frameGeometry()
    window_geometry.moveCenter(center_point)
    self.centered_position = window_geometry.topLeft()
    # Move the window to the center position
    self.move(self.centered_position)

  def is_mouse_inside_grip(self, pos):
    # logging.info(pos)
    for grip in self.grips:
      if grip.geometry().contains(pos):
        return True
    return False

  def mousePressEvent(self, event):
    if drag_window or self.drag_resize:
      # logging.info("press")
      self.candidate_start_position = event.globalPosition().toPoint()
      # if not self.is_mouse_inside_grip(self.candidate_start_position):
      if not self.is_mouse_inside_grip(event.pos()):
        self.drag_start_position = self.candidate_start_position
    else:
      pass

  def mouseReleaseEvent(self, event):
    if drag_window or self.drag_resize:
      # logging.info("release")
      if event.button() == 1:  # Left mouse button
        self.drag_start_position = None

  def mouseMoveEvent(self, event):
    if drag_window or self.drag_resize:
      # logging.info("move")
      if self.drag_start_position is not None and not self.is_mouse_inside_grip(self.drag_start_position):
        delta = QPoint(event.globalPosition().toPoint() - self.drag_start_position)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.drag_start_position = event.globalPosition().toPoint()

  def blurBackground(self):
    # GlobalBlur(self.winId(), Dark=True, Acrylic=True, QWidget=self)
    GlobalBlur(self.winId(), Dark=True, Acrylic=False, QWidget=self)
    # self.setStyleSheet("background-color: lightgrey")
    self.setStyleSheet("background-color: rgba(0, 0, 0, 0)")

  def format_y_tick_label(self, value, pos):
    return f"{self.currency_symbol}{value:.2f}"

  def plotStock(self):
    # Function to convert datetime string to "July 26" format
    def format_x_label(datetime_str):
      # Parse the datetime string to a datetime object
      dt_obj = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S%z")
      # Format the datetime object to "July 26" format
      formatted_date = dt_obj.strftime("%B %d")
      return formatted_date

    logging.info("Plotting Stock...")
    # stock = "AAPL"
    # data = yf.download(stock, interval="1h", period="1mo", prepost=True) # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
    # data = yf.download(stock, interval="5m", period="1wk", prepost=True) # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
    # logging.info(data.to_markdown())
    # logging.info(data)

    # logging.info(data['Datetime'])

    # So that days where no market activity took place are omitted instead of drawn as a straight line 
    # formatter = CustomFormatter(self.data['Datetime'])

    # Clear the existing plot
    self.plotItem.clear()

    # Plot the stock data
    x = np.arange(len(self.data['Datetime']))
    y = self.data['Close']
    self.plotItem.plot(x=x, y=y, pen=pg.mkPen(color=(255, 0, 0), width=1))
    
    # Customize plot appearance
    # self.plotItem.setLabel('bottom', 'Datetime')
    # self.plotItem.setLabel('left', 'Stock Price')
    # self.plotItem.getAxis('bottom').setTickSpacing(1, 0.1)  # Customize x-axis tick spacing
    # self.plotItem.getAxis('bottom').setStyle(autoExpandTextSpace=True)  # Ensure x-axis labels are visible
    
    # self.plotItem.layout.setContentsMargins(0, 0, 0, 0)

    # Refresh the graph
    self.graphWidget.update()

    logging.info("Done Plotting Stock")