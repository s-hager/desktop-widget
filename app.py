from PyQt6 import QtGui
from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtCore import Qt, QSize, QPoint, QObject, QEvent, QRectF
from PyQt6.QtGui import QGuiApplication, QPainter, QRegion, QPainterPath
from BlurWindow.blurWindow import GlobalBlur
import time
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
monday_lines_style = 'solid'
monday_lines_transparency = 0.5
monday_lines_width = 1
vertical_lines = True
vertical_lines_color = 'white'
vertical_lines_style = (0, (5, 10))
vertical_lines_transparency = 0.5
vertical_lines_width = 0.5
padding_multiplier = 0.1
y_label_every_x_datapoints = 100
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

    # Initialize variables to track the mouse position
    # self.drag_start_position = self.pos()

    # Create a Figure and Canvas for Matplotlib plot
    self.figure = plt.figure()
    self.canvas = FigureCanvas(self.figure)
    self.canvas.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    self.figure.patch.set_alpha(0)
    self.setCentralWidget(self.canvas)
    self.canvas.installEventFilter(self)

    # Call the method to plot the stock graph
    self.plot_stock()

    # Center the window on the screen
    self.centerWindow()

  def eventFilter(self, obj: QObject, event: QEvent) -> bool:
    # Handle mouse events for the canvas and forward them to the window
    if obj == self.canvas and event.type() == QEvent.Type.MouseButtonPress:
        self.mousePressEvent(event)
    elif obj == self.canvas and event.type() == QEvent.Type.MouseMove:
        self.mouseMoveEvent(event)
    elif obj == self.canvas and event.type() == QEvent.Type.MouseButtonRelease:
        self.mouseReleaseEvent(event)
    return super().eventFilter(obj, event)

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

  def centerWindow(self):
    frame_geometry = self.frameGeometry()
    screen_center = QGuiApplication.primaryScreen().availableGeometry().center()
    frame_geometry.moveCenter(screen_center)
    self.move(frame_geometry.topLeft())

  # def mousePressEvent(self, event):
  #   self.drag_start_position = event.globalPos()

  # def mouseMoveEvent(self, event):
  #   delta = QPoint(event.globalPos() - self.drag_start_position())
  #   print(delta)

  # def mousePressEvent(self, event):
  #   # Get the current mouse position relative to the window's top-left corner
  #   self.drag_position = event.globalPos() - self.frameGeometry().topLeft()

  # def mouseMoveEvent(self, event):
  #   # If the user has pressed the left mouse button, move the window
  #   if event.buttons() == Qt.MouseButton.LeftButton:
  #     # Calculate the new window position based on the mouse movement
  #     new_position = event.globalPos() - self.drag_position
  #     self.move(new_position)

  # def mouseReleaseEvent(self, event):
  #   # Clear the drag position when the mouse button is released
  #   self.drag_position = None

  def mousePressEvent(self, event):
    # if event.button() == Qt.MouseButton.LeftButton:
      # Store the initial position of the mouse press
      self.drag_start_position = event.globalPosition().toPoint()
      # event.accept()

  def mouseMoveEvent(self, event):
    # if event.buttons() & Qt.MouseButton.LeftButton:
      # Calculate the new position of the window
      delta = QPoint(event.globalPosition().toPoint() - self.drag_start_position)
      self.move(self.x() + delta.x(), self.y() + delta.y())
      self.drag_start_position = event.globalPosition().toPoint()
      # event.accept()

  # def mouseReleaseEvent(self, event):
  #   # Reset the drag_start_position when the mouse is released
  #   self.drag_start_position = None
  #   event.accept()

  def blurBackground(self):
    self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    # GlobalBlur(self.winId(), Dark=True, Acrylic=True, QWidget=self)
    GlobalBlur(self.winId(), Dark=True, Acrylic=False, QWidget=self)
    # GlobalBlur(self.winId())
    # self.setStyleSheet("background-color: rgba(123, 123, 123, 123)")
    self.setStyleSheet("background-color: rgba(0, 0, 0, 0)")

  def plot_stock(self):
    # Function to convert datetime string to "July 26" format
    def format_x_label(datetime_str):
      # Parse the datetime string to a datetime object
      dt_obj = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S%z")
      # Format the datetime object to "July 26" format
      formatted_date = dt_obj.strftime("%B %d")
      return formatted_date

    # stock = "AAPL"
    data = yf.download(stock, interval="1h", period="1mo", prepost=True) # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
    # data = yf.download(stock, interval="5m", period="1wk", prepost=True) # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
    # print(data.to_markdown())
    # print(data)

    data = data.reset_index().rename({'index': 'Datetime'}, axis=1, copy=False)
    data['Datetime'] = pd.to_datetime(data['Datetime'])
    # print(data['Datetime'])

    formatter = CustomFormatter(data['Datetime'])
    # Clear the existing plot
    self.figure.clear()

    # Create a subplot and plot the stock data
    ax = self.figure.add_subplot(111)
    ax.xaxis.set_major_formatter(formatter)
    data['Close'].plot(ax=ax, color=chart_line_color)
    # Fill the area below the stock price line with a color
    if (area_chart):
      ax.fill_between(data.index, data['Close'], color=chart_area_color, alpha=0.3, zorder=-1)

    # Customize the plot
    # ax.set_xlabel('Date', color='white', fontsize=10)
    # ax.set_ylabel('Stock Price (USD)', color='white', fontsize=10)
    ax.set_title(f'{stock.upper()} Stock Price Chart', color=legend_color, fontsize=10)
    ax.set_facecolor('none')
    ax.tick_params(which='minor', size=0)
    ax.tick_params(color=legend_color, labelcolor=legend_color)
    # Remove left and right margins
    ax.margins(x=0)

    self.figure.set_size_inches(10, 7)
    
    # Set y-axis limits to avoid the area graph from being pushed up
    ymin = data['Close'].min()
    ymax = data['Close'].max()
    padding = padding_multiplier * (ymax - ymin)
    ax.set_ylim(ymin - padding, ymax + padding)

    x_labels = range(len(data['Datetime']))

    formatted_dates = [format_x_label(str(label)) for label in data['Datetime'][::y_label_every_x_datapoints]]
    
    if (monday_lines):
      # Loop through the formatted dates and draw vertical lines at the beginning of each Monday
      prev_week = None
      for i, formatted_date in enumerate(formatted_dates):
        date_obj = datetime.strptime(formatted_date, "%B %d")
        if prev_week is not None and prev_week != date_obj.isocalendar()[1]:
            # Draw a vertical line at position i
            ax.axvline(i * y_label_every_x_datapoints, color=monday_lines_color, alpha=monday_lines_transparency, linestyle=monday_lines_style, linewidth=monday_lines_width)
        prev_week = date_obj.isocalendar()[1]

    if (vertical_lines):
      # Add vertical lines at every y-tick position
      y_ticks_positions = ax.get_yticks()
      for y_tick_position in y_ticks_positions:
        ax.axhline(y_tick_position, color=vertical_lines_color, alpha=vertical_lines_transparency, linestyle=vertical_lines_style, linewidth=vertical_lines_width)

    # # Loop through the formatted dates and draw vertical lines after each date change
    # prev_formatted_date = None
    # for i, formatted_date in enumerate(formatted_dates):
    #     if prev_formatted_date is not None and prev_formatted_date != formatted_date:
    #         # Draw a vertical line at position i
    #         ax.axvline(i * label_every_x_datapoints, color='white', linestyle='dashed', linewidth=1)
    #     prev_formatted_date = formatted_date

    plt.xticks(x_labels[::y_label_every_x_datapoints], [format_x_label(str(label)) for label in data['Datetime'][::y_label_every_x_datapoints]], ha='right', color=legend_color) # Rotate the x-axis labels for better readability
    plt.gca().xaxis.set_minor_locator(FixedLocator(x_labels))
    # plt.gca().xaxis.set_minor_formatter(FuncFormatter(lambda x, pos: ""))
    # plt.xticks(rotation=45, color='white') # Rotate the x-axis labels for better readability
    plt.yticks(color=legend_color)  # Set y tick labels text color to white

    # Set the color of spines (borders) to white
    for spine in ax.spines.values():
      spine.set_color(legend_color)

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