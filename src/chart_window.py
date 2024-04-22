from PyQt6.QtWidgets import (QMainWindow, QApplication, QSizeGrip, QLabel, QWidget, 
                             QVBoxLayout, QSizePolicy)
from PyQt6.QtCore import Qt, QSize, QPoint, QTimer
from PyQt6.QtGui import QGuiApplication, QFont
from BlurWindow.blurWindow import GlobalBlur
# import matplotlib.pyplot as plt
# import matplotlib.ticker as ticker
# from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.ticker import Formatter, FixedLocator
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import yfinance as yf
import logging
import time
import calendar
import sys

import dev_sandbox.MyQLabel as MyQLabel #TODO WIP

# own variables:
from config import *
from constants import *

# https://stackoverflow.com/questions/54277905/how-to-disable-date-interpolation-in-matplotlib
# class CustomFormatter(Formatter):
#   def __init__(self, dates, format='%Y-%m-%d %H:%M:%S-%H:%M'):
#     self.dates = dates
#     self.format = format

#   def __call__(self, x, pos=0):
#     'Return the label for time x at position pos'
#     index = int(np.round(x))
#     if index >= len(self.dates) or index < 0:
#       return ''
#     return self.dates[index].strftime(self.format)

class CrosshairPlotWidget(pg.PlotWidget):
  def __init__(self, crosshair, parent=None, background='default', plotItem=None, **kargs):
    super().__init__(parent=parent, background=background, plotItem=plotItem, **kargs)
    self.crosshair = crosshair
    self.vLine = None
    self.hLine = None
    # self.vLine.show()
    # self.hLine.show()
  
  def leaveEvent(self, event):
    if self.crosshair:
      self.vLine.hide()
      self.hLine.hide()

  def enterEvent(self, event):
    if self.crosshair:
      self.vLine.show()
      self.hLine.show()

  def mouseMoveEvent(self, event):
    if self.crosshair:
      vb = self.plotItem.vb
      pos = event.position()
      if self.sceneBoundingRect().contains(pos):
        mousePoint = vb.mapSceneToView(pos)
        self.vLine.setPos(mousePoint.x())
        self.hLine.setPos(mousePoint.y())

  def toggleCrosshair(self):
    self.crosshair = not self.crosshair

class ChartWindow(QMainWindow):
  def __init__(self, tray_icon, stock_symbol, window_id):
    super(ChartWindow, self).__init__(parent=None)
    self.tray_icon = tray_icon
    self.first_resize = True
    self.stock_symbol = stock_symbol
    self.drag_start_position = None
    self.bought_line = False
    self.initial_crosshair = True
    # self.value_to_highlight = 68.82
    self.value_to_highlight = 0
    logging.info(f"Start Creating Window with id {window_id}")
    self.window_id = f"window_{window_id}"
    # if window_id:
    #   self.window_id = f"window_{window_id}"
    # else:
    #   self.window_id = f"window_{window_id}"
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

    # Create a central widget to hold the layout
    self.central_widget = QWidget()
    self.central_widget.setObjectName("central_widget")
    self.setCentralWidget(self.central_widget)

    self.blurBackground()
    # self.roundCorners() # TODO

    # Create plot
    self.plotWidget = CrosshairPlotWidget(self.initial_crosshair)
    # self.graphWidget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    self.plotWidget.setBackground(pg.mkColor(chart_background_color))
    self.plotWidget.setMouseEnabled(x=False, y=False)
    self.plotWidget.setMenuEnabled(False)
    self.plotWidget.hideButtons()
    
    # https://stackoverflow.com/questions/38795508/autoranging-plotwidget-without-padding-pyqtgraph
    # https://stackoverflow.com/a/65545219
    # pg.ViewBox.suggestPadding = lambda *_: 0.0

    self.view_box = pg.ViewBox()
    # print(self.view_box.suggestPadding(self))
    # self.view_box.setDefaultPadding(0.0)
    # print(self.view_box.suggestPadding(self))
    # self.view_box.autoRange(padding=0)
    # self.view_box.enableAutoRange()
    # self.canvas.setStyleSheet("QWidget { border: 1px solid red; }") # canvas is a widget
    
    self.plotItem = self.plotWidget.plotItem

    # # Create a Figure and Canvas for Matplotlib plot
    # if debug:
    #   self.figure = plt.figure(facecolor='blue')
    # else:
    #   self.figure = plt.figure()
    # # self.figure.tight_layout(pad=0.1)
    # self.canvas = FigureCanvas(self.figure)
    # self.canvas.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    # self.figure.patch.set_alpha(0)
    # # self.canvas.setStyleSheet("QWidget { border: 1px solid red; }") # canvas is a widget
    
    self.downloadStockData()

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
    if sys.platform.startswith('darwin'):
      self.setWindowFlag(Qt.WindowType.WindowStaysOnBottomHint | Qt.WindowType.FramelessWindowHint)
    else:
      self.setWindowFlag(Qt.WindowType.WindowStaysOnBottomHint | Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)

    # Add the title bar and canvas to a vertical layout

    self.title_widget = self.titleWidget()
    self.title_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
    # self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    self.plotWidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    # Call the method to plot the stock graph on the canvas
    # self.plotStock()

    layout = QVBoxLayout()
    self.plotWidget.setStyleSheet(f"background-color: rgba(0, 0, 0, 0);")
    layout.addWidget(self.title_widget)
    # layout.addWidget(self.canvas)
    layout.addWidget(self.plotWidget)
    if display_refresh_time:
      layout.addWidget(self.refreshTimeLabel())
    layout.setSpacing(0)
    layout.setContentsMargins(*window_margins)
    # layout.setContentsMargins(0, 0, 0, 0)

    self.central_widget.setLayout(layout)
    if debug:
      self.central_widget.setStyleSheet("border: 1px solid red;")

    # self.canvas.installEventFilter(self)
    self.plotWidget.installEventFilter(self)

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

  def toggleCrosshair(self):
    self.plotWidget.toggleCrosshair()
    if self.plotWidget.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents):
      self.plotWidget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
    else:
      self.plotWidget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

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
    logging.info(f"Downloading Stock Data for {self.stock_symbol}...")
      # self.data = yf.download(self.stock_symbol, interval="1h", period="1mo", prepost=True, progress=True) # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
    # else:
    try_counter = 0
    while try_counter < retries:
      try:
        self.data = yf.download(self.stock_symbol, interval="1h", period="1mo", prepost=True, progress=False) # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
        self.update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.data = self.data.reset_index().rename({'index': 'Datetime'}, axis=1, copy=False)
        self.data['Datetime'] = pd.to_datetime(self.data['Datetime'])
        # Get stock currency
        self.currency_symbol = self.replaceCurrencySymbols(yf.Ticker(self.stock_symbol).info["currency"])
        # self.currency_symbol = yf.Ticker(self.stock_symbol).info["currency"]
        if percentage_change:
          last_close_date = self.data['Datetime'].iloc[-1].strftime("%Y-%m-%d")
          previous_close_date = datetime.strptime(last_close_date, "%Y-%m-%d")
          previous_close_date = (previous_close_date - timedelta(days=1)).strftime("%Y-%m-%d")
          # print(last_close_date)
          # print(previous_close_date)
          last_close_data = self.data[self.data['Datetime'].dt.strftime("%Y-%m-%d") == last_close_date]
          previous_close_data = self.data[self.data['Datetime'].dt.strftime("%Y-%m-%d") == previous_close_date]
          # print(last_close_data)
          # print(previous_close_data)
          last_close_last_nonzero_index = last_close_data[last_close_data['Volume'] != 0].index[-1]
          previous_close_last_nonzero_index = previous_close_data[previous_close_data['Volume'] != 0].index[-1]
          try:
            last_close_value = last_close_data.loc[last_close_last_nonzero_index + 1, 'Open']
          except Exception as e:
            last_close_value = last_close_data.loc[last_close_last_nonzero_index, 'Open']
          try:
            previous_close_value = previous_close_data.loc[previous_close_last_nonzero_index + 1, 'Open']
          except Exception as e:
            previous_close_value = previous_close_data.loc[previous_close_last_nonzero_index, 'Open']
          #last_close_data = last_close_data[self.data['Volume'] != 0] # manually exclude pre and post market data (where volume == 0)
          #previous_close_data = previous_close_data[self.data['Volume'] != 0] # manually exclude pre and post market data (where volume == 0)
          # print(last_close_data)
          # last_close_value = round(last_close_open_value_after_last_nonzero, 2)
          # last_close_value = last_close_open_value_after_last_nonzero
          # previous_close_value = round(previous_close_open_value_after_last_nonzero, 2)
          # previous_close_value = previous_close_open_value_after_last_nonzero

          logging.info(f"{self.stock_symbol} Open:  {self.currency_symbol}{last_close_value}")
          logging.info(f"{self.stock_symbol} Close: {self.currency_symbol}{previous_close_value}")
          # print(last_close_value)
          # print(previous_close_value)
          self.percentage_increase = ((last_close_value - previous_close_value) / previous_close_value) * 100
          self.increase_symbol = '+' if self.percentage_increase >= 0 else ''
          logging.info(f"{self.stock_symbol} Increase: {self.increase_symbol}{self.percentage_increase:.2f}%")

          self.close_price = last_close_value
          # print(f"{self.percentage_increase:.2f}%")
          # print(self.percentage_increase)

        self.current_price = self.data['Close'].iloc[-1]
        # print(type(self.data['Datetime']))
        # print(self.data['Datetime'])
        break
      except Exception as e:
        logging.info(f"An exception occurred: {str(e)}")
        logging.info(f"Download Attempt {try_counter + 1} failed.")
        logging.info("Retrying in 0.5 seconds...")
        time.sleep(0.5)
      try_counter += 1
    if try_counter == retries:
      # self.setWindowIcon(QIcon(app_icon))
      # QMessageBox.critical(self, "Error", "Could not download stock data after 5 tries.")
      error = f"Could not download stock data for {self.stock_symbol} after {retries} tries."
      raise RuntimeError(error)

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
      self.refresh_time_label.setStyleSheet(f"background-color: rgba(0, 0, 0, 0); color:{legend_color}; border: 1px solid red;")
    else:
      self.refresh_time_label.setStyleSheet(f"background-color: rgba(0, 0, 0, 0); color:{legend_color};")
    font = QFont()
    font.setPointSize(update_font_size)
    self.refresh_time_label.setFont(font)
    self.refresh_time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
    return self.refresh_time_label

  def updateRefreshTimeLabel(self):
    self.refresh_time_label.setText(self.update_time)
    logging.info(f"Updated Refresh Time to {self.update_time}")

  def titleWidget(self):
    if percentage_change and self.percentage_increase >= 0:
      text_color = chart_line_color_positive
    elif percentage_change:
      text_color = chart_line_color_negative
    if debug:
      if percentage_change:
        text = f"""<font size='3'>{self.stock_symbol.upper()}</font>
                   <font size='1.5'>{self.currency_symbol}{self.close_price:.2f}</font>
                   <font size='1.5' color='{text_color}'>{self.increase_symbol}{self.percentage_increase:.2f}% {self.window_id}</font>
                   <font size='1.5'>{self.currency_symbol}{self.current_price:.2f}</font>"""
        stylesheet = f"background-color: rgba(0, 0, 0, 0); color:{legend_color}; border: 1px solid red;"
      else:
        text = f"""<font size='3'>{self.stock_symbol.upper()}</font>
                   <font size='1.5'>{self.currency_symbol}{self.current_price:.2f}</font>"""
        stylesheet = f"background-color: rgba(0, 0, 0, 0); color:{legend_color}; border: 1px solid red;"
    else:
      if percentage_change:
        #title = MyQLabel(f"{self.stock_symbol.upper()} {self.currency_symbol}{self.data['Close'].iloc[-1]:.2f}")
        text = f"""<font size='3'>{self.stock_symbol.upper()}</font>
                   <font size='1.5'>{self.currency_symbol}{self.close_price:.2f}</font>
                   <font size='1.5' color='{text_color}'>{self.increase_symbol}{self.percentage_increase:.2f}%</font>
                   <font size='1.5'>{self.currency_symbol}{self.current_price:.2f}</font>"""
        stylesheet = f"background-color: rgba(0, 0, 0, 0); color:{legend_color};"
      else:
        text = f"""<font size='3'>{self.stock_symbol.upper()}</font>
                   <font size='1.5'>{self.currency_symbol}{self.current_price:.2f}</font>"""
        stylesheet = f"background-color: rgba(0, 0, 0, 0); color:{legend_color};"
    title = QLabel()
    title.setStyleSheet(stylesheet)
    title.setText(text)
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
    self.refresh_timer.timeout.connect(lambda: logging.info("Done Refreshing Plot"))
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
    logging.info("Blurring Background...")
    #GlobalBlur(self.winId(), Dark=True, Acrylic=True, QWidget=self)
    GlobalBlur(self.winId(), Dark=True, Acrylic=False, QWidget=self)
    # self.setStyleSheet("background-color: lightgrey")
    self.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
    self.central_widget.setStyleSheet(f"background-color: rgba{background_color};")
    logging.info("Done Blurring Background")

  def format_y_tick_label(self, value, pos):
    return f"{self.currency_symbol}{value:.2f}"

  def plotStock(self):
    # Function to convert datetime string to "July 26" format
    # def format_x_label(datetime_str):
    #   # Parse the datetime string to a datetime object
    #   dt_obj = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S%z")
    #   # Format the datetime object to "July 26" format
    #   formatted_date = dt_obj.strftime("%B %d")
    #   return formatted_date

    logging.info("Plotting Stock...")
    
    # Clear the existing plot
    self.plotItem.clear()

    # add crosshair
    self.plotWidget.vLine = pg.InfiniteLine(angle=90, movable=False)
    self.plotWidget.hLine = pg.InfiniteLine(angle=0, movable=False)
    self.plotWidget.addItem(self.plotWidget.vLine, ignoreBounds=True)
    self.plotWidget.addItem(self.plotWidget.hLine, ignoreBounds=True)

    # print(np.arange(len(self.data['Datetime'])))
    # Plot the stock data
    x = np.arange(len(self.data['Datetime']))
    y = self.data['Close']
    # print(self.data['Datetime'])
    # x = self.data['Datetime']
    # pd.set_option('display.max_rows', None)
    # pd.set_option('display.max_columns', None)
    # print(self.data['Datetime'])
    # x = self.data['Datetime']
    # x = [x.timestamp() for x in x]
    # print(x)
    # print(self.data['Datetime'][0])
    # print(type(self.data['Datetime'][0]))
    
    def find_open_dates():
      # # https://www.swingtradesystems.com/trading-days-calendars.html
      open_dates = []
      for index, timestamp in enumerate(self.data['Datetime']):
        # if date n + 1 - 1 day is not equal to date n
        # if self.data['Datetime'][index + 1] is not None and timestamp.day != self.data['Datetime'][index + 1].day - 1: #and timestamp.month == self.data['Datetime'][index + 1].month:
        try:
          if timestamp.day != self.data['Datetime'][index + 1].day: #and timestamp.month == self.data['Datetime'][index + 1].month:
            # print("x")
            # print(timestamp.day)
            # print(self.data['Datetime'][index + 1].day)
          # if timestamp.day != self.data['Datetime'][index + 1].day: #and timestamp.month == self.data['Datetime'][index + 1].month:
            # stock market closed detected
            # print(timestamp.day, self.data['Datetime'][index + 1].day - 1)
            # print(timestamp.day, self.data['Datetime'][index + 1].day)
            # print(self.data['Datetime'][index])
            open_dates.append((timestamp.day, timestamp.month, timestamp.year, index))
        except KeyError:
          open_dates.append((timestamp.day, timestamp.month, timestamp.year, index))
          # print(timestamp.day)
          # print(self.data['Datetime'][index])
          break
      # print(dates)
      open_dates_series = pd.Series(open_dates)
      open_dates = open_dates_series.unique()
      # print(open_dates)
      return open_dates

    def find_first_day_after_gap(dates_list):
      result_days = []
      indices = []
      length = len(dates_list)
      for index, date in enumerate(dates_list):
        _, days_in_month = calendar.monthrange(date[2], date[1])
        if index + 1 <= length - 1:  # if index + 1 is still valid list index
          if date[0] == days_in_month and dates_list[index + 1][0] == 1:
            continue
          elif date[0] != dates_list[index + 1][0] - 1:  # if date day n does not equal date day n+1 - 1
            first_day_after_gap_date = dates_list[index + 1][0:3]
            first_day_after_gap_index = dates_list[index + 1][3]
            result_days.append(first_day_after_gap_date)
            indices.append(first_day_after_gap_index)
      # print(days)
      return result_days, indices

    # Create custom ticks and labels for x axis
    open_dates = find_open_dates()
    days, indices = find_first_day_after_gap(open_dates)
    # print(days, indices)
    # custom_x_labels = days
    # custom_x_labels = [f'{t[0]}.{t[1]}.{t[2]}' for t in days]
    
    # if display_first_date_as_tick:
    #   oldest_data = self.data['Datetime'][0]
    #   oldest_day = (oldest_data.day, oldest_data.month, oldest_data.year)
    #   days.insert(0, oldest_day)
    #   indices.insert(0, 0)
    #   print(days) # oldest day not showing????
    #   print(indices) # oldest day not showing????

    x_labels = [f'{date[0]}.{date[1]}.' for date in days]
    x_ticks = indices

    self.plotWidget.getAxis('bottom').setTicks([[(val, label) for val, label in zip(x_ticks, x_labels)]])

    # Create a DateAxisItem for the x-axis
    # axis = pg.DateAxisItem()
    # self.plotItem.setAxisItems({'bottom':axis})

    # Customize plot appearance
    self.plotWidget.showGrid(x=True, y=True)
    self.plotWidget.getAxis('left').setGrid(False)
    self.plotWidget.getAxis('bottom').setGrid(False)

    self.plotWidget.getAxis('left').setTextPen(legend_color)
    self.plotWidget.getAxis('bottom').setTextPen(legend_color)

    self.plotWidget.getAxis('left').setPen(legend_color)
    self.plotWidget.getAxis('bottom').setPen(legend_color)
    self.plotWidget.getAxis('right').setPen(legend_color)
    self.plotWidget.getAxis('top').setPen(legend_color)

    max_x_value = len(self.data['Close']) - 1
    self.plotWidget.setXRange(0, max_x_value, padding=0)
    # self.plotWidget.setXRange(0, max_x_value, padding=0.005)
    # self.plotWidget.setXRange(0, max_x_value)

    # check if oldest close value is smaller or bigger than newest close value
    positive_chart = None
    if self.data['Close'].iloc[-1] < self.data['Close'].iloc[0]: # compare last and first values and color chart accordingly 
      positive_chart = True
    else:
      positive_chart = False

    # Conditional Line Color
    if positive_chart:
        chart_line_color = chart_line_color_negative
        chart_area_color = chart_area_color_negative_trans
    else:
        chart_line_color = chart_line_color_positive
        chart_area_color = chart_area_color_positive_trans

    # Fill the area below the stock price line with a color
    if area_chart:
      # TODO: the y "limits" are not being set correctly
      self.plotItem.plot(x=x, y=y, pen=pg.mkPen(color=chart_line_color, width=1), fillLevel=0, brush=chart_area_color)
      self.plotWidget.setYRange(min(self.data['Close']), max(self.data['Close']))
      # self.plotItem.plot(x=x, y=y, pen=pg.mkPen(color=chart_line_color, width=1))
    else:
      self.plotItem.plot(x=x, y=y, pen=pg.mkPen(color=chart_line_color, width=1))

    # https://stackoverflow.com/questions/69816567/pyqtgraph-cuts-off-tick-labels-if-showgrid-is-called
    for key in ['right', 'top']:
      self.plotWidget.showAxis(key)                            # Show top/right axis (and grid, since enabled here)
      self.plotWidget.getAxis(key).setStyle(showValues=False)  # Hide tick labels on top/right

    # self.plotWidget.hLine = pg.InfiniteLine(angle=0, movable=False)
    # self.plotWidget.addItem(self.plotWidget.vLine, ignoreBounds=True)

    if self.bought_line:
      # if line would not be visible (value too small or large) display it at bottom or top of visible plot
      y_min = self.plotWidget.getViewBox().getState()['viewRange'][1][0]
      y_max = self.plotWidget.getViewBox().getState()['viewRange'][1][1]
      bought_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen((255, 255, 0, 255), width=1.5))
      dot = pg.ScatterPlotItem(symbol='o', size=10, pen=pg.mkPen(None), brush=pg.mkBrush((255, 255, 0, 255)))
      self.plotWidget.addItem(bought_line, ignoreBounds=True)
      self.plotWidget.addItem(dot, ignoreBounds=True)
      if self.value_to_highlight < y_min:
        # "below" line
        # offset because line is being drawn just below value and would be outside of plot otherwise (not appear)
        # offset = 0.01 * (y_max - y_min)
        # ax.axhline(y=y_min + offset, color='yellow', linewidth=1)
        # ax.scatter(0, y_min + offset, color='yellow', s=25, marker='o')  # 0 is the x-coordinate for the dot
        # line_width_offset tries to only offset 1 pixel (the bought lines' width, wheras offset takes 1% of entire data)
        # line_width_offset = 1 / (ax.transData.transform([0, 1])[1] - ax.transData.transform([0, 0])[1])
        # ax.axhline(y=y_min + line_width_offset, color='yellow', linewidth=1)
        # self.plotWidget.addItem(pg.InfiniteLine(angle=0, movable=False), ignoreBounds=True)
        # ax.scatter(0, y_min + line_width_offset, color='yellow', s=25, marker='o')  # 0 is the x-coordinate for the dot
        window_height_correction = 1 / self.height()
        offset = window_height_correction + 0.001 * (y_max - y_min)
        # print("0.003___" + str(window_height_correction))
        # print("0.004___" + str( window_height_correction + 0.001))
        # print(offset)
        bought_line.setPos(y_min + offset)
        dot.setData(pos=[(0, y_min + offset)])
      elif self.value_to_highlight > y_max:
        # "above" line
        offset = 0.007 * (y_max - y_min)
        bought_line.setPos(y_max - offset)
        # bought_line.setPos(y_max)
        dot.setData(pos=[(0, y_max - offset)])
        # dot.setData(pos=[(0, y_max)])
        # bought_line.setPos(self.value_to_highlight)
        # ax.axhline(y=y_max, color='yellow', linewidth=1)
        # ax.scatter(0, y_max, color='yellow', s=25, marker='o')  # 0 is the x-coordinate for the dot
      else:
        # "normal" line
        bought_line.setPos(self.value_to_highlight)
        dot.setData(pos=[(0, self.value_to_highlight)])
      #   ax.axhline(y=self.value_to_highlight, color='yellow', linewidth=1)
      #   ax.scatter(0, self.value_to_highlight, color='yellow', s=25, marker='o')  # 0 is the x-coordinate for the dot

    # Refresh the graph
    self.plotWidget.update()

    # stock = "AAPL"
    # data = yf.download(stock, interval="1h", period="1mo", prepost=True) # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
    # data = yf.download(stock, interval="5m", period="1wk", prepost=True) # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
    # logging.info(data.to_markdown())
    # logging.info(data)

    # logging.info(data['Datetime'])

    # So that days where no market activity took place are omitted instead of drawn as a straight line 
    # formatter = CustomFormatter(self.data['Datetime'])

    # # Clear the existing plot
    # self.figure.clear()

    # # Create a subplot and plot the stock data
    # ax = self.figure.add_subplot(111)
    # ax.xaxis.set_major_formatter(formatter)
    # ax.yaxis.set_major_formatter(ticker.FuncFormatter(self.format_y_tick_label))
    # if self.data['Close'].iloc[-1] < self.data['Close'].iloc[0]: # compare last and first values and color chart accordingly 
    #   self.data['Close'].plot(ax=ax, color=chart_line_color_negative)
    # else:
    #   self.data['Close'].plot(ax=ax, color=chart_line_color_positive)
    # self.figure.set_tight_layout({'pad': 0.1}) # TODO 0.1 otherwise right border is not visible

    # # Fill the area below the stock price line with a color
    # if area_chart:
    #   if self.data['Close'].iloc[-1] < self.data['Close'].iloc[0]: # compare last and first values and color chart accordingly 
    #     ax.fill_between(self.data.index, self.data['Close'], color=chart_area_color_negative, alpha=0.3, zorder=-1)
    #   else:
    #     ax.fill_between(self.data.index, self.data['Close'], color=chart_area_color_positive, alpha=0.3, zorder=-1)

    # # Customize the plot
    # # ax.set_xlabel('Date', color='white', fontsize=10)
    # # ax.set_ylabel('Stock Price (USD)', color='white', fontsize=10)
    # # ax.set_title(f'{stock.upper()} Stock Price Chart', color=legend_color, fontsize=10)
    # # if debug:
    # #   ax.set_facecolor('yellow')
    # # else:
    # ax.set_facecolor('none')

    # ax.tick_params(which='minor', size=0)
    # ax.tick_params(color=legend_color, labelcolor=legend_color)
    # ax.tick_params(left = False, bottom = False)
    # ax.tick_params(axis='x', which='major', labelsize=8, pad=0)
    # ax.tick_params(axis='y', which='major', labelsize=8, pad=0)
    # # Remove left and right margins
    # ax.margins(x=0)
    # # Remove graph frame (borders)
    # # ax.spines['top'].set_visible(False)
    # # ax.spines['right'].set_visible(False)
    # # ax.spines['bottom'].set_visible(False)
    # # ax.spines['left'].set_visible(False)
    # # ax.spines['top'].set_color(legend_color)
    # # ax.spines['right'].set_color(legend_color)
    # # ax.spines['bottom'].set_color(legend_color)
    # # ax.spines['left'].set_color(legend_color)
    # # ax.spines['top'].set_alpha(0.5)
    # # ax.spines['right'].set_alpha(0.5)
    # # ax.spines['bottom'].set_alpha(0.5)
    # # ax.spines['left'].set_alpha(0.5)
    # # Set the color of spines (borders) to white and change their transparency
    # for spine in ax.spines.values():
    #   spine.set_color(legend_color)
    #   spine.set_alpha(0.5)

    # # ax.autoscale()
    # # self.figure.set_size_inches(4.8, 2)

    # # Set y-axis limits to avoid the area graph from being pushed up
    # ymin = self.data['Close'].min()
    # ymax = self.data['Close'].max()
    # padding = padding_multiplier * (ymax - ymin)
    # ax.set_ylim(ymin - padding, ymax + padding)

    # if self.bought_line:
    #   # if line would not be visible (value too small or large) display it at bottom or top of visible plot
    #   y_min, y_max = ax.get_ylim()
    #   if self.value_to_highlight < y_min:
    #     # offset because line is being drawn just below value and would be outside of plot otherwise (not appear)
    #     # offset = 0.01 * (y_max - y_min)
    #     # ax.axhline(y=y_min + offset, color='yellow', linewidth=1)
    #     # ax.scatter(0, y_min + offset, color='yellow', s=25, marker='o')  # 0 is the x-coordinate for the dot
    #     # line_width_offset tries to only offset 1 pixel (the bought lines' width, wheras offset takes 1% of entire data)
    #     line_width_offset = 1 / (ax.transData.transform([0, 1])[1] - ax.transData.transform([0, 0])[1])
    #     ax.axhline(y=y_min + line_width_offset, color='yellow', linewidth=1)
    #     ax.scatter(0, y_min + line_width_offset, color='yellow', s=25, marker='o')  # 0 is the x-coordinate for the dot
    #   elif self.value_to_highlight > y_max:
    #     ax.axhline(y=y_max, color='yellow', linewidth=1)
    #     ax.scatter(0, y_max, color='yellow', s=25, marker='o')  # 0 is the x-coordinate for the dot
    #   else:
    #     ax.axhline(y=self.value_to_highlight, color='yellow', linewidth=1)
    #     ax.scatter(0, self.value_to_highlight, color='yellow', s=25, marker='o')  # 0 is the x-coordinate for the dot

    # if monday_lines:
    #   formatted_dates = [format_x_label(str(label)) for label in self.data['Datetime'][::y_label_every_x_datapoints]]
    #   # Loop through the formatted dates and draw vertical lines at the beginning of each Monday
    #   prev_week = None
    #   for i, formatted_date in enumerate(formatted_dates):
    #     date_obj = datetime.strptime(formatted_date, "%B %d")
    #     if prev_week is not None and prev_week != date_obj.isocalendar()[1]:
    #         # Draw a vertical line at position i
    #         ax.axvline(i * y_label_every_x_datapoints, color=monday_lines_color, alpha=monday_lines_transparency, linestyle=monday_lines_style, linewidth=monday_lines_width)
    #     prev_week = date_obj.isocalendar()[1]

    # if horizontal_lines:
    #   # Add horizontal lines at every y-tick position
    #   y_ticks_positions = ax.get_yticks()
    #   for y_tick_position in y_ticks_positions:
    #     ax.axhline(y_tick_position, color=horizontal_lines_color, alpha=horizontal_lines_transparency, linestyle=horizontal_lines_style, linewidth=horizontal_lines_width)

    # x_labels = range(len(self.data['Datetime']))
    # ax.set_xticks(x_labels[::y_label_every_x_datapoints], [format_x_label(str(label)) for label in self.data['Datetime'][::y_label_every_x_datapoints]], ha='center', color=legend_color)
    # ax.xaxis.set_minor_locator(FixedLocator(x_labels))
    # # plt.gca().xaxis.set_minor_formatter(FuncFormatter(lambda x, pos: ""))
    # # plt.xticks(rotation=45, color='white') # Rotate the x-axis labels for better readability
    # ax.yaxis.set_tick_params(color=legend_color)  # Set y tick labels text color to white

    # # plt.tight_layout(pad=0.1) # TODO 0.1 otherwise right border is not visible
    # # plt.autoscale(axis='x')
    # # Refresh the canvas to update the plot
    # self.canvas.draw()
    logging.info("Done Plotting Stock")