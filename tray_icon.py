from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QIcon, QAction, QCursor
import logging

# own files:
from settings_window import Settings
from utils import resourcePath
# own variables:
from config import *

class TrayIcon:
  def __init__(self, app, windows):
    self.app = app
    self.windows = windows
    # Ensure only one settings window exists at a time:
    self.settings_window = None
    # Create the system tray icon
    self.tray_icon = QSystemTrayIcon(self.app)
    self.tray_icon.setIcon(QIcon(resourcePath("icon.png")))
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
    if not windows:
      self.showSettingsWindow()

    self.open_settings.triggered.connect(self.showSettingsWindow)
    self.quit_action.triggered.connect(lambda: QCoreApplication.quit())
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

  def clickHandler(self, reason):
    if reason == QSystemTrayIcon.ActivationReason.Trigger: # left click
      if debug:
        logging.info("Tray Icon was left clicked")
      self.showSettingsWindow()
    elif reason == QSystemTrayIcon.ActivationReason.Context: # right click
      if debug:
        logging.info("Tray Icon was right clicked")
      self.moveMenuToCursor()

  def moveMenuToCursor(self):
    cursor_position = QCursor.pos()
    self.tray_menu.move(cursor_position)

  def clear_settings_reference(self):
    self.settings_window = None

  def showSettingsWindow(self):
    if self.settings_window is None:
      self.settings_window = Settings(self.windows)
      self.settings_window.close_settings.connect(self.clear_settings_reference)
      self.settings_window.show()
      self.settings_window.activateWindow()
    else:
      # If Settings Window is already open, bring it to the front of all windows
      if debug:
        logging.info("Settings Window Instance already exists, showing and bringing it to front")
      self.settings_window.show()
      self.settings_window.activateWindow()
      # QMessageBox.critical(self, "Error", "A Settings Window is already open.")