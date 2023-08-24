from PyQt6.QtWidgets import (QMainWindow, QApplication, QSizeGrip, QLabel, QWidget, 
                             QVBoxLayout, QSystemTrayIcon, QMenu, QSizePolicy, QCheckBox, 
                             QLineEdit, QPushButton, QHBoxLayout, QMessageBox)
from PyQt6.QtCore import Qt, QSize, QPoint, QTimer, QCoreApplication, QSettings, QRectF
from PyQt6.QtGui import QGuiApplication, QIcon, QAction, QFont, QCursor, QRegion, QPainterPath
from BlurWindow.blurWindow import GlobalBlur
import sys
import signal
import time
import os
import re
if 'nt' in sys.builtin_module_names:
  import winreg as reg
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import Formatter, FixedLocator
from datetime import datetime
import numpy as np
import pandas as pd
import yfinance as yf
import logging

import functools

# own files:
from config import *
from constants import *
from tray_icon import TrayIcon
from chart_window import ChartWindow # TODO: rewrite so this is not required here

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
# use createNewChartWindow also at startup
# fix program closing after waking up from sleep mode
# fix program behaviour when monitor is connected/disconnected

def main():
  if debug:
    if log_to_file:
      logging.basicConfig(filename="stockwidget.log", filemode="w", level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')
      # logging.basicConfig(filename="stockwidget.log", filemode="w", level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')
    else:
      logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')
      # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')
  global window_id_counter
  logging.info("Starting")
  # used to end app with ctrl + c
  signal.signal(signal.SIGINT, signal.SIG_DFL)

  logging.info("Creating Application...")
  app = QApplication(sys.argv)
  logging.info("Done Creating Application")
  # windows = [ChartWindow(), ChartWindow(), ChartWindow()]
  all_keys = settings.allKeys()
  for i, key in enumerate(all_keys):
    if key.startswith("window_") and key.endswith("_symbol"):
      window_symbol = settings.value(key)
      window_id = int(re.findall(r"^window_(\d+)_[^_]+$", key)[0])
      if window_id > window_id_counter:
        window_id_counter = window_id
      window = ChartWindow(window_symbol, window_id)
      logging.info(f"Showing Window with id {window_id}")
      window.applyConfig() # load windows' settings from config
      window.show()
      window.plotStock()
      windows.append(window)
  logging.info("Done Showing all windows")
  logging.info("Creating Tray Icon...")
  tray_icon = TrayIcon(app, windows)
  logging.info("Done Creating Tray Icon")
  sys.exit(app.exec())

if __name__ == '__main__':
  main()