import os
import logging
from multiprocessing import cpu_count

DEBUG = False

if DEBUG:
    from PyQt5 import QtWidgets
    QtWidgets.QMessageBox.information(None, 'info', 'DEBUG')

timeFormat = r"%Y-%m-%d %H:%M:%S"

class TempFile:
    prefixTimeFormat = r"orbitool_%Y%m%d%H%M%S_"
    tempPath = None


rootPath = os.path.dirname(os.path.dirname(__file__))

logPath = os.path.join(rootPath, 'log.txt')

logLevel = "DEBUG" if DEBUG else "WARNING"

log_file_handler = logging.FileHandler(logPath, encoding='utf-8')
logging.root.handlers.clear()
logging.basicConfig(format="\n%(asctime)s - %(filename)s - %(levelname)s \n %(message)s",
                    level=logLevel, handlers=[log_file_handler])


multi_cores = cpu_count() - 1
if multi_cores <= 0:
    multi_cores = 1

test_timeout = 0.1 # second