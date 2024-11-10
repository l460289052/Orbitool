from dataclasses import dataclass
import logging
import logging.handlers
from sys import stdout
from .config import ROOT_PATH


LOG_PATH = ROOT_PATH / 'log.txt'
logLevel = "DEBUG"

formatter = logging.Formatter(
    "%(asctime)s -%(levelname)s- %(message)s")
log_file_handler = logging.handlers.TimedRotatingFileHandler(LOG_PATH, when="midnight", encoding='utf-8')
log_file_handler.setFormatter(formatter)
std_handler = logging.StreamHandler(stdout)
std_handler.setFormatter(formatter)
_logger = logging.getLogger("Orbitool")
_logger.setLevel(logLevel)
_logger.addHandler(log_file_handler)
_logger.addHandler(std_handler)

@dataclass
class _Logger:
    logger: logging.Logger

    def _flog(self, TAG: str, content: str):
        return f"[{TAG}] {content}"

    def d(self, TAG: str, content: str):
        """
        10
        """
        self.logger.debug(self._flog(TAG, content))

    def i(self, TAG: str, content: str):
        """
        20
        """
        self.logger.info(self._flog(TAG, content))

    def w(self, TAG: str, content: str):
        """
        30
        """
        self.logger.warning(self._flog(TAG, content))

    def error(self, TAG: str, content: str):
        """
        40
        """
        self.logger.error(self._flog(TAG, content))

    def exception(self, TAG: str, content: str):
        """
        40
        """
        self.logger.exception(self._flog(TAG, content))

    def critical(self, TAG: str, content: str):
        """
        50
        """
        self.logger.critical(self._flog(TAG, content))

logger = _Logger(_logger)