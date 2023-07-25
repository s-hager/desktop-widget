from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

import yfinance as yf

class Window(QMainWindow):
  def __init__(self):
    super().__init__(parent=None)
    self.setWindowTitle("no title")
    self.setWindowFlag(Qt.WindowType.WindowStaysOnBottomHint | Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)

    # Create a Figure and Canvas for Matplotlib plot
    self.figure = plt.figure()
    self.canvas = FigureCanvas(self.figure)
    self.setCentralWidget(self.canvas)

    # Call the method to plot the stock graph
    self.plot_stock()

  def plot_stock(self):
    msft = yf.Ticker("MSFT")
    hist = msft.history(period="1mo")
    print(hist)

    # Clear the existing plot
    self.figure.clear()

    # Create a subplot and plot the stock data
    ax = self.figure.add_subplot(111)
    hist['Close'].plot(ax=ax)

    # Customize the plot
    ax.set_xlabel('Date')
    ax.set_ylabel('Stock Price (USD)')
    ax.set_title('Microsoft (MSFT) Stock Price Chart')

    # Rotate the x-axis labels for better readability
    plt.xticks(rotation=45)

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