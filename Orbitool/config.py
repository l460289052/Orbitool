import logging
import os
from datetime import timedelta
from multiprocessing import cpu_count

from pydantic import BaseModel


DEBUG = False
NO_MULTIPROCESS = False

timeFormat = r"%Y-%m-%d %H:%M:%S"
exportTimeFormat = r"%Y%m%d_%H%M%S"


class TempFile:
    prefixTimeFormat = r"orbitool_%Y%m%d%H%M%S_"
    tempPath = None


rootPath = os.path.dirname(os.path.dirname(__file__))

logPath = os.path.join(rootPath, 'log.txt')

logLevel = "DEBUG" if DEBUG else "WARNING"

formatter = logging.Formatter(
    "\n%(asctime)s - %(filename)s - %(levelname)s \n %(message)s")
log_file_handler = logging.FileHandler(logPath, encoding='utf-8')
log_file_handler.setFormatter(formatter)
logger = logging.getLogger("Orbitool")
logger.setLevel(logLevel)
logger.addHandler(log_file_handler)


multi_cores = cpu_count()
if multi_cores <= 0:
    multi_cores = 1

test_timeout = 0.1  # second

time_delta = timedelta(seconds=1)

default_select = True  # if True, will select first row

noise_formulas = ["NO3-", "HN2O6-"]

plot_refresh_interval = timedelta(seconds=1)
