import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import PyQt5

from BlurWindow.blurWindow import GlobalBlur

if sys.platform == 'darwin':
    from AppKit import NSMakeRect, NSVisualEffectView, NSVisualEffectStateActive, \
                      NSVisualEffectMaterialUltraDark, NSVisualEffectBlendingModeBehindWindow, \
                      NSFullSizeContentViewWindowMask, NSAppearance, NSAppearanceNameVibrantDark, NSViewWidthSizable, NSViewHeightSizable, NSWindowBelow
    import objc

class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        #self.setAttribute(Qt.WA_TranslucentBackground)
        #self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        #self.setWindowFlag(Qt.FramelessWindowHint)
        #self.resize(500, 400)

        #self.setStyleSheet("background-color: rgba(0, 0, 0, 0)")  
        if sys.platform == 'darwin':
            frame = NSMakeRect(0, 0, self.width(), self.height())
            view = objc.objc_object(c_void_p=self.winId().__int__())

            visualEffectView = NSVisualEffectView.new()
            visualEffectView.setAutoresizingMask_(NSViewWidthSizable|NSViewHeightSizable)
            visualEffectView.setWantsLayer_(True)
            visualEffectView.setFrame_(frame)
            visualEffectView.setState_(NSVisualEffectStateActive)
            visualEffectView.setMaterial_(NSVisualEffectMaterialUltraDark)
            visualEffectView.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
            visualEffectView.setWantsLayer_(True)

            self.setAttribute(Qt.WA_TranslucentBackground, True)

            window = view.window()
            content = window.contentView()

            container = QMacCocoaViewContainer(0, self)
            content.addSubview_positioned_relativeTo_(visualEffectView, NSWindowBelow, container)

            window.setTitlebarAppearsTransparent_(True)
            window.setStyleMask_(window.styleMask() | NSFullSizeContentViewWindowMask)

            appearance = NSAppearance.appearanceNamed_(NSAppearanceNameVibrantDark)
            window.setAppearance_(appearance)   

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = MainWindow()
    #GlobalBlur(QWidget=mw,HWND=mw.winId(),Dark=True)
    mw.show()
    sys.exit(app.exec_())