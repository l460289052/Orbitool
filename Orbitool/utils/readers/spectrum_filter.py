from typing import TypedDict


class SpectrumFilter(TypedDict):
    string: str
    polarity: str
    mass_range: str
    higher_energy_CiD: str
    scan: str

def match(filter: SpectrumFilter, target_filter: SpectrumFilter):
    for key, value in target_filter.items():
        if filter.get(key, None) != value:
            return False
    return True