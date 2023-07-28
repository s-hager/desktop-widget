# desktop-widget

### activate venv (linux):
source venv/bin/activate

### activate venv (windows):
venv\Scripts\activate

### build exe with:
pyinstaller app.py --paths=./venv/lib/site-packages --onefile
pyinstaller app.py --onefile --paths=./venv/lib/site-packages --add-data "icon.ico;."

### then set console to false in app.spec and rebuild with
pyinsatller app.spec