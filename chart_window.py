from PyQt6.QtWidgets import (QMainWindow, QApplication, QSizeGrip, QLabel, QWidget, 
                             QVBoxLayout, QSizePolicy)
from PyQt6.QtCore import Qt, QSize, QPoint, QTimer
from PyQt6.QtGui import QGuiApplication, QFont
from BlurWindow.blurWindow import GlobalBlur
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import Formatter, FixedLocator
from datetime import datetime
import numpy as np
import pandas as pd
import yfinance as yf

# own variables:
from config import *
from constants import *

# https://stackoverflow.com/questions/54277905/how-to-disable-date-interpolation-in-matplotlib
class CustomFormatter(Formatter):
  def __init__(self, dates, format='%Y-%m-%d %H:%M:%S-%H:%M'):
    self.dates = dates
    self.format = format

  def __call__(self, x, pos=0):
    'Return the label for time x at position pos'
    index = int(np.round(x))
    if index >= len(self.dates) or index < 0:
      return ''
    return self.dates[index].strftime(self.format)

class ChartWindow(QMainWindow):
  def __init__(self, stock_symbol, window_id=None):
    super(ChartWindow, self).__init__(parent=None)
    self.first_resize = True
    self.stock_symbol = stock_symbol
    self.drag_start_position = None
    window_id = window_id_counter
    self.value_to_highlight = 68.82
    if debug:
      print(f"DEBUG: Start Creating Window with id {window_id}")
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

    if debug:
      print("DEBUG: Blurring Background...", end="")
    self.blurBackground()
    if debug:
      print("Done")
    # self.roundCorners() # TODO

    # Create a Figure and Canvas for Matplotlib plot
    if debug:
      self.figure = plt.figure(facecolor='blue')
    else:
      self.figure = plt.figure()
    # self.figure.tight_layout(pad=0.1)
    self.canvas = FigureCanvas(self.figure)
    self.canvas.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    self.figure.patch.set_alpha(0)
    # self.canvas.setStyleSheet("QWidget { border: 1px solid red; }") # canvas is a widget
    
    self.downloadStockData()

    # Get stock currency
    self.currency_symbol = self.replaceCurrencySymbols(yf.Ticker(self.stock_symbol).info["currency"])

    # Add the title bar and canvas to a vertical layout

    self.title_widget = self.titleWidget()
    self.title_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
    self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    # Call the method to plot the stock graph on the canvas
    # self.plotStock()

    layout = QVBoxLayout()
    layout.addWidget(self.title_widget)
    layout.addWidget(self.canvas)
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

    self.canvas.installEventFilter(self)

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
  #   # print(f"Move Event on window {window_id}")
  #   self.savePositionAndSize()
  #   super().moveEvent(event)

  def savePositionAndSize(self):
    settings.setValue(f"{self.window_id}_pos", self.pos())
    settings.setValue(f"{self.window_id}_size", self.size())

  def downloadStockData(self):
    # Get stock data and convert index Datetime to its own column (['Datetime', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])
    if debug:
      print("DEBUG: Downloading Stock Data...")
      self.data = yf.download(self.stock_symbol, interval="1h", period="1mo", prepost=True, progress=True) # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
    else:
      self.data = yf.download(self.stock_symbol, interval="1h", period="1mo", prepost=True, progress=False) # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
    self.update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    self.data = self.data.reset_index().rename({'index': 'Datetime'}, axis=1, copy=False)
    self.data['Datetime'] = pd.to_datetime(self.data['Datetime'])

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
    if debug:
      print(f"DEBUG: Updated Refresh Time to {self.update_time}")

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
    if debug:
      self.refresh_timer.timeout.connect(lambda: print("DEBUG: Refreshing Plot..."))
    self.refresh_timer.timeout.connect(self.downloadStockData)
    self.refresh_timer.timeout.connect(self.plotStock)
    self.refresh_timer.timeout.connect(self.updateRefreshTimeLabel)
    if debug:
      self.refresh_timer.timeout.connect(lambda: print("Done"))
    # Start the timer with the specified refresh_interval in milliseconds
    self.refresh_timer.start(refresh_interval * 1000)

  def resizeEvent(self, event):
    # Dont plot stock on first default resize event
    if self.first_resize:
      self.first_resize = False
      return
    else:
      self.plotStock() # replot stock to adjust to new window size
      if debug:
        print(f"DEBUG: Resize Event")
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
    # print(pos)
    for grip in self.grips:
      if grip.geometry().contains(pos):
        return True
    return False

  def mousePressEvent(self, event):
    if drag_window or self.drag_resize:
      # print("press")
      self.candidate_start_position = event.globalPosition().toPoint()
      # if not self.is_mouse_inside_grip(self.candidate_start_position):
      if not self.is_mouse_inside_grip(event.pos()):
        self.drag_start_position = self.candidate_start_position
    else:
      pass

  def mouseReleaseEvent(self, event):
    if drag_window or self.drag_resize:
      # print("release")
      if event.button() == 1:  # Left mouse button
        self.drag_start_position = None

  def mouseMoveEvent(self, event):
    if drag_window or self.drag_resize:
      # print("move")
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

    if debug:
      print("DEBUG: Plotting Stock...", end="")
    # stock = "AAPL"
    # data = yf.download(stock, interval="1h", period="1mo", prepost=True) # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
    # data = yf.download(stock, interval="5m", period="1wk", prepost=True) # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
    # print(data.to_markdown())
    # print(data)

    # print(data['Datetime'])

    # So that days where no market activity took place are omitted instead of drawn as a straight line 
    formatter = CustomFormatter(self.data['Datetime'])

    # Clear the existing plot
    self.figure.clear()

    # Create a subplot and plot the stock data
    ax = self.figure.add_subplot(111)
    ax.xaxis.set_major_formatter(formatter)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(self.format_y_tick_label))
    if self.data['Close'].iloc[-1] < self.data['Close'].iloc[0]: # compare last and first values and color chart accordingly 
      self.data['Close'].plot(ax=ax, color=chart_line_color_negative)
    else:
      self.data['Close'].plot(ax=ax, color=chart_line_color_positive)
    self.figure.set_tight_layout({'pad': 0.1}) # TODO 0.1 otherwise right border is not visible

    # Fill the area below the stock price line with a color
    if area_chart:
      if self.data['Close'].iloc[-1] < self.data['Close'].iloc[0]: # compare last and first values and color chart accordingly 
        ax.fill_between(self.data.index, self.data['Close'], color=chart_area_color_negative, alpha=0.3, zorder=-1)
      else:
        ax.fill_between(self.data.index, self.data['Close'], color=chart_area_color_positive, alpha=0.3, zorder=-1)

    if bought_line:
      ax.axhline(y=self.value_to_highlight, color='yellow', linewidth=1)
      ax.scatter(0, self.value_to_highlight, color='yellow', s=25, marker='o')  # 0 is the x-coordinate for the dot

    # Customize the plot
    # ax.set_xlabel('Date', color='white', fontsize=10)
    # ax.set_ylabel('Stock Price (USD)', color='white', fontsize=10)
    # ax.set_title(f'{stock.upper()} Stock Price Chart', color=legend_color, fontsize=10)
    # if debug:
    #   ax.set_facecolor('yellow')
    # else:
    ax.set_facecolor('none')

    ax.tick_params(which='minor', size=0)
    ax.tick_params(color=legend_color, labelcolor=legend_color)
    ax.tick_params(left = False, bottom = False)
    ax.tick_params(axis='x', which='major', labelsize=8, pad=0)
    ax.tick_params(axis='y', which='major', labelsize=8, pad=0)
    # Remove left and right margins
    ax.margins(x=0)
    # Remove graph frame (borders)
    # ax.spines['top'].set_visible(False)
    # ax.spines['right'].set_visible(False)
    # ax.spines['bottom'].set_visible(False)
    # ax.spines['left'].set_visible(False)
    # ax.spines['top'].set_color(legend_color)
    # ax.spines['right'].set_color(legend_color)
    # ax.spines['bottom'].set_color(legend_color)
    # ax.spines['left'].set_color(legend_color)
    # ax.spines['top'].set_alpha(0.5)
    # ax.spines['right'].set_alpha(0.5)
    # ax.spines['bottom'].set_alpha(0.5)
    # ax.spines['left'].set_alpha(0.5)
    # Set the color of spines (borders) to white and change their transparency
    for spine in ax.spines.values():
      spine.set_color(legend_color)
      spine.set_alpha(0.5)

    # ax.autoscale()
    # self.figure.set_size_inches(4.8, 2)

    # Set y-axis limits to avoid the area graph from being pushed up
    ymin = self.data['Close'].min()
    ymax = self.data['Close'].max()
    padding = padding_multiplier * (ymax - ymin)
    ax.set_ylim(ymin - padding, ymax + padding)

    if monday_lines:
      formatted_dates = [format_x_label(str(label)) for label in self.data['Datetime'][::y_label_every_x_datapoints]]
      # Loop through the formatted dates and draw vertical lines at the beginning of each Monday
      prev_week = None
      for i, formatted_date in enumerate(formatted_dates):
        date_obj = datetime.strptime(formatted_date, "%B %d")
        if prev_week is not None and prev_week != date_obj.isocalendar()[1]:
            # Draw a vertical line at position i
            ax.axvline(i * y_label_every_x_datapoints, color=monday_lines_color, alpha=monday_lines_transparency, linestyle=monday_lines_style, linewidth=monday_lines_width)
        prev_week = date_obj.isocalendar()[1]

    if horizontal_lines:
      # Add horizontal lines at every y-tick position
      y_ticks_positions = ax.get_yticks()
      for y_tick_position in y_ticks_positions:
        ax.axhline(y_tick_position, color=horizontal_lines_color, alpha=horizontal_lines_transparency, linestyle=horizontal_lines_style, linewidth=horizontal_lines_width)

    x_labels = range(len(self.data['Datetime']))
    ax.set_xticks(x_labels[::y_label_every_x_datapoints], [format_x_label(str(label)) for label in self.data['Datetime'][::y_label_every_x_datapoints]], ha='center', color=legend_color)
    ax.xaxis.set_minor_locator(FixedLocator(x_labels))
    # plt.gca().xaxis.set_minor_formatter(FuncFormatter(lambda x, pos: ""))
    # plt.xticks(rotation=45, color='white') # Rotate the x-axis labels for better readability
    ax.yaxis.set_tick_params(color=legend_color)  # Set y tick labels text color to white

    # plt.tight_layout(pad=0.1) # TODO 0.1 otherwise right border is not visible
    # plt.autoscale(axis='x')
    # Refresh the canvas to update the plot
    self.canvas.draw()
    if debug:
      print("Done")