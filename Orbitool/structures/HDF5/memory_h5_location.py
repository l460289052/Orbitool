
class Dataset:
    def __init__(self, data):
        self.data = data

    def read_direct(self, target):
        target[:] = self.data

    @property
    def shape(self):
        return self.data.shape

    @property
    def dtype(self):
        return self.data.dtype


class Location(dict):
    def __init__(self):
        super().__init__()
        self.attrs = {}

    def create_dataset(self, key, data, *args, **kwargs):
        self[key] = Dataset(data)

    def create_group(self, key, *args, **kwargs):
        location = Location()
        self[key] = location
        return location
