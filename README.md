# desktop-widget

### activate venv (linux):
source venv/bin/activate

### activate venv (windows):
venv\Scripts\activate

### build exe with:
`pyinstaller app.py --paths=./venv/lib/site-packages --onefile`

`pyinstaller app.py --onefile --paths=./venv/lib/site-packages --add-data "icon.ico;."`

`pyinstaller app.py --onefile --paths=./venv/lib/site-packages --add-data "icon.png;." --add-data "locked.png;." --add-data "unlocked.png;."`

`pyinstaller app.py --onefile --paths=./venv/lib/site-packages --icon=icon.png --add-data "icon.png;." --add-data "locked.png;." --add-data "unlocked.png;."`

`pyinstaller app.py --onefile --paths=./venv/lib/site-packages --name=StockWidget --icon=icon.png --add-data "icon.png;." --add-data "locked.png;." --add-data "unlocked.png;."`

`pyinstaller app.py --onefile --noconsole --paths=./venv/lib/site-packages --name=StockWidget --icon=icon.png --add-data "icon.png;." --add-data "locked.png;." --add-data "unlocked.png;."`

`pyinstaller main.py --onefile --noconsole --paths=./venv/lib/site-packages --name=StockWidget --icon=icon.png --add-data "icon.png;." --add-data "locked.png;." --add-data "unlocked.png;."`

### then rebuild with
pyinstaller app.spec
pyinstaller StockWidget.spec

### Auto Launch on System Start
Autostart adds windows registry key to 

```Computer\HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run```

if running as .exe

pyqtgraph fix cut off x axis labels:
https://stackoverflow.com/questions/69816567/pyqtgraph-cuts-off-tick-labels-if-showgrid-is-called

pyqtgraph examples:
$ python -m pyqtgraph.examples