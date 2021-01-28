import os
import logging
DEBUG = False

if DEBUG:
    from PyQt5 import QtWidgets
    QtWidgets.QMessageBox.information(None, 'info', 'DEBUG')


class TempFile:
    prefixTimeFormat = r"orbitool_%Y%m%d%H%M%S_"
    tempPath = None


rootPath = os.path.dirname(os.path.dirname(__file__))

logPath = os.path.join(rootPath, 'log.txt')

logLevel = "DEBUG" if DEBUG else "WARNING"

log_file_handler = logging.FileHandler(logPath, encoding='utf-8')
logging.basicConfig(format=r"%(asctime)s - %(filename)s - %(levelname)s \n %(message)s",
                    level=logLevel, handlers=[log_file_handler])
