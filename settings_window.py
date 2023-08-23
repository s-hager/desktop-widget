from PyQt6.QtWidgets import (QMainWindow, QApplication, QLabel, QWidget, 
                             QVBoxLayout, QSizePolicy, QCheckBox, 
                             QLineEdit, QPushButton, QHBoxLayout, QMessageBox)
from PyQt6.QtCore import QSize, pyqtSignal
from PyQt6.QtGui import QIcon
import sys
if 'nt' in sys.builtin_module_names:
  import winreg as reg
import functools
import logging

# own files:
from utils import resourcePath
from chart_window import ChartWindow
from chart_settings_window import ChartSettingsWindow
# own variables:
from config import *
from constants import *

class SettingsWindow(QMainWindow):
  close_settings_signal = pyqtSignal()
  def __init__(self, windows, parent=None):
    super().__init__(parent)
    if debug:
      logging.info("Creating Settings Object")
    self.windows = windows
    self.setWindowTitle("Settings")
    self.setWindowIcon(QIcon(app_icon))
    # self.setGeometry(100, 100, 300, 200)
    self.layout = QVBoxLayout()

    new_stock_layout = QHBoxLayout()
    self.textbox = QLineEdit(self)
    self.button_new_window = QPushButton("Add New Window", self)
    self.launch_on_startup_checkbox = QCheckBox("Launch Application on Startup")

    self.textbox.setPlaceholderText("Stock Symbol")
    self.textbox.returnPressed.connect(lambda: self.button_new_window.click())
    new_stock_layout.addWidget(self.textbox)
    
    self.button_new_window.clicked.connect(self.createNewChartWindow)
    new_stock_layout.addWidget(self.button_new_window)
    self.layout.addLayout(new_stock_layout)

    launch_on_startup_stored_value = settings.value("launch_on_startup", False, type=bool)

    self.launch_on_startup_checkbox.setChecked(launch_on_startup_stored_value)
    self.launch_on_startup_checkbox.clicked.connect(self.launchOnStartupChanged)
    self.layout.addWidget(self.launch_on_startup_checkbox)

    self.settings_stock_layouts = []
    self.addOpenWindows()

    central_widget = QWidget()
    central_widget.setLayout(self.layout)
    self.setCentralWidget(central_widget)

    # Set the window's size to a fraction of the screen's size
    screen_size = QApplication.primaryScreen().size()  # Get the screen's size
    fraction_of_screen = 0.3  # Set the fraction of the screen size you want the window to occupy
    size_relative_to_screen = QSize(int(screen_size.width() * fraction_of_screen),
                                    int(0))
    self.resize(size_relative_to_screen)

  def addOpenWindows(self):
    # self.clearLayout(self.window_layout)
    for window in self.windows:
      # Add the QHBoxLayout for this window to the main QVBoxLayout
      new_settings_stock_object = self.SettingsStockLayout(self, window)
      self.settings_stock_layouts.append(new_settings_stock_object)
      self.layout.addLayout(new_settings_stock_object.getLayout())

    # previous_old_id = None
    # previous_new_id = None
    # for i, key in enumerate(settings.allKeys()):
    #   if key.startswith(f"window_"):
    #     # logging.info(key)
    #     # logging.info(int(re.findall(r"^window_(\d+)_[^_]+$", key)[0]))
    #     value_variable = str(re.findall(r"^window_\d+_(.*)$", key)[0])
    #     key_id = int(re.findall(r"^window_(\d+)_[^_]+$", key)[0])
    #     if not previous_old_id:
    #       previous_old_id = key_id
    #       previous_new_id = i
    #       settings.setValue(f"window_{i}_{value_variable}", settings.value)
    #     if previous_old_id == key_id:
    #       settings.setValue(f"window_{previous_new_id}_{value_variable}", settings.value)

  def createNewChartWindow(self):
    global window_id_counter
    # self.clearLayout(self.window_layout)
    # self.addOpenWindows()
    stock_symbol = self.textbox.text().strip().upper()
    if not stock_symbol:
      QMessageBox.critical(self, "Error", "Stock Symbol cannot be empty.")
    else:
      self.textbox.clear() # clear user input from textbox
      window_id = window_id_counter
      settings.setValue(f"window_{window_id}_symbol", stock_symbol)
      window_id_counter += 1
      new_window = ChartWindow(stock_symbol)
      new_window.show()
      new_window.plotStock()
      windows.append(new_window)
      new_settings_stock_object = self.SettingsStockLayout(self, new_window)
      self.settings_stock_layouts.append(new_settings_stock_object)
      self.layout.addLayout(new_settings_stock_object.getLayout())

  class SettingsStockLayout(QHBoxLayout):
    def __init__(self, settings, window, parent=None):
      super().__init__(parent)
      self.settings = settings
      self.window = window
      self.window_id = window.window_id
      self.stock_symbol = window.stock_symbol
      self.clearChartSettingsWindowReference()

      # Create a QHBoxLayout for each window label and button
      self.window_layout = QHBoxLayout()
      
      # Add the label containing the stock symbol to the layout
      label = QLabel(self.stock_symbol)
      self.window_layout.addWidget(label)

      self.lock_button = QPushButton()
      self.lock_button.setIcon(QIcon(resourcePath("locked.png")))
      self.lock_button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
      self.lock_button.clicked.connect(self.toggleLock)
      # Add a button next to the label
      if debug:
        settings_button = QPushButton(f"{self.stock_symbol} Settings id:{self.window_id}")
      else:
        settings_button = QPushButton(f"{self.stock_symbol} Settings")
      settings_button.clicked.connect(self.openChartSettingsWindow)

      delete_button = QPushButton(f"Delete {self.stock_symbol}")
      delete_button.clicked.connect(functools.partial(self.deleteChartWindow))
      
      self.window_layout.addWidget(self.lock_button)
      self.window_layout.addWidget(settings_button)
      self.window_layout.addWidget(delete_button)

    def clearChartSettingsWindowReference(self):
      self.chart_settings_window = None

    def openChartSettingsWindow(self):
      if self.chart_settings_window is None:
        self.chart_settings_window = ChartSettingsWindow(self, self.window)
        self.chart_settings_window.show()
        self.chart_settings_window.activateWindow()
      else:
        # If Window is already open, bring it to the front of all windows
        if debug:
          logging.info(f"Chart Settings Window Instance for {self.window_id} already exists, showing and bringing it to front")
        self.chart_settings_window.show()
        self.chart_settings_window.activateWindow()

    def toggleLock(self):
      self.window.drag_resize = not self.window.drag_resize
      if self.window.drag_resize:
        if debug:
          logging.info(f"Unlocking Window with id {self.window_id}")
        self.lock_button.setIcon(QIcon(resourcePath("unlocked.png")))
        self.window.showResizeGrips()
        self.window.positionGrips()
        self.window.setFixedSize(16777215, 16777215) # reset constraints set by setFixedSize() cant get QWIDGETSIZE_MAX to work
        self.window.central_widget.setStyleSheet("QWidget#central_widget { border: 2px solid yellow; }") # yellow border to show unlocked status
      else:
        if debug:
          logging.info(f"Locking Window with id {self.window_id}")
          self.window.central_widget.setStyleSheet("border: 1px solid red;") # add debug border again
        else:
          self.window.central_widget.setStyleSheet("QWidget#central_widget { }") # remove border
        self.lock_button.setIcon(QIcon(resourcePath("locked.png")))
        self.window.savePositionAndSize()
        self.window.hideResizeGrips()
        self.window.setFixedSize(self.window.size())

    def getLayout(self):
      return self.window_layout

    def deleteChartWindow(self):
      if debug:
        logging.info(f"Deleting window {self.window_id} with symbol {self.window.stock_symbol}")
      all_keys = settings.allKeys()
      # logging.info(all_keys)
      for key in all_keys:
        if key.startswith(self.window_id):
          if debug:
            logging.info(f"Removing {key} with value {settings.value(key)} from config")
          settings.remove(key)
      self.window.close()
      if debug:
        logging.info("Closed window")
      # remove layout from settings window
      self.deleteLayout()
      # Remove the instance from settings_stock_layouts list
      if self in self.settings.settings_stock_layouts:
        self.settings.settings_stock_layouts.remove(self)

    def deleteLayout(self):
      # Remove all widgets from the layout
      while self.window_layout.count():
        item = self.window_layout.takeAt(0)
        widget = item.widget()
        if widget:
          widget.deleteLater()

      # Delete the layout itself
      self.window_layout.deleteLater()

  def launchOnStartupChanged(self, state):
    # TODO save state
    settings.setValue("launch_on_startup", state)

    if state: # Checkbox is checked
      self.enableLaunchOnStartup()
    else:
      self.disableLaunchOnStartup()
  
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
          logging.info(f"Successfully added to startup. Path: {app_path}")
      except Exception as e: # TODO Handle exception in gui
        if debug:
          logging.info(f"Failed to add to startup. Error: {str(e)}")
        QMessageBox.critical(self, "Error", "Failed to add to startup.")
    else:
      # if debug:
        logging.info("Not running .exe")

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
            logging.info("Successfully removed from startup.")
        else:
          if debug:
            logging.info("The registry value does not exist, nothing to remove.")

        reg.CloseKey(open_key)
      except Exception as e:
        if debug:
          logging.info(f"Failed to remove from startup. Error: {str(e)}")
        QMessageBox.critical(self, "Error", "Failed to remove from startup.")
    else:
      # if debug:
        logging.info("Not running .exe")

  def exeFilePath(self):
    if getattr(sys, 'frozen', False):
      # Running as an executable (compiled with PyInstaller)
      return sys.executable # returns "D:\Personal\Privat\Programming\desktop-widget\dist\app.exe"
    else:
      # Running as a regular Python script
      # return sys.argv[0] # returns ".\app.py"
      return False

  def closeEvent(self, event):
    # lock window positions and sizes if unlocked
    for settings_stock_layout in self.settings_stock_layouts:
      if settings_stock_layout.window.drag_resize:
        settings_stock_layout.toggleLock()
    
    # Overriding closeEvent to hide the window instead of closing it
    # self.hide()
    self.destroy()
    event.ignore() # ignore close event (would cause program to exit)
    if debug:
      logging.info("Closed Settings")
    self.close_settings_signal.emit()  # Emit custom signal
    # super().closeEvent(event)