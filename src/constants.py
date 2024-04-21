from PyQt6.QtCore import QSettings

# own files:
from utils import appDirectoryPath, resourcePath

### --------------------------- Global Constants --------------------------- ###
settings = QSettings(appDirectoryPath("config.ini"), QSettings.Format.IniFormat)
# window_id_counter = 0
# windows = []
app_icon = resourcePath("./assets/icon.png")
locked_icon = resourcePath("./assets/locked.png")
unlocked_icon = resourcePath("./assets/unlocked.png")
### ------------------------------------------------------------------------ ###