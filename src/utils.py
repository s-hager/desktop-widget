import os
import sys

def appDirectoryPath(file):
  if getattr(sys, 'frozen', False):
    # Running as compiled executable (e.g., PyInstaller)
    application_directory = os.path.dirname(sys.executable)
  else:
    # Running as a script
    application_directory = os.path.dirname(os.path.abspath(__file__))
  return os.path.join(application_directory, file)

def resourcePath(relative_path):
  # Get absolute path to resource, works for dev and for PyInstaller
  base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
  return os.path.join(base_path, relative_path)