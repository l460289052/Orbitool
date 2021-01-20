import numpy as np


class Location(dict):
    def __init__(self):
        super().__init__()
        self.attrs = {}

    def create_dataset(self, name, shape=None, dtype=None, data=None, *args, **kwargs):
        assert not (shape is None and dtype is None and data is None)
        if shape is None:
            if dtype is None:
                self[name] = np.array(data)
            if data is None:
                self[name] = np.empty((0,), dtype=dtype)
        elif dtype is None:
            assert data is not None
            self[name] = np.empty(shape, dtype=np.array(data).dtype)
            self[name][:len(data)] = data
        else:
            self[name] = np.empty(shape, dtype=dtype)
            if data is not None:
                self[name][:len(data)] = data

    def create_group(self, key, *args, **kwargs):
        location = Location()
        self[key] = location
        return location
