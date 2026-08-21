import sys
import os
import platform

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from frontend.main_window import MainWindow, ICON_APP


def main():
    if platform.system() == "Windows":
        import ctypes
        try:
            myappid = "FocusFlow"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            print(f"[AppUserModelID] Error: {e}")

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(ICON_APP))
    app.setApplicationName("FocusFlow")
    app.setApplicationDisplayName("FocusFlow")
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
