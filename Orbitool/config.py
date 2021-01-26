import os
DEBUG = False

if DEBUG:
    from PyQt5 import QtWidgets
    QtWidgets.QMessageBox.information(None, 'info', 'DEBUG')


class TempFile:
    prefixTimeFormat = r"orbitool_%Y%m%d%H%M%S_"
    tempPath = None


logPath = os.path.join(os.path.dirname(
    os.path.dirname(__file__)), 'log.sqlite3')
logLevel = "DEBUG"