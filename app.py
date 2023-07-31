from PyQt6.QtWidgets import QMainWindow, QApplication, QSizeGrip, QLabel, QWidget, QVBoxLayout, QSystemTrayIcon, QMenu, QSizePolicy, QDialog, QPushButton
from PyQt6.QtCore import Qt, QSize, QPoint, QTimer, QCoreApplication, QSettings, QByteArray, QDataStream
from PyQt6.QtGui import QGuiApplication, QIcon, QAction, QFont
from BlurWindow.blurWindow import GlobalBlur
import time
import os
import winreg as reg
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import Formatter, FixedLocator
from datetime import datetime
import numpy as np
import pandas as pd
import yfinance as yf

### -------------------------------- Config -------------------------------- ###
app_name="StockWidget" # used as name for reg variable for auto startup
stock = "mu"
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
padding_multiplier = 0.5
y_label_every_x_datapoints = 100
title_font_size = 20
update_font_size = 8
center_window = False
drag_window = True
display_update_time = True
refresh_interval = 3600 # seconds
# refresh_interval = 20 # seconds
window_margins = [10, 10, 10, 10]
# debug = False # set to False for pyinstaller
debug = True # set to False for pyinstaller
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
# add last refreshed time
# 'cache' x axis date labels so that they dont have to be recalculated every time when resizing
# remove unnecessary resize event(s) at start
# make resizing smoother
# base amount of y axis tick labels on window size

class Settings(QMainWindow):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.setWindowTitle("Settings")
    self.setGeometry(100, 100, 300, 200)
    layout = QVBoxLayout()
    self.setLayout(layout)
    self.setting_button = QPushButton("Change Settings")
    layout.addWidget(self.setting_button)
    self.setting_button.clicked.connect(self.show_setting_dialog)

  def show_setting_dialog(self):
    # This method can be used to show another dialog for specific settings
    print("Settings dialog will open here.")
  
  def closeEvent(self, event):
    # Overriding closeEvent to hide the window instead of closing it
    self.hide()
    event.ignore()

class TrayIcon:
  def __init__(self, app):
    self.app = app
    # Create the system tray icon
    self.tray_icon = QSystemTrayIcon(self.app)
    self.tray_icon.setIcon(QIcon(self.resource_path("icon.ico")))

    # Create a menu for the system tray icon
    self.tray_menu = QMenu()
    self.quit_action = QAction("Quit", self.app)
    self.enable_startup_action = QAction("Enable Launch on Startup", self.app)
    self.disable_startup_action = QAction("Disable Launch on Startup", self.app)
    self.open_settings = QAction("Open Settings", self.app)

    self.enable_startup_action.setCheckable(True)
    self.enable_startup_action.setChecked(True) # TODO merge actions into 1 that is either checked or unchecked

    self.settings_window = Settings()
    self.quit_action.triggered.connect(lambda: QCoreApplication.quit())
    self.enable_startup_action.triggered.connect(self.enableLaunchOnStartup)
    self.disable_startup_action.triggered.connect(self.disableLaunchOnStartup)
    self.open_settings.triggered.connect(lambda: self.settings_window.show())
    self.tray_menu.addAction(self.quit_action)
    self.tray_menu.addAction(self.enable_startup_action)
    self.tray_menu.addAction(self.disable_startup_action)
    self.tray_menu.addAction(self.open_settings)

    # Add the menu to the system tray icon
    self.tray_icon.setContextMenu(self.tray_menu)

    # Show the system tray icon
    self.tray_icon.show()

  def enableLaunchOnStartup(self):
    # https://www.geeksforgeeks.org/autorun-a-python-script-on-windows-startup/
    app_path = self.exeFilePath()
    if app_path: # check that app is running as exe
      try:
        key = reg.HKEY_CURRENT_USER
        key_path = "Software\Microsoft\Windows\CurrentVersion\Run"
        open_key = reg.OpenKey(key, key_path, 0, reg.KEY_ALL_ACCESS)
        reg.SetValueEx(open_key, app_name, 0, reg.REG_SZ, app_path)
        reg.CloseKey(open_key)
        if debug:
          print(f"Successfully added to startup. Path: {app_path}")
      except Exception as e: # TODO Handle exception in gui
        if debug:
          print(f"Failed to add to startup. Error: {str(e)}")
    else:
      # if debug:
        print("Not running .exe")

  def disableLaunchOnStartup(self):
    if self.exeFilePath():
      try:
        key = reg.HKEY_CURRENT_USER
        key_path = "Software\Microsoft\Windows\CurrentVersion\Run"
        open_key = reg.OpenKey(key, key_path, 0, reg.KEY_ALL_ACCESS)

        # Delete the registry value if it exists
        if reg.QueryValueEx(open_key, app_name):
          reg.DeleteValue(open_key, app_name)
          if debug:
            print("Successfully removed from startup.")
        else:
          if debug:
            print("The registry value does not exist, nothing to remove.")

        reg.CloseKey(open_key)
      except Exception as e:
        if debug:
          print(f"Failed to remove from startup. Error: {str(e)}")
    else:
      # if debug:
        print("Not running .exe")

  def exeFilePath(self):
    if getattr(sys, 'frozen', False):
      # Running as an executable (compiled with PyInstaller)
      return sys.executable # returns "D:\Personal\Privat\Programming\desktop-widget\dist\app.exe"
    else:
      # Running as a regular Python script
      # return sys.argv[0] # returns ".\app.py"
      return False

  def resource_path(self, relative_path):
    # Get absolute path to resource, works for dev and for PyInstaller
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

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
  window_count = 0
  def __init__(self):
    super(Window, self).__init__(parent=None)
    Window.window_count += 1
    self.drag_start_position = None
    if debug:
      print(f"Start Creating Window {Window.window_count}")
    self.window_id = f"window_{Window.window_count}"
    # Call move with an invalid position to prevent default positioning
    # self.move(-1000, -1000)

    # Set the window's size to a fraction of the screen's size
    screen_size = QApplication.primaryScreen().size()  # Get the screen's size
    fraction_of_screen = 0.2  # Set the fraction of the screen size you want the window to occupy
    size_relative_to_screen = QSize(int(screen_size.width() * fraction_of_screen),
                                    int(screen_size.height() * fraction_of_screen))
    # self.resize(self.sizeHint().expandedTo(size_relative_to_screen))

    # Load settings from config file and move window
    settings = QSettings("config.ini", QSettings.Format.IniFormat)
    pos = settings.value(f"{self.window_id}_pos", QPoint(QGuiApplication.primaryScreen().availableGeometry().center()), type=QPoint)
    size = settings.value(f"{self.window_id}_size", QSize(size_relative_to_screen), type=QSize)
    self.move(pos)
    self.resize(size)
    self.setWindowTitle(f"{self.window_id}")
    self.setWindowFlag(Qt.WindowType.WindowStaysOnBottomHint | Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)

    if debug:
      print("Blurring Background...", end="")
    self.blurBackground()
    if debug:
      print("Done")
    # self.roundCorners() # TODO

    # Create a Figure and Canvas for Matplotlib plot
    if debug:
      self.figure = plt.figure(facecolor='blue')
    else:
      self.figure = plt.figure()
    self.canvas = FigureCanvas(self.figure)
    self.canvas.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    self.figure.patch.set_alpha(0)
    # self.canvas.setStyleSheet("QWidget { border: 1px solid red; }") # canvas is a widget
    
    self.downloadStockData()

    # Get stock currency
    self.currency_symbol = self.replaceCurrencySymbols(yf.Ticker(stock).info["currency"])

    # Add the title bar and canvas to a vertical layout

    self.title_widget = self.titleWidget()
    self.title_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
    self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    # Call the method to plot the stock graph on the canvas
    # self.plotStock()

    layout = QVBoxLayout()
    layout.addWidget(self.title_widget)
    layout.addWidget(self.canvas)
    if display_update_time:
      layout.addWidget(self.refreshTimeLabel())
    layout.setSpacing(0)
    layout.setContentsMargins(*window_margins)
    # layout.setContentsMargins(0, 0, 0, 0)

    # Create a central widget to hold the layout
    central_widget = QWidget()
    central_widget.setLayout(layout)
    self.setCentralWidget(central_widget)
    if debug:
      central_widget.setStyleSheet("border: 1px solid red;")

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
      if debug:
        grip.setStyleSheet("background-color: red;")

    self.startRefreshTimer()

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

  def moveEvent(self, event):
    # This method is called when the window is moved
    self.savePositionAndSize()
    super().moveEvent(event)

  def savePositionAndSize(self):
    settings = QSettings("config.ini", QSettings.Format.IniFormat)
    # pos_data = QByteArray()
    # stream = QDataStream(pos_data, QDataStream.WriteOnly)
    # stream << self.pos() # globalPosition()
    settings.setValue(f"{self.window_id}_pos", self.pos())
    settings.setValue(f"{self.window_id}_size", self.size())

  def downloadStockData(self):
    # Get stock data and convert index Datetime to its own column (['Datetime', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])
    if debug:
      print("Downloading Stock Data...")
      self.data = yf.download(stock, interval="1h", period="1mo", prepost=True, progress=True) # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
    else:
      self.data = yf.download(stock, interval="1h", period="1mo", prepost=True, progress=False) # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
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
      print(f"Updated Refresh Time to {self.update_time}")

  def titleWidget(self):
    if debug:
      title = QLabel(f"{stock.upper()} {self.currency_symbol}{self.data['Close'].iloc[-1]:.2f} {self.window_id}")
      title.setStyleSheet(f"color:{legend_color}; border: 1px solid red;")
    else:
      title = QLabel(f"{stock.upper()} {self.currency_symbol}{self.data['Close'].iloc[-1]:.2f}")
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
      self.refresh_timer.timeout.connect(lambda: print("Refreshing Plot..."))
    self.refresh_timer.timeout.connect(self.downloadStockData)
    self.refresh_timer.timeout.connect(self.plotStock)
    self.refresh_timer.timeout.connect(self.updateRefreshTimeLabel)
    if debug:
      self.refresh_timer.timeout.connect(lambda: print("Done"))
    # Start the timer with the specified refresh_interval in milliseconds
    self.refresh_timer.start(refresh_interval * 1000)

  def resizeEvent(self, event):
    self.plotStock() # replot stock to adjust to new window size
    if debug:
      print("Resize Event")
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
    # time.sleep(0.01)

  def centerWindow(self):
    frame_geometry = self.frameGeometry()
    screen_center = QGuiApplication.primaryScreen().availableGeometry().center()
    frame_geometry.moveCenter(screen_center)
    self.move(frame_geometry.topLeft())

  def is_mouse_inside_grip(self, pos):
    # print(pos)
    for grip in self.grips:
      if grip.geometry().contains(pos):
        return True
    return False

  if drag_window:
    def mousePressEvent(self, event):
      # print("press")
      self.candidate_start_position = event.globalPosition().toPoint()
      # if not self.is_mouse_inside_grip(self.candidate_start_position):
      if not self.is_mouse_inside_grip(event.pos()):
        self.drag_start_position = self.candidate_start_position

    def mouseReleaseEvent(self, event):
      # print("release")
      if event.button() == 1:  # Left mouse button
        self.drag_start_position = None

    def mouseMoveEvent(self, event):
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
      print("Plotting Stock...", end="")
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
    self.data['Close'].plot(ax=ax, color=chart_line_color)

    # Fill the area below the stock price line with a color
    if area_chart:
      ax.fill_between(self.data.index, self.data['Close'], color=chart_area_color, alpha=0.3, zorder=-1)

    # Customize the plot
    # ax.set_xlabel('Date', color='white', fontsize=10)
    # ax.set_ylabel('Stock Price (USD)', color='white', fontsize=10)
    # ax.set_title(f'{stock.upper()} Stock Price Chart', color=legend_color, fontsize=10)
    if debug:
      ax.set_facecolor('yellow')
    else:
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
    plt.xticks(x_labels[::y_label_every_x_datapoints], [format_x_label(str(label)) for label in self.data['Datetime'][::y_label_every_x_datapoints]], ha='center', color=legend_color)
    plt.gca().xaxis.set_minor_locator(FixedLocator(x_labels))
    # plt.gca().xaxis.set_minor_formatter(FuncFormatter(lambda x, pos: ""))
    # plt.xticks(rotation=45, color='white') # Rotate the x-axis labels for better readability
    plt.yticks(color=legend_color)  # Set y tick labels text color to white

    plt.tight_layout(pad=0.1) # TODO 0.1 otherwise right border is not visible
    # plt.autoscale(axis='x')
    # Refresh the canvas to update the plot
    self.canvas.draw()
    if debug:
      print("Done")

if __name__ == '__main__':
  if debug:
    print("Starting")
  import sys
  # used to end app with ctrl + c
  import signal
  signal.signal(signal.SIGINT, signal.SIG_DFL)

  if debug:
    print("Creating Application...", end="")
  app = QApplication(sys.argv)
  if debug:
    print("Done")
    print("Creating Tray Icon...", end="")
  tray_icon = TrayIcon(app)
  if debug:
    print("Done")
  windows = [Window(), Window(), Window()]
  for i, window in enumerate(windows):
    if debug:
      print(f"Showing Window {i + 1}")
    window.show()
    window.plotStock()
  if debug:
    print("Done")
  sys.exit(app.exec())