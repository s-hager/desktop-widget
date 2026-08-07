from PyQt6.QtWidgets import (QMainWindow, QApplication, QSizeGrip, QLabel, QWidget, 
                             QVBoxLayout, QHBoxLayout, QGridLayout, QSizePolicy, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QSize, QPoint, QTimer, pyqtSignal, QRectF, QThread, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QGuiApplication, QFont, QPainterPath, QRegion
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
import ctypes
import platform

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
class IndexTimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datetimes = None
        
    def set_datetimes(self, datetimes):
        self.datetimes = datetimes
        self.picture = None
        self.update()
        
    def tickValues(self, minVal, maxVal, size):
        num_labels = 5
        spacing = max(1.0, round((maxVal - minVal) / max(1, (num_labels - 1))))
        
        start = int((minVal + spacing - 1) // spacing) * spacing
        values = []
        val = start
        while val <= maxVal:
            values.append(val)
            val += spacing
            
        return [(spacing, values)]

    def tickStrings(self, values, scale, spacing):
        if self.datetimes is None or len(self.datetimes) == 0:
            return [''] * len(values)
        
        strings = []
        for v in values:
            index = int(round(v))
            if 0 <= index < len(self.datetimes):
                dt = self.datetimes.iloc[index]
                if hasattr(dt, 'strftime'):
                    day = dt.day
                    month = dt.strftime("%b")
                    strings.append(f"{day}. {month}")
                else:
                    strings.append(str(dt))
            else:
                strings.append('')
        return strings

class MajorTickAxisItem(pg.AxisItem):
    """Custom AxisItem that strips out minor ticks to prevent minor gridlines."""
    def tickValues(self, minVal, maxVal, size):
        ticks = super().tickValues(minVal, maxVal, size)
        if ticks:
            return [ticks[0]]
        return ticks

class CrosshairPlotWidget(pg.PlotWidget):
  mouseMovedSignal = pyqtSignal(float)

  def __init__(self, crosshair, parent=None, background='default', plotItem=None, **kargs):
    super().__init__(parent=parent, background=background, plotItem=plotItem, **kargs)
    self.crosshair = crosshair
    self.vLine = None
    self.hLine = None
    self.textItem = None
  
  def leaveEvent(self, event):
    if self.crosshair:
      if self.vLine: self.vLine.hide()
      if self.hLine: self.hLine.hide()
      if self.textItem: self.textItem.hide()

  def enterEvent(self, event):
    if self.crosshair:
      if self.vLine: self.vLine.show()
      if self.hLine: self.hLine.show()
      if self.textItem: self.textItem.show()

  def mouseMoveEvent(self, event):
    if self.crosshair:
      vb = self.plotItem.vb
      pos = event.position()
      if self.sceneBoundingRect().contains(pos):
        mousePoint = vb.mapSceneToView(pos)
        self.mouseMovedSignal.emit(mousePoint.x())

  def toggleCrosshair(self):
    self.crosshair = not self.crosshair

class DownloadWorker(QThread):
  finished_download = pyqtSignal(dict)

  def __init__(self, stock_symbol, parent=None):
    super().__init__(parent)
    self.stock_symbol = stock_symbol

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

  def run(self):
    logging.info(f"Downloading Stock Data for {self.stock_symbol}...")
    try_counter = 0
    while try_counter < retries:
      try:
        data = yf.download(self.stock_symbol,
                           interval="1h",
                           period="1mo",
                           prepost=True,
                           progress=False,
                           auto_adjust=True)
        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = data.reset_index().rename({'index': 'Datetime'}, axis=1, copy=False)
        data['Datetime'] = pd.to_datetime(data['Datetime'])
        
        ticker_info = yf.Ticker(self.stock_symbol).info
        currency_symbol = self.replaceCurrencySymbols(ticker_info.get("currency", "$"))
        
        percentage_increase = 0.0
        increase_symbol = ""
        close_price = 0.0
        current_price = ticker_info.get("regularMarketPrice", 0.0)
        post_market_price = ticker_info.get("postMarketPrice", None)
        post_market_percentage_increase = ticker_info.get("postMarketChangePercent", 0.0)
        post_market_increase_symbol = '+' if post_market_percentage_increase is not None and post_market_percentage_increase >= 0 else ''
        
        market_state = ticker_info.get("marketState", "UNKNOWN")
        next_target_timestamp = None
        next_target_type = ""

        try:
            md = yf.Ticker(self.stock_symbol).get_history_metadata()
            tp = md.get("tradingPeriods")
            if tp is not None and not tp.empty:
                last_tp = tp.iloc[-1]
                start = last_tp['start']
                end = last_tp['end']
                now = pd.Timestamp.now(tz=start.tz)
                
                is_24_7 = (start.hour == 0 and start.minute == 0 and end.hour == 23 and end.minute == 59)
                
                if not is_24_7:
                    if now < start:
                        next_target_timestamp = start.timestamp()
                        next_target_type = "open"
                    elif start <= now < end:
                        next_target_timestamp = end.timestamp()
                        next_target_type = "close"
                    else:
                        next_start = start + timedelta(days=1)
                        while next_start.weekday() >= 5:
                            next_start += timedelta(days=1)
                        next_target_timestamp = next_start.timestamp()
                        next_target_type = "open"
        except Exception as e:
            logging.info(f"Could not parse market hours: {e}")

        if current_price == 0.0 and not data.empty:
            current_price = data['Close'].iloc[-1].iloc[0] if isinstance(data['Close'].iloc[-1], pd.Series) else data['Close'].iloc[-1]

        close_price = ticker_info.get("regularMarketPreviousClose", 0.0)
        percentage_increase = ticker_info.get("regularMarketChangePercent", 0.0)
        logging.info(f"{self.stock_symbol} Close: {currency_symbol}{close_price}")
        increase_symbol = '+' if percentage_increase >= 0 else ''
        logging.info(f"{self.stock_symbol} Increase: {increase_symbol}{percentage_increase:.2f}%")
        
        if debug_force_market_open:
            market_state = "REGULAR"
            next_target_timestamp = time.time() + 3600 * 3
            next_target_type = "close"
        
        result = {
            'data': data,
            'update_time': update_time,
            'currency_symbol': currency_symbol,
            'percentage_increase': percentage_increase,
            'increase_symbol': increase_symbol,
            'close_price': close_price,
            'current_price': current_price,
            'post_market_price': post_market_price,
            'post_market_percentage_increase': post_market_percentage_increase,
            'post_market_increase_symbol': post_market_increase_symbol,
            'market_state': market_state,
            'next_target_timestamp': next_target_timestamp,
            'next_target_type': next_target_type,
            'error': None
        }
        self.finished_download.emit(result)
        return
      except Exception as e:
        logging.info(f"An exception occurred: {str(e)}")
        logging.info(f"Download Attempt {try_counter + 1} failed.")
        logging.info("Retrying in 0.5 seconds...")
        time.sleep(0.5)
      try_counter += 1
      
    error_msg = f"Could not download stock data for {self.stock_symbol} after {retries} tries."
    logging.error(error_msg)
    result = {
        'data': pd.DataFrame(),
        'update_time': "Error",
        'currency_symbol': "",
        'percentage_increase': 0.0,
        'increase_symbol': "",
        'close_price': 0.0,
        'current_price': 0.0,
        'post_market_price': None,
        'post_market_percentage_increase': 0.0,
        'post_market_increase_symbol': "",
        'market_state': "UNKNOWN",
        'next_target_timestamp': None,
        'next_target_type': "",
        'error': error_msg
    }
    self.finished_download.emit(result)

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
    self.roundCorners()

    # Create plot
    time_axis = IndexTimeAxisItem(orientation='bottom')
    left_axis = MajorTickAxisItem(orientation='left')
    self.plotWidget = CrosshairPlotWidget(self.initial_crosshair, axisItems={'bottom': time_axis, 'left': left_axis})
    self.plotWidget.mouseMovedSignal.connect(self.onCrosshairMoved)
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
    
    self.startDownloadStockData()

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

    self.title_widget = self.createTitleWidget()
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

  def roundCorners(self):
    # Try Windows 11 native rounded corners first (smooth)
    if sys.platform == 'win32':
        try:
            build = int(platform.version().split('.')[2])
            if build >= 22000:
                hwnd = int(self.winId())
                value = ctypes.c_int(2) # DWMWCP_ROUND
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(value), ctypes.sizeof(value))
                return
        except Exception as e:
            logging.warning(f"Could not set native rounded corners: {e}")

    # Fallback to QRegion mask (works on Win10 and earlier)
    path = QPainterPath()
    rectf = QRectF(self.rect())
    path.addRoundedRect(rectf, 12.0, 12.0)

    # Create a QRegion with the QPainterPath and set it as the widget's mask
    region_ = QRegion(path.toFillPolygon().toPolygon())
    self.setMask(region_)

  # lag workaround for blurred background (makes window stutter):
  # def moveEvent(self, event) -> None:
  #   time.sleep(0.01)  # sleep for 10ms

  def resizeEvent(self, event) -> None:
    # Update the mask when the window is resized
    self.roundCorners()
    super().resizeEvent(event)

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

  def startDownloadStockData(self):
    self.download_worker = DownloadWorker(self.stock_symbol, self)
    self.download_worker.finished_download.connect(self.onDownloadFinished)
    self.download_worker.start()

  def onDownloadFinished(self, result):
    self.data = result['data']
    self.update_time = result['update_time']
    self.currency_symbol = result['currency_symbol']
    self.percentage_increase = result['percentage_increase']
    self.increase_symbol = result['increase_symbol']
    self.close_price = result['close_price']
    self.current_price = result['current_price']
    self.post_market_price = result.get('post_market_price')
    self.post_market_percentage_increase = result.get('post_market_percentage_increase')
    self.post_market_increase_symbol = result.get('post_market_increase_symbol')
    self.market_state = result.get('market_state', 'UNKNOWN')
    self.next_target_timestamp = result.get('next_target_timestamp')
    self.next_target_type = result.get('next_target_type')
    
    self.updateTitleWidgetText()
    if display_refresh_time and hasattr(self, 'refresh_time_label'):
      self.updateRefreshTimeLabel()
    self.plotStock()
    logging.info("Done Refreshing Plot")

  def refreshTimeLabel(self):
    # self.update_time is set by onDownloadFinished(), initially empty or 'Loading...'
    self.refresh_time_label = QLabel(f"{getattr(self, 'update_time', 'Loading...')}")
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

  def createTitleWidget(self):
    self.title_container = QWidget()
    
    layout = QVBoxLayout(self.title_container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    
    top_row = QHBoxLayout()
    top_row.setContentsMargins(0, 0, 0, 0)
    top_row.setSpacing(6)

    self.status_dot = QLabel()
    self.status_dot.setFixedSize(18, 18)
    self.status_dot.setStyleSheet("background-color: grey; border-radius: 9px;")
    
    self.main_price_label = QLabel()
    font = QFont()
    font.setPointSize(title_font_size)
    self.main_price_label.setFont(font)
    self.main_price_label.setContentsMargins(0, 0, 0, 0)
    
    self.dot_layout = QVBoxLayout()
    self.dot_layout.setContentsMargins(0, 3, 0, 0) # Exact margin to push it down
    self.dot_layout.addWidget(self.status_dot)
    
    top_row.addLayout(self.dot_layout)
    top_row.addWidget(self.main_price_label, alignment=Qt.AlignmentFlag.AlignTop)
    top_row.addStretch()
    
    bottom_row = QHBoxLayout()
    bottom_row.setContentsMargins(0, 0, 0, 0)
    bottom_row.setSpacing(6)
    
    self.countdown_label = QLabel()
    font = QFont()
    font.setPointSize(update_font_size)
    self.countdown_label.setFont(font)
    self.countdown_label.setStyleSheet(f"color: {legend_color};")
    self.countdown_label.setText("--:--:--")
    
    self.ah_price_label = QLabel()
    ah_font = QFont()
    ah_font.setPointSize(update_font_size)
    self.ah_price_label.setFont(ah_font)
    self.ah_price_label.setContentsMargins(0, 0, 0, 0)
    self.ah_price_label.hide()
    
    bottom_row.addWidget(self.countdown_label, alignment=Qt.AlignmentFlag.AlignVCenter)
    bottom_row.addWidget(self.ah_price_label, alignment=Qt.AlignmentFlag.AlignVCenter)
    bottom_row.addStretch()
    
    layout.addLayout(top_row)
    layout.addLayout(bottom_row)
    layout.addStretch()

    stylesheet = f"background-color: rgba(0, 0, 0, 0); color:{legend_color};"
    if debug:
      stylesheet += " border: 1px solid red;"
    self.title_container.setStyleSheet(stylesheet)

    self.dot_opacity_effect = QGraphicsOpacityEffect(self.status_dot)
    self.status_dot.setGraphicsEffect(self.dot_opacity_effect)
    self.dot_animation = QPropertyAnimation(self.dot_opacity_effect, b"opacity")
    self.dot_animation.setDuration(1500)
    self.dot_animation.setStartValue(0.2)
    self.dot_animation.setEndValue(1.0)
    self.dot_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
    self.dot_animation.setLoopCount(-1)

    self.countdown_timer = QTimer(self)
    self.countdown_timer.timeout.connect(self.updateCountdown)
    self.countdown_timer.start(1000)
    
    return self.title_container

  def updateCountdown(self):
    if not hasattr(self, 'next_target_timestamp') or self.next_target_timestamp is None:
        self.countdown_label.setText("")
        return

    now_ts = time.time()
    diff = int(self.next_target_timestamp - now_ts)
    if diff <= 0:
        self.countdown_label.setText("00:00:00")
        return

    hours = diff // 3600
    minutes = (diff % 3600) // 60
    seconds = diff % 60
    if hours > 0:
        self.countdown_label.setText(f"{hours}h:{minutes:02d}m:{seconds:02d}s")
    else:
        self.countdown_label.setText(f"{minutes:02d}m:{seconds:02d}s")

  def updateTitleWidgetText(self):
    if hasattr(self, 'market_state'):
        if self.market_state == "REGULAR":
            self.status_dot.setStyleSheet("background-color: #21b700; border-radius: 9px;")
            if self.dot_animation.state() != QPropertyAnimation.State.Running:
                self.dot_animation.start()
        else:
            self.status_dot.setStyleSheet("background-color: grey; border-radius: 9px;")
            self.dot_animation.stop()
            self.dot_opacity_effect.setOpacity(1.0)

    if not hasattr(self, 'data') or self.data is None or (isinstance(self.data, pd.DataFrame) and self.data.empty):
      self.main_price_label.setText(f"<font size='4'>{self.stock_symbol.upper()}</font> <font size='2' color='red'>Error: Could not load data</font>")
      self.ah_price_label.hide()
    else:
      if self.percentage_increase >= 0:
        text_color = chart_line_color_positive
      else:
        text_color = chart_line_color_negative
        
      main_text = f"""<font size='3'>{self.stock_symbol.upper()}</font>&nbsp;&nbsp;
                 <font size='2'>{self.currency_symbol}{self.current_price:.2f}</font>&nbsp;
                 <font size='2' color='{text_color}'>{self.increase_symbol}{self.percentage_increase:.2f}%{' ' + self.window_id if debug else ''}</font>"""
      self.main_price_label.setText(main_text)
                   
      is_regular = hasattr(self, 'market_state') and self.market_state == "REGULAR"
      if not is_regular and hasattr(self, 'post_market_price') and self.post_market_price is not None:
        if self.post_market_percentage_increase is not None and self.post_market_percentage_increase >= 0:
            pm_color = chart_line_color_positive
        else:
            pm_color = chart_line_color_negative
            
        pm_pct = self.post_market_percentage_increase if self.post_market_percentage_increase is not None else 0.0
        ah_text = f"""<font color='white'>AH: {self.currency_symbol}{self.post_market_price:.2f}</font>&nbsp;
                      <font color='{pm_color}'>{self.post_market_increase_symbol}{pm_pct:.2f}%</font>"""
        self.ah_price_label.setText(ah_text)
        self.ah_price_label.show()
      else:
        self.ah_price_label.hide()

  def startRefreshTimer(self):
    # Create a QTimer object
    self.refresh_timer = QTimer(self)
    # Connect the timer's timeout signal to the plot_stock method
    self.refresh_timer.timeout.connect(lambda: logging.info("Refreshing Plot..."))
    self.refresh_timer.timeout.connect(self.startDownloadStockData)
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

  def onCrosshairMoved(self, x):
    if not hasattr(self, 'data') or self.data is None or len(self.data) == 0:
      return
    
    index = int(round(x))
    if index < 0: index = 0
    elif index >= len(self.data['Close']): index = len(self.data['Close']) - 1
    
    y_val = float(self.data['Close'].iloc[index].item()) if hasattr(self.data['Close'].iloc[index], 'item') else float(self.data['Close'].iloc[index])
    
    if hasattr(self.plotWidget, 'vLine') and self.plotWidget.vLine is not None:
      self.plotWidget.vLine.setPos(index)
      self.plotWidget.hLine.setPos(y_val)
      
      time_val = self.data['Datetime'].iloc[index]
      if hasattr(time_val, 'strftime'):
          time_str = time_val.strftime("%Y-%m-%d %H:%M")
      else:
          time_str = str(time_val)
          
      self.plotWidget.textItem.setText(f"{time_str}\n${y_val:.2f}")
      if index > len(self.data['Close']) / 2:
          self.plotWidget.textItem.setAnchor((1.1, 0.5))
      else:
          self.plotWidget.textItem.setAnchor((-0.1, 0.5))
      self.plotWidget.textItem.setPos(index, y_val)

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

    if not hasattr(self, 'data') or self.data is None or (isinstance(self.data, pd.DataFrame) and self.data.empty):
      logging.info("No data to plot.")
      return

    # add crosshair
    self.plotWidget.vLine = pg.InfiniteLine(angle=90, movable=False)
    self.plotWidget.hLine = pg.InfiniteLine(angle=0, movable=False)
    self.plotWidget.textItem = pg.TextItem(text="", color=(255, 255, 255), fill=(0, 0, 0, 150))
    self.plotWidget.addItem(self.plotWidget.vLine, ignoreBounds=True)
    self.plotWidget.addItem(self.plotWidget.hLine, ignoreBounds=True)
    self.plotWidget.addItem(self.plotWidget.textItem, ignoreBounds=True)
    self.plotWidget.vLine.hide()
    self.plotWidget.hLine.hide()
    self.plotWidget.textItem.hide()

    # print(np.arange(len(self.data['Datetime'])))
    # Plot the stock data
    x = np.arange(len(self.data['Datetime']))
    y = self.data['Close'].to_numpy().flatten()

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
    
    bottom_axis = self.plotWidget.getAxis('bottom')
    if isinstance(bottom_axis, IndexTimeAxisItem):
        bottom_axis.set_datetimes(self.data['Datetime'])

    # Customize plot appearance
    self.plotWidget.showGrid(x=True, y=True)
    self.plotWidget.getAxis('right').setGrid(False)
    self.plotWidget.getAxis('top').setGrid(False)

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
    if self.data['Close'].iloc[-1].item() < self.data['Close'].iloc[0].item(): # compare last and first values and color chart accordingly 
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
      self.plotWidget.setYRange(float(np.nanmin(self.data['Close'].values)), float(np.nanmax(self.data['Close'].values)))
      # self.plotItem.plot(x=x, y=y, pen=pg.mkPen(color=chart_line_color, width=1))
    else:
      self.plotItem.plot(x=x, y=y, pen=pg.mkPen(color=chart_line_color, width=1))

    # https://stackoverflow.com/questions/69816567/pyqtgraph-cuts-off-tick-labels-if-showgrid-is-called
    for key in ['right', 'top']:
      self.plotWidget.showAxis(key)                            # Show top/right axis (and grid, since enabled here)
      axis = self.plotWidget.getAxis(key)
      axis.setStyle(showValues=False, tickLength=0)  # Hide tick labels and lines on top/right
      if key == 'right':
        axis.setWidth(2)  # Give the right axis a small width so its line doesn't get clipped

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