from operator import getitem
from typing import TypedDict


class SpectrumFilter(TypedDict):
    string: str
    polarity: str
    mass: str
    CiD: str
    scan: str


class SpectrumStats(TypedDict):
    TIC: float


def match(filter: SpectrumFilter, target_filter: SpectrumFilter):
    for key, value in target_filter.items():
        if filter.get(key, None) != value:
            return False
    return True


filter_headers = ["mass", "polarity", "CiD", "scan", "string"]
stats_header = ["TIC"]
stats_default_filter = ("?", 5000)


def filter_to_row(filter: SpectrumFilter):
    return (filter[key] for key in filter_headers.keys())


def stats_to_row(stats: SpectrumStats):
    return (stats[key] for key in stats.keys())
