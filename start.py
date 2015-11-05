import sys

from PyQt5.QtWidgets import (QApplication, QMessageBox, QSystemTrayIcon)
from osfoffline.application.main import OSFApp


def start():
    app = QApplication(sys.argv)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(
            None,
            "Systray",
            "Could not detect a system tray on this system"
        )
        sys.exit(1)

    QApplication.setQuitOnLastWindowClosed(False)

    osf = OSFApp()
    osf.start()

    osf.hide()
    app.exec_()


if __name__ == "__main__":
    start()