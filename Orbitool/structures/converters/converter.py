from collections import deque
from typing import Dict, Set, Deque


class BaseConverter:
    version_to = None
    version_from = None

    def convert(self, h5file) -> None:
        self.check_version(h5file)

    @staticmethod
    def get_version(h5file) -> None:
        return h5file.attrs['version']

    def check_version(self, h5file):
        version = BaseConverter.get_version(h5file)
        pass


class VersionCheckError(Exception):
    pass


def generate_chain(maps: dict):
    beginers = maps.copy()
    enders = {v: k for k, v in maps.items()}

    chains = []

    while beginers:
        v_from = next(iter(beginers.keys()))
        v_to = beginers.pop(v_from)
        enders.pop(v_to)

        c = deque((v_from, v_to))

        while v_from in enders:
            v_from = enders.pop(v_from)
            beginers.pop(v_from)
            c.appendleft(v_from)
        while v_to in beginers:
            v_to = beginers.pop(v_to)
            enders.pop(v_to)
            c.append(v_to)
        chains.append(c)

    return chains


class _Converters:
    def __init__(self) -> None:
        self.converters: Dict[str, type] = {}
        self.chain: list = None
        self.chainMap: Dict[str, int] = None

    def register(self, converter: type):
        assert issubclass(converter, BaseConverter)
        self.converters[converter.version_from] = converter
        self.chain = None

    def generate_chain(self):
        chains = generate_chain(
            {c.version_from: c.version_to for c in self.converters})
        if len(chains) > 1:
            raise VersionCheckError("Find more than 1 chain", chains)

        self.chain = list(chains[0])
        self.chainMap = {c: i for i, c in enumerate(self.chain)}

    def convert(self, h5file):
        if self.chain is None:
            self.generate_chain()
        version = BaseConverter.get_version(h5file)
        converters = self.converters
        for version in self.chain[self.chainMap[version]:]:
            converter = converters[version]
            converter = converter()
            converter.convert(h5file)

    def clear(self):
        self.converters.clear()
        self.chain = None
        self.chainMap = None


converter = _Converters()

register = converter.register
convert = converter.convert
clear = converter.clear
