from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QRegion, QPainterPath

from BlurWindow.blurWindow import GlobalBlur
import time

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

import yfinance as yf

class Window(QMainWindow):
  # lag workaround for blurred background (makes window stutter):
  def moveEvent(self, event) -> None:
    time.sleep(0.02)  # sleep for 20ms

  def resizeEvent(self, event) -> None:
    time.sleep(0.02)  # sleep for 20ms

  def __init__(self):
    super(Window, self).__init__(parent=None)
    self.setWindowTitle("no title")
    self.setWindowFlag(Qt.WindowType.WindowStaysOnBottomHint | Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
    
    self.roundCorners()

    # blur background
    # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    GlobalBlur(self.winId(),Dark=True,Acrylic=False,QWidget=self)
    # self.setStyleSheet("background-color: rgba(0, 0, 0, 0)")

    

    # Create a Figure and Canvas for Matplotlib plot
    self.figure = plt.figure()
    self.canvas = FigureCanvas(self.figure)
    self.figure.patch.set_alpha(0)
    self.setCentralWidget(self.canvas)

    # Call the method to plot the stock graph
    self.plot_stock()

  def roundCorners(self):
    # Create a QPainterPath with rounded corners
    path = QPainterPath()
    rectf = QRectF(self.rect())
    path.addRoundedRect(rectf, 20, 20)

    # Create a QRegion with the QPainterPath and set it as the widget's mask
    region = QRegion(path.toFillPolygon().toPolygon())
    self.setMask(region)


  def plot_stock(self):
    msft = yf.Ticker("MSFT")
    hist = msft.history(interval="1d", period="1mo") # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
    # print(hist)

    # Clear the existing plot
    self.figure.clear()

    # Create a subplot and plot the stock data
    ax = self.figure.add_subplot(111)
    hist['Close'].plot(ax=ax, color='white')

    # Customize the plot
    ax.set_xlabel('Date', color='white')
    ax.set_ylabel('Stock Price (USD)', color='white')
    ax.set_title('Microsoft (MSFT) Stock Price Chart', color='white')
    ax.set_facecolor('none')

    ax.tick_params(color='red', labelcolor='red')

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