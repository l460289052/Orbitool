from dataclasses import asdict, dataclass
import json
import multiprocessing
import os
from pathlib import Path
import shutil
import subprocess
import sys
from traceback import format_exception, print_exc, print_exception
import traceback
import zipfile

import pytest

from Orbitool.version import VERSION
from utils import pyuic, setup


@dataclass
class Config:
    not_compile_once: bool = False
    compile: bool = True
    test: bool = True
    build: bool = True
    zip_file: bool = True
    multiprocess_upx: bool = True

    upx_dir: str = ""


CWD = Path.cwd()
CONFIG_PATH = Path("build-config.json")
DIST_DIR = Path("dist")
EXE_DIR = DIST_DIR / "Orbitool"
ZIP_PATH = DIST_DIR / \
    f"Orbitool-{VERSION.replace('.','_')}.zip"
START_SCRIPT = CWD / "utils/StartOrbitool.bat"
UPX_SUFFIX = {".exe", ".dll", ".pyd"}


def read_config():
    try:
        config = Config(**json.loads(CONFIG_PATH.read_text()))
        exists = True
    except:
        config = Config()
        exists = False
    not_compile_once = config.not_compile_once
    if config.compile and not_compile_once:
        config.not_compile_once = False
    CONFIG_PATH.write_text(json.dumps(asdict(config), indent=4))
    if config.compile and not_compile_once:
        config.compile = False

    return exists, config


def run_pyuic(config: Config):
    pyuic.pyuic(CWD / "Orbitool/UI")


def run_compile(config: Config):
    try:
        for pyd in (CWD / "Orbitool").glob("**/*.pyd"):
            print("removing pyd", pyd)
            pyd.unlink()
        setup.main(CWD / "Orbitool")
    except:
        print_exc()
        return False
    return True


def run_test(config: Config):
    ret = pytest.main(["-c", "pytest.ini"])
    if ret != 0:
        print("Test failed with code", ret)
        return False
    return True


def do_upx(upx_dir, file):
    try:
        os.system(f"{upx_dir}/upx --lzma -q {file}")
    except:
        print_exc()


def run_build(config: Config):
    if not config.upx_dir or not Path(config.upx_dir).exists():
        if not config.upx_dir:
            print("please provide upx path")
        else:
            print("cannot find upx path", config.upx_dir)
        return False
    if config.multiprocess_upx:
        # os.system(f"pyinstaller main.spec -y")
        cpu_count = multiprocessing.cpu_count()
        pool = multiprocessing.Pool(
            cpu_count - 2 if cpu_count > 2 else cpu_count)

        def files_iter():
            for file in EXE_DIR.glob("**/*"):
                if file.suffix in UPX_SUFFIX:
                    yield config.upx_dir, file  # has bug, maybe need to ignore some files
        pool.starmap_async(do_upx, files_iter(), error_callback=print_exc)
        pool.close()
        pool.join()
    else:
        os.system(f"pyinstaller main.spec --upx-dir {config.upx_dir} -y")
    TARGET = DIST_DIR / START_SCRIPT.name
    shutil.copyfile(START_SCRIPT, TARGET)
    return True


def run_package(config: Config):
    with zipfile.ZipFile(ZIP_PATH, 'w') as file:
        for path in EXE_DIR.glob("**/*"):
            print("write to zip files:", path)
            file.write(path, path.relative_to(DIST_DIR), zipfile.ZIP_DEFLATED)
        file.write(CWD / "utils/StartOrbitool.bat",
                   "StartOrbitool.bat", zipfile.ZIP_DEFLATED)

    subprocess.Popen(
        f'explorer /select,"{ZIP_PATH.absolute()}"')


if __name__ == "__main__":
    exists, config = read_config()
    if not exists:
        print("build-config.json was created, please check it\n and rerun this script to continue")
        exit()
    if config.compile:
        run_pyuic(config)
        if not run_compile(config):
            exit(-1)
    if config.test:
        if not run_test(config):
            exit(-1)
    if config.build:
        if not run_build(config):
            exit(-1)
    if config.zip_file:
        run_package(config)
