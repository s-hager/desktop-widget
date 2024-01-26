# brew install create-dmg
#!/bin/sh
# Create a folder (named dmg) to prepare our DMG in (if it doesn't already exist).
mkdir -p dist/dmg
# Empty the dmg folder.
rm -r dist/dmg/*
# Copy the app bundle to the dmg folder.
cp -r "dist/StockWidget.app" dist/dmg
# If the DMG already exists, delete it.
test -f "dist/StockWidget.dmg" && rm "dist/StockWidget.dmg"
create-dmg \
  --volname "StockWidget" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "StockWidget.app" 175 120 \
  --hide-extension "StockWidget.app" \
  --app-drop-link 425 120 \
  "dist/StockWidget.dmg" \
  "dist/dmg/"