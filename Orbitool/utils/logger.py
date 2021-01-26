import os
import enum
import sqlite3
import datetime
import threading
import queue
from Orbitool import config


class LogLevel(enum.Enum):
    NOTSET = 0
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


_logLevel = 0


def setLogLevel(logLevel: LogLevel):
    assert isinstance(logLevel, LogLevel)
    global _logLevel
    _logLevel = logLevel.value


class _LogListener:
    def __init__(self):
        PATH = config.logPath
        new = not os.path.exists(PATH)
        db = sqlite3.connect(PATH)
        if new:
            self._initializeSQL(db)
        self.sqlite3 = db

    def _initializeSQL(self, db: sqlite3.connect):
        with db as cursor:
            cursor.execute("""
            CREATE TABLE logs(
                Time    DATETIME NOT NULL,
                Level   INT     NOT NULL,
                Content TEXT    NOT NULL,
                Trackback   TEXT,
                Otherinfos  TEXT);""")

    def _log(self, record: tuple):
        with self.sqlite3 as cursor:
            try:
                cursor.execute(
                    "INSERT INTO logs VALUES(?,?,?,?,?)", record)
            except sqlite3.IntegrityError:
                pass


def _LogListen(q: queue.Queue):
    listener = _LogListener()
    try:
        while True:
            record = q.get(timeout=0.1)
            if record is None:
                break
            listener._log(record)
    except queue.Empty:
        pass
        # print("log stop")


class _LoggerSender:
    def __init__(self):
        self.queue = queue.Queue()
        self.listenerThread: threading.Thread = None

    @property
    def isListen(self):
        if self.listenerThread is None or not self.listenerThread.is_alive():
            return False
        return True

    def beginListen(self):
        self.listenerThread = threading.Thread(
            target=_LogListen, args=(self.queue,))
        self.listenerThread.start()

    def _log(self, level: int, content: str, traceback: str, otherinfos: str):
        if level < _logLevel:
            return
        if not self.isListen:
            self.beginListen()
        record = (datetime.datetime.now().isoformat(),
                  level, content, traceback, otherinfos)
        self.queue.put(record)

    def debug(self, content: str, otherinfos=None, traceback: str = None):
        self._log(LogLevel.DEBUG.value, content, traceback, otherinfos)

    def info(self, content: str, otherinfos=None, traceback: str = None):
        self._log(LogLevel.INFO.value, content, traceback, otherinfos)

    def warning(self, content: str, traceback: str = None, otherinfos=None):
        self._log(LogLevel.WARNING.value, content, traceback, otherinfos)

    def error(self, content: str, traceback, otherinfos=None):
        self._log(LogLevel.ERROR.value, content, traceback, otherinfos)

    def critical(self, content: str, traceback, otherinfos=None):
        self._log(LogLevel.CRITICAL.value, content, traceback, otherinfos)

    def __del__(self):
        self.queue.put(None)
        if self.listenerThread is not None:
            self.listenerThread.join()


_logger = _LoggerSender()
debug = _logger.debug
info = _logger.info
warning = _logger.warning
error = _logger.error
critical = _logger.critical
