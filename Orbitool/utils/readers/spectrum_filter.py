from typing import TypedDict


class SpectrumFilter(TypedDict):
    string: str
    polarity: str
    mass_range: str
    higher_energy_CiD: str
    scan: str