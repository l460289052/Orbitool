import logging
import os
from datetime import timedelta
from pathlib import Path
from multiprocessing import cpu_count
from typing import List
from pydantic import BaseModel, Field
from .version import VERSION


class TempFile:
    prefixTimeFormat = r"orbitool_%Y%m%d%H%M%S_"
    tempPath = None


ROOT_PATH = Path(__file__).parent.parent

LOG_PATH = ROOT_PATH / 'log.txt'

logLevel = "DEBUG"

formatter = logging.Formatter(
    "\n%(asctime)s - %(filename)s - %(levelname)s \n %(message)s")
log_file_handler = logging.FileHandler(LOG_PATH, encoding='utf-8')
log_file_handler.setFormatter(formatter)
logger = logging.getLogger("Orbitool")
logger.setLevel(logLevel)
logger.addHandler(log_file_handler)

config_path = ROOT_PATH / "setting.json"

multi_cores = cpu_count() - 1
if multi_cores < 1:
    multi_cores = 1

class General(BaseModel):
    default_select: bool = True
    format_time: str = r"%Y-%m-%d %H:%M:%S"
    format_export_time: str = r"%Y%m%d_%H%M%S"
    multi_cores: int = multi_cores


class Debug(BaseModel):
    thread_block_gui: bool = False
    NO_MULTIPROCESS: bool = False


class _Setting(BaseModel):
    general: General = General()
    debug: Debug = Debug()

    test_timeout: int = 1
    time_delta: timedelta = timedelta(seconds=1)


    noise_formulas: List[str] = ["NO3-", "HNO3NO3-"]

    plot_refresh_interval: float = 1

    version: str = VERSION

    def save_setting(self):
        config_path.write_text(self.json(indent=4))

    def update_from(self, new_config: "_Setting"):
        for key in new_config.__fields__.keys():
            setattr(self, key, getattr(new_config, key))


if config_path.exists():
    setting = _Setting.parse_file(config_path)
else:
    setting = _Setting()

setting.general.multi_cores = max(min(setting.general.multi_cores, multi_cores), 1)
setting.save_setting()
