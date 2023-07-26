from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QRegion, QPainterPath
from BlurWindow.blurWindow import GlobalBlur
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import Formatter, FixedLocator
from datetime import datetime
import numpy as np
import pandas as pd
import yfinance as yf

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
  # lag workaround for blurred background (makes window stutter):
  def moveEvent(self, event) -> None:
    time.sleep(0.01)  # sleep for 10ms

  def resizeEvent(self, event) -> None:
    time.sleep(0.01)  # sleep for 10ms

  def __init__(self):
    super(Window, self).__init__(parent=None)
    self.setWindowTitle("no title")
    self.setWindowFlag(Qt.WindowType.WindowStaysOnBottomHint | Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
    # self.resize(400, 300)

    self.blurBackground()
    # self.roundCorners()

    # Create a Figure and Canvas for Matplotlib plot
    self.figure = plt.figure()
    self.canvas = FigureCanvas(self.figure)
    self.figure.patch.set_alpha(0)
    self.setCentralWidget(self.canvas)

    # Call the method to plot the stock graph
    self.plot_stock()

  # def roundCorners(self):
  #   # Create a QPainterPath with rounded corners
  #   path = QPainterPath()
  #   rectf = QRectF(self.rect())
  #   path.addRoundedRect(rectf, 100, 100)

  #   # Create a QRegion with the QPainterPath and set it as the widget's mask
  #   region = QRegion(path.toFillPolygon().toPolygon())
  #   self.setMask(region)

  def blurBackground(self):
    self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    GlobalBlur(self.winId(),Dark=True,Acrylic=False,QWidget=self)
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

    stock = "AAPL"
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
    data['Close'].plot(ax=ax, color='#4ece6f')
    # Fill the area below the stock price line with a color
    ax.fill_between(data.index, data['Close'], color='green', alpha=0.3, zorder=-1)

    # Customize the plot
    ax.set_xlabel('Date', color='white', fontsize=10)
    ax.set_ylabel('Stock Price (USD)', color='white', fontsize=10)
    ax.set_title(f'{stock} Stock Price Chart', color='white', fontsize=10)
    ax.set_facecolor('none')
    ax.tick_params(which='minor', size=0)
    ax.tick_params(color='white', labelcolor='white')

    self.figure.set_size_inches(10, 7)
    
    # Set y-axis limits to avoid the graph from being pushed up
    ymin = data['Close'].min()
    ymax = data['Close'].max()
    padding = 0.1 * (ymax - ymin)
    ax.set_ylim(ymin - padding, ymax + padding)

    x_labels = range(len(data['Datetime']))
    label_every_x_datapoints = 20

    formatted_dates = [format_x_label(str(label)) for label in data['Datetime'][::label_every_x_datapoints]]
    
    # Loop through the formatted dates and draw vertical lines at the beginning of each Monday
    prev_week = None
    for i, formatted_date in enumerate(formatted_dates):
      date_obj = datetime.strptime(formatted_date, "%B %d")
      if prev_week is not None and prev_week != date_obj.isocalendar()[1]:
          # Draw a vertical line at position i
          ax.axvline(i * label_every_x_datapoints, color='white', linestyle='dashed', linewidth=1)
      prev_week = date_obj.isocalendar()[1]

    # # Loop through the formatted dates and draw vertical lines after each date change
    # prev_formatted_date = None
    # for i, formatted_date in enumerate(formatted_dates):
    #     if prev_formatted_date is not None and prev_formatted_date != formatted_date:
    #         # Draw a vertical line at position i
    #         ax.axvline(i * label_every_x_datapoints, color='white', linestyle='dashed', linewidth=1)
    #     prev_formatted_date = formatted_date

    plt.xticks(x_labels[::label_every_x_datapoints], [format_x_label(str(label)) for label in data['Datetime'][::label_every_x_datapoints]], rotation=45, ha='right', color='white') # Rotate the x-axis labels for better readability
    plt.gca().xaxis.set_minor_locator(FixedLocator(x_labels))
    # plt.gca().xaxis.set_minor_formatter(FuncFormatter(lambda x, pos: ""))
    # plt.xticks(rotation=45, color='white') # Rotate the x-axis labels for better readability
    plt.yticks(color='white')  # Set y tick labels text color to white

    # Set the color of spines (borders) to white
    for spine in ax.spines.values():
      spine.set_color('white')

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