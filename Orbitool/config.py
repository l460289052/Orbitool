import logging
import os
from datetime import timedelta
from multiprocessing import cpu_count
from typing import List
from dataclasses import dataclass, field


class TempFile:
    prefixTimeFormat = r"orbitool_%Y%m%d%H%M%S_"
    tempPath = None


rootPath = os.path.dirname(os.path.dirname(__file__))

logPath = os.path.join(rootPath, 'log.txt')

logLevel = "DEBUG"

formatter = logging.Formatter(
    "\n%(asctime)s - %(filename)s - %(levelname)s \n %(message)s")
log_file_handler = logging.FileHandler(logPath, encoding='utf-8')
log_file_handler.setFormatter(formatter)
logger = logging.getLogger("Orbitool")
logger.setLevel(logLevel)
logger.addHandler(log_file_handler)


@dataclass
class _Config:
    DEBUG: bool = False
    NO_MULTIPROCESS: bool = False

    format_time: str = r"%Y-%m-%d %H:%M:%S"
    format_export_time: str = r"%Y%m%d_%H%M%S"

    multi_cores: int = field(default_factory=cpu_count)

    test_timeout: float = .1
    time_delta: timedelta = timedelta(seconds=1)

    default_select: bool = True

    noise_formulas: List[str] = field(
        default_factory=lambda: ["NO3-", "HNO3NO3-"])

    plot_refresh_interval: float = 1


_config = _Config()


def get_config() -> _Config:
    return _config


def set_config(config):
    global _config
    _config = config
