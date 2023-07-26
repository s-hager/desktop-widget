from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QRegion, QPainterPath
from BlurWindow.blurWindow import GlobalBlur
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import Formatter
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
    # self.setWindowFlag(Qt.WindowType.WindowStaysOnBottomHint | Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
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
    stock = "AAPL"
    data = yf.download(stock, interval="1h", period="1mo", prepost=True) # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
    # print(data.to_markdown())
    print(data)

    data = data.reset_index().rename({'index': 'Datetime'}, axis=1, copy=False)
    data['Datetime'] = pd.to_datetime(data['Datetime'])
    print(data['Datetime'])

    formatter = CustomFormatter(data['Datetime'])
    # Clear the existing plot
    self.figure.clear()

    # Create a subplot and plot the stock data
    ax = self.figure.add_subplot(111)
    ax.xaxis.set_major_formatter(formatter)
    data['Close'].plot(ax=ax, color='green')

    # Customize the plot
    ax.set_xlabel('Date', color='white', fontsize=10)
    ax.set_ylabel('Stock Price (USD)', color='white', fontsize=10)
    ax.set_title(f'{stock} Stock Price Chart', color='white', fontsize=10)
    ax.set_facecolor('none')

    ax.tick_params(color='white', labelcolor='white')

    self.figure.set_size_inches(10, 6)

    # plt.xticks(rotation=45, color='white') # Rotate the x-axis labels for better readability
    # plt.yticks(color='white')  # Set y tick labels text color to white

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