from PyQt6.QtCore import QSettings 

# own files:
from utils import appDirectoryPath

### --------------------------- Global Constants --------------------------- ###
settings = QSettings(appDirectoryPath("config.ini"), QSettings.Format.IniFormat)
window_id_counter = 0
windows = []
### ------------------------------------------------------------------------ ###