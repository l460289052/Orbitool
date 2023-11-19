from datetime import datetime
import json
from sys import hash_info
from h5py import File, Group
import numpy as np


def update(f: File):
    """
    to 2.5.2
    """

    path = "info/file_tab/spectrum_infos"

    d = f[path][()]
    if len(d) == 0:
        return
    del f[path]
    new_filter = json.dumps(
        dict(polarity=str(d[0]["polarity"])), ensure_ascii=False)
    new_filter_dtype = f"S{len(new_filter)}"
    new_dtype = np.dtype(
        [('start_time', '<i8'), ('end_time', '<i8'), ('path', d.dtype['path']),
         ('filter', new_filter_dtype), ('average_index', '<i8')]
    )
    new_dataset = f.create_dataset(path, d.shape, new_dtype)
    for col in ["start_time", "end_time", "path", "average_index"]:
        new_dataset[col] = d[col]
    new_dataset["filter"] = [new_filter.encode()] * len(d)
