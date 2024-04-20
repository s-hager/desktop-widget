from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QIcon, QAction, QCursor
import logging
import re

# own files:
from settings_window import SettingsWindow
from chart_window import ChartWindow
# own variables:
from config import *
from constants import *

class TrayIcon:
  def __init__(self, app):
    self.window_id_counter = 0
    self.windows = []
    self.app = app
    all_keys = settings.allKeys()
    for i, key in enumerate(all_keys):
      if key.startswith("window_") and key.endswith("_symbol"):
        self.loadChartFromConfig(key)
    logging.info("Done Showing all windows")

    # Ensure only one settings window exists at a time:
    self.clearSettingsReference()
    # Create the system tray icon
    self.tray_icon = QSystemTrayIcon(self.app)
    self.tray_icon.setIcon(QIcon(app_icon))
    self.tray_icon.setToolTip(app_name)
    # self.tray_icon.setStyleSheet("QSystemTrayIcon {background-color: #333333; color: #FFFFFF;}")

    # Create a menu for the system tray icon
    self.tray_menu = QMenu()
    self.open_settings = QAction("Open Settings", self.app)
    self.quit_action = QAction("Quit", self.app)
    # self.enable_startup_action = QAction("Enable Launch on Startup", self.app)
    # self.disable_startup_action = QAction("Disable Launch on Startup", self.app)

    # self.enable_startup_action.setCheckable(True)
    # self.enable_startup_action.setChecked(True) # TODO merge actions into 1 that is either checked or unchecked

    # show settings if no windows in config
    if not self.windows:
      self.openSettingsWindow()

    self.open_settings.triggered.connect(self.openSettingsWindow)
    self.quit_action.triggered.connect(self.quitApp)
    # self.enable_startup_action.triggered.connect(self.enableLaunchOnStartup)
    # self.disable_startup_action.triggered.connect(self.disableLaunchOnStartup)
    self.tray_menu.addAction(self.open_settings)
    self.tray_menu.addAction(self.quit_action)
    # self.tray_menu.addAction(self.enable_startup_action)
    # self.tray_menu.addAction(self.disable_startup_action)

    # Add the menu to the system tray icon
    self.tray_icon.setContextMenu(self.tray_menu)

    self.tray_icon.activated.connect(self.clickHandler)

    # Show the system tray icon
    self.tray_icon.show()

  def loadChartFromConfig(self, key):
    window_symbol = settings.value(key).upper()
    window_id = int(re.findall(r"^window_(\d+)_[^_]+$", key)[0])
    if window_id > self.window_id_counter:
      self.window_id_counter = window_id
    window = ChartWindow(self, window_symbol, window_id)
    logging.info(f"Showing Window with id {window_id}")
    window.applyConfig() # load windows' settings from config
    window.show()
    window.plotStock()
    self.windows.append(window)

  def quitApp(self):
    logging.info("Quitting Application")
    QCoreApplication.quit()

  def clickHandler(self, reason):
    if reason == QSystemTrayIcon.ActivationReason.Trigger: # left click
      logging.info("Tray Icon was left clicked")
      self.openSettingsWindow()
    elif reason == QSystemTrayIcon.ActivationReason.Context: # right click
      logging.info("Tray Icon was right clicked")
      self.moveMenuToCursor()

  def moveMenuToCursor(self):
    cursor_position = QCursor.pos()
    self.tray_menu.move(cursor_position)

  def clearSettingsReference(self):
    self.settings_window = None

  def openSettingsWindow(self):
    if self.settings_window is None:
      self.settings_window = SettingsWindow(self)
      self.settings_window.close_settings_signal.connect(self.clearSettingsReference)
      self.settings_window.show()
      self.settings_window.activateWindow()
    else:
      # If Settings Window is already open, bring it to the front of all windows
      logging.info("Settings Window Instance already exists, showing and bringing it to front")
      self.settings_window.show()
      self.settings_window.activateWindow()
      # QMessageBox.critical(self, "Error", "A Settings Window is already open.")