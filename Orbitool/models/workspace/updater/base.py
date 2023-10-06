import h5py
from Orbitool.utils import binary_search
from typing import List, Tuple, Callable
from packaging.version import Version

start_versions: List[Tuple[Version, Callable]] = []


def register(version: str, func: Callable):
    version = Version(version)
    posi = binary_search.indexFirstBiggerThan(
        start_versions, version, method=lambda a, i: a[i][0])
    start_versions.insert(posi, (version, func))


def update(path: str):
    version = Version(get_version(path))
    posi = binary_search.indexFirstBiggerThan(
        start_versions, version, method=lambda a, i: a[i][0])

    for version, updater in start_versions[posi:]:
        with h5py.File(path, 'r+') as f:
            updater(f)
    set_version(path)


def need_update(version: str):
    version = Version(version)
    return version < start_versions[-1][0]


def get_version(path: str):
    with h5py.File(path, 'r') as f:
        return f["info"].attrs["version"]

def set_version(path:str):
    with h5py.File(path, 'r+') as f:
        f["info"].attrs["version"] = str(start_versions[-1][0])