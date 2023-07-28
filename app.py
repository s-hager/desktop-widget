from PyQt6 import QtGui
from PyQt6.QtWidgets import QMainWindow, QApplication, QSizeGrip, QLabel, QWidget, QVBoxLayout, QSystemTrayIcon, QMenu
from PyQt6.QtCore import Qt, QSize, QPoint, QTimer, QCoreApplication, QObject, QEvent, QRectF
from PyQt6.QtGui import QGuiApplication, QIcon, QAction, QFont, QCursor, QPainter, QRegion, QPainterPath
from BlurWindow.blurWindow import GlobalBlur
import time
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import Formatter, FixedLocator
from datetime import datetime
import numpy as np
import pandas as pd
import yfinance as yf

### -------------------------------- Config -------------------------------- ###
stock = "mu" # temp
legend_color = 'white'
chart_area_color = 'green'
chart_line_color = '#4ece6f'
area_chart = True
monday_lines = True
monday_lines_color = 'white'
monday_lines_style = 'solid' # https://matplotlib.org/stable/gallery/lines_bars_and_markers/linestyles.html
monday_lines_transparency = 0.5
monday_lines_width = 1
horizontal_lines = True
horizontal_lines_color = 'white'
horizontal_lines_style = (0, (5, 10)) # https://matplotlib.org/stable/gallery/lines_bars_and_markers/linestyles.html
horizontal_lines_transparency = 0.5
horizontal_lines_width = 0.5
padding_multiplier = 0.1
y_label_every_x_datapoints = 100
title_font_size = 20
center_window = True
drag_window = True
refresh_interval = 3600 # seconds
### ------------------------------------------------------------------------ ###

## TODO
# remove space from left and right of graph
# add vertical lines for price
# auto refresh charts
# button to add additional charts
# stock symbol input field
# make size and position adjustable and fixable
# make app a tool that lives in tray and starts up automatically
# make corners rounded
# make transparency better (without time.sleep)
# create options menu

def replaceCurrencySymbols(text):
  currency_symbols = {
      "USD": "$",
      "EUR": "€",
      "JPY": "¥",
      "GBP": "£",
  }
  for currency_code, currency_symbol in currency_symbols.items():
      text = text.replace(currency_code, currency_symbol)
  return text


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

class Window(QMainWindow):
  def __init__(self):
    super(Window, self).__init__(parent=None)
    self.setWindowTitle("no title")
    self.setWindowFlag(Qt.WindowType.WindowStaysOnBottomHint | Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)

    self.blurBackground()
    # self.roundCorners()

    # Set the window's size to a fraction of the screen's size
    screen_size = QApplication.primaryScreen().size()  # Get the screen's size
    fraction_of_screen = 0.2  # Set the fraction of the screen size you want the window to occupy
    size_relative_to_screen = QSize(int(screen_size.width() * fraction_of_screen),
                                    int(screen_size.height() * fraction_of_screen))
    self.resize(self.sizeHint().expandedTo(size_relative_to_screen))
    
    # Create a Figure and Canvas for Matplotlib plot
    self.figure = plt.figure()
    self.canvas = FigureCanvas(self.figure)
    self.canvas.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    self.figure.patch.set_alpha(0.1) #TODO not ideal solution (actually should be 0 but then only graph instead of entire window is draggable)
    # self.setCentralWidget(self.canvas)
    # self.canvas.installEventFilter(self)

    self.canvas.setStyleSheet("border: 1px solid red;") # canvas is a widget

    # Get stock data and convert index Datetime to its own column (['Datetime', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])
    self.data = yf.download(stock, interval="1h", period="1mo", prepost=True, progress=False) # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
    self.data = self.data.reset_index().rename({'index': 'Datetime'}, axis=1, copy=False)
    self.data['Datetime'] = pd.to_datetime(self.data['Datetime'])
    # Get stock currency
    self.currency_symbol = replaceCurrencySymbols(yf.Ticker(stock).info["currency"])

    # Add the title bar and canvas to a vertical layout
    layout = QVBoxLayout()
    layout.addWidget(self.titleWidget())
    layout.addWidget(self.canvas)
    layout.setSpacing(0)
    layout.setContentsMargins(20, 20, 20, 20)

    # Create a central widget to hold the layout
    central_widget = QWidget()
    central_widget.setLayout(layout)
    self.setCentralWidget(central_widget)

    self.canvas.installEventFilter(self)

    if center_window:
      # Center the window on the screen
      self.centerWindow()

    # Add resize grips
    self.gripSize = 16
    self.grips = []
    for i in range(4):
      grip = QSizeGrip(self)
      grip.resize(self.gripSize, self.gripSize)
      self.grips.append(grip)

    # Call the method to plot the stock graph
    self.plotStock()

    self.startRefreshTimer()

    # Create tray icon
    self.trayIcon()

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

  def resource_path(self, relative_path):
    # Get absolute path to resource, works for dev and for PyInstaller
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

  def trayIcon(self):
    # Create the system tray icon
    self.tray_icon = QSystemTrayIcon(self)
    self.tray_icon.setIcon(QIcon(self.resource_path("icon.ico")))

    # Create a menu for the system tray icon
    self.tray_menu = QMenu()
    self.quit_action = QAction("Quit", self)
    self.quit_action.triggered.connect(self.quitApp)
    self.tray_menu.addAction(self.quit_action)

    # Add the menu to the system tray icon
    self.tray_icon.setContextMenu(self.tray_menu)

    # Show the system tray icon
    self.tray_icon.show()

  def quitApp(self):
    QCoreApplication.quit()

  def titleWidget(self):
    # print(type(self.data))
    # print(self.data.columns)
    title = QLabel(f"{stock.upper()} {self.currency_symbol}{round(self.data['Close'].iloc[-1], 2)}")
    # title.setAlignment(Qt.AlignmentFlag.AlignLeft)
    title.setStyleSheet(f"color:{legend_color};")
    # title.setStyleSheet("color:white; border: 1px solid red;")
    font = QFont()
    font.setPointSize(title_font_size)
    title.setFont(font)
    return title

  def startRefreshTimer(self):
    # Create a QTimer object
    self.refresh_timer = QTimer(self)
    # Connect the timer's timeout signal to the plot_stock method
    self.refresh_timer.timeout.connect(self.plotStock)
    # Start the timer with the specified refresh_interval in milliseconds
    self.refresh_timer.start(refresh_interval * 1000)

  def resizeEvent(self, event):
    QMainWindow.resizeEvent(self, event)
    rect = self.rect()
    # top left grip doesn't need to be moved...
    # top right
    self.grips[1].move(rect.right() - self.gripSize, 0)
    # bottom right
    self.grips[2].move(
        rect.right() - self.gripSize, rect.bottom() - self.gripSize)
    # bottom left
    self.grips[3].move(0, rect.bottom() - self.gripSize)
    time.sleep(0.01)

  def centerWindow(self):
    frame_geometry = self.frameGeometry()
    screen_center = QGuiApplication.primaryScreen().availableGeometry().center()
    frame_geometry.moveCenter(screen_center)
    self.move(frame_geometry.topLeft())

  if drag_window:
    def mousePressEvent(self, event):
      self.drag_start_position = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
      delta = QPoint(event.globalPosition().toPoint() - self.drag_start_position)
      self.move(self.x() + delta.x(), self.y() + delta.y())
      self.drag_start_position = event.globalPosition().toPoint()

  def blurBackground(self):
    self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    # GlobalBlur(self.winId(), Dark=True, Acrylic=True, QWidget=self)
    GlobalBlur(self.winId(), Dark=True, Acrylic=False, QWidget=self)
    # GlobalBlur(self.winId())
    # self.setStyleSheet("background-color: rgba(123, 123, 123, 123)")
    self.setStyleSheet("background-color: rgba(0, 0, 0, 0)")

  def plotStock(self):
    # Function to convert datetime string to "July 26" format
    def format_x_label(datetime_str):
      # Parse the datetime string to a datetime object
      dt_obj = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S%z")
      # Format the datetime object to "July 26" format
      formatted_date = dt_obj.strftime("%B %d")
      return formatted_date

    # stock = "AAPL"
    # data = yf.download(stock, interval="1h", period="1mo", prepost=True) # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
    # data = yf.download(stock, interval="5m", period="1wk", prepost=True) # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
    # print(data.to_markdown())
    # print(data)

    # print(data['Datetime'])

    formatter = CustomFormatter(self.data['Datetime'])
    # Clear the existing plot
    self.figure.clear()

    # Create a subplot and plot the stock data
    ax = self.figure.add_subplot(111)
    ax.xaxis.set_major_formatter(formatter)
    self.data['Close'].plot(ax=ax, color=chart_line_color)
    # Fill the area below the stock price line with a color
    if (area_chart):
      ax.fill_between(self.data.index, self.data['Close'], color=chart_area_color, alpha=0.3, zorder=-1)

    # Customize the plot
    # ax.set_xlabel('Date', color='white', fontsize=10)
    # ax.set_ylabel('Stock Price (USD)', color='white', fontsize=10)
    # ax.set_title(f'{stock.upper()} Stock Price Chart', color=legend_color, fontsize=10)
    ax.set_facecolor('none')
    ax.tick_params(which='minor', size=0)
    ax.tick_params(color=legend_color, labelcolor=legend_color)
    ax.tick_params(left = False, bottom = False)
    # Remove left and right margins
    ax.margins(x=0)
    # Remove graph frame (borders)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    # ax.autoscale()
    self.figure.set_size_inches(5, 2)

    # Set y-axis limits to avoid the area graph from being pushed up
    ymin = self.data['Close'].min()
    ymax = self.data['Close'].max()
    padding = padding_multiplier * (ymax - ymin)
    ax.set_ylim(ymin - padding, ymax + padding)

    if (monday_lines):
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
    plt.xticks(x_labels[::y_label_every_x_datapoints], [format_x_label(str(label)) for label in self.data['Datetime'][::y_label_every_x_datapoints]], ha='center', color=legend_color)
    plt.gca().xaxis.set_minor_locator(FixedLocator(x_labels))
    # plt.gca().xaxis.set_minor_formatter(FuncFormatter(lambda x, pos: ""))
    # plt.xticks(rotation=45, color='white') # Rotate the x-axis labels for better readability
    plt.yticks(color=legend_color)  # Set y tick labels text color to white

    # Set the color of spines (borders) to white
    for spine in ax.spines.values():
      spine.set_color(legend_color)

    plt.tight_layout()
    # Refresh the canvas to update the plot
    self.canvas.draw()

if __name__ == '__main__':
  import sys
  # used to end app with ctrl + c
  import signal
  signal.signal(signal.SIGINT, signal.SIG_DFL)

  app = QApplication(sys.argv)
  window = Window()
  window.show()
  sys.exit(app.exec())