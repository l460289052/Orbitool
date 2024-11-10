from datetime import datetime
import json
from sys import hash_info
from h5py import File, Group
import numpy as np

def update(f: File):
    """
    to 2.5.3
    """
    OLD_KEY = "keys"
    NEW_KEY = "_keys"

    paths = ["data/raw_spectra", "data/calibrated_spectra", "data/time_series"]
    for p in paths:
        obj: Group= f[p]
        keys = obj.attrs[OLD_KEY]
        obj.create_dataset(NEW_KEY, data=keys)