from __future__ import annotations
from typing import Union
import numpy as np
from . import group, descriptor


class List(group.Group):
    h5_type = descriptor.RegisterType("LightList")
    sequence = descriptor.SmallNumpy()
    max_index = descriptor.Int()

    index_dtype = np.dtype('S')

    def initialize(self):
        self.max_index = -1
        self.sequence = np.empty(0, dtype=self.index_dtype)

    def __getitem__(self, index: Union[int, slice]):
        true_index = self.sequence[index]
        attrs = self.location.attrs
        if not isinstance(index, slice):
            return attrs[true_index]
        return [attrs[index] for index in true_index]

    def append(self, item):
        self.max_index += 1
        index = str(self.max_index).encode('ascii')
        self.sequence = np.concatenate((self.sequence, (index,)))
        self.location.attrs[index] = item

    def __delitem__(self, index: Union[int, slice]):
        sequence = self.sequence
        slt = np.ones_like(sequence, dtype=bool)
        slt[index] = False
        attrs = self.location.attrs
        for ind in sequence[~slt]:
            del attrs[ind]
        self.sequence = sequence[slt]

    def insert(self, index, item):
        sequence = self.sequence
        part1 = sequence[:index]
        part2 = sequence[index:]
        self.max_index += 1
        index = str(self.max_index).encode('ascii')
        self.sequence = np.concatenate((part1, (index,), part2))
        self.location.attrs[index] = item

    def __iter__(self):
        attrs = self.location.attrs
        for index in self.sequence:
            yield attrs[index]

    def copy_from(self, another: List):
        super().copy_from(another)
        attrs = self.location.attrs
        aattrs = another.location.attrs
        for index in another.sequence:
            attrs[index] = aattrs[index]
