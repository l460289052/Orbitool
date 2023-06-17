from string import digits, ascii_uppercase
import h5py
from .utils import move_to, create_group


def update(path: str):
    """
    to 2.4.3
    """

    with h5py.File(path, 'r+') as f:
        source = "info/time_series_tab/series"
        target = "data/time_series"
        move_to(f, source, target)
        create_group(target)
        f[target].attrs["keys"] = sorted(list(map(int, f[target].keys())))
        series: h5py.Group
        for series in f[target].values():
            series.attrs["range_sum"] = False
            tag:str = series.attrs.pop("tag")
            if "-" in tag:
                continue
            if tag[0] in digits:
                continue
            if tag[0] in ascii_uppercase and " " not in tag:
                series.attrs["formulas"] = tag
