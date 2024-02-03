import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from BlurWindow.blurWindow import GlobalBlur

class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setAttribute(Qt.WA_TranslucentBackground)
        #self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        #self.setWindowFlag(Qt.FramelessWindowHint)
        self.resize(500, 400)

        self.setStyleSheet("background-color: rgba(0, 0, 0, 0)")  
         
        label = QLabel('blur_macos_lib', self)
        label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)  # Center horizontally and vertically
        # Use a layout to manage the position of the QLabel
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addStretch(1)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = MainWindow()
    GlobalBlur(QWidget=mw,HWND=mw.winId(),Dark=True)
    mw.show()
    sys.exit(app.exec_())