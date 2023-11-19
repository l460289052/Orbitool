from operator import getitem
from typing import Dict, Literal, TypedDict


class SpectrumFilter(TypedDict):
    string: str
    polarity: str
    mass: str
    CiD: str
    scan: str


class SpectrumStats(TypedDict):
    TIC: float

StatsFilters = Dict[str, Dict[Literal["==", "<=", ">="], float]]
"""
StatsFilters = Dict[str, Dict[Literal["==", "<=", ">="], float]]
"""


def filter_match(filter: SpectrumFilter, target_filter: SpectrumFilter):
    for key, value in target_filter.items():
        if filter.get(key, None) != value:
            return False
    return True


filter_headers = ["mass", "polarity", "CiD", "scan", "string"]
stats_header = ["TIC"]
stats_default_filter = ("?", 5000)


def filter_to_row(filter: SpectrumFilter):
    return (filter[key] for key in filter_headers)


def stats_to_row(stats: SpectrumStats):
    return (stats[key] for key in stats.keys())

def stats_match(stats: SpectrumStats, target_stats: StatsFilters):
    for key, item in target_stats.items():
        for op, value in item.items():
            match op:
                case "==":
                    if stats[key] != value: return False
                case "<=":
                    if stats[key] > value: return False
                case ">=":
                    if stats[key] < value: return False
    return True

