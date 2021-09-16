from ...functions import binary_search
from typing import List, Tuple, Callable
from packaging.version import Version
from ..workspace import WorkSpace

start_versions: List[Tuple[Version, Callable]] = []


def register(version: str, func: Callable):
    version = Version(version)
    posi = binary_search.indexFirstBiggerThan(
        start_versions, version, method=lambda a, i: a[i][0])
    start_versions.insert(posi, (version, func))


def update(workspace: WorkSpace):
    version = Version(workspace.info.version)
    posi = binary_search.indexFirstNotSmallerThan(
        start_versions, version, method=lambda a, i: a[i][0])

    for version, updater in start_versions[posi:]:
        updater(workspace)

def need_update(workspace:WorkSpace):
    version = Version(workspace.info.version)
    posi = binary_search.indexFirstNotSmallerThan(
        start_versions, version, method=lambda a, i: a[i][0])
    if posi < len(start_versions):
        return True
