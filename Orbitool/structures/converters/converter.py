from typing import Dict, Set


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


class VersionChainItem:
    __slots__ = ['front', 'version', 'next']

    def __init__(self, version=None) -> None:
        self.front = None
        self.version = version
        self.next = None


class _Converters:
    def __init__(self) -> None:
        self.converters: Dict[str, type] = {}
        self.chain: Dict[str, VersionChainItem] = None

    def register(self, converter: type):
        assert issubclass(converter, BaseConverter)
        self.converters[converter.version_from] = converter
        self.chain = None

    def generate_chain(self):
        chainBeginers: Dict[str, VersionChainItem] = {}
        chainEnders: Dict[str, VersionChainItem] = {}

        chain = {}
        for converter in self.converters.values():
            version_from = converter.version_from
            item = VersionChainItem(version_from)
            version_to = converter.version_to

            chain[version_from] = item
            chainEnders[version_to] = item
            chainBeginers[version_from] = item
            if version_from in chainEnders:
                chainItem = chainEnders.pop(version_from)
                chainBeginers.pop(version_from)
                chainItem.next = item
                item.front = chainItem
            if version_to in chainBeginers:
                chainItem = chainBeginers.pop(version_to)
                chainEnders.pop(version_to)
                chainItem.front = item
                item.next = chainItem

        if len(chainBeginers) > 1:
            converters = self.converters
            chains = []
            for item in chainBeginers.values():
                chain = []
                while item is not None:
                    converter = converters[item.version]
                    chain.append(
                        (converter.version_from, converter.version_to))
                    item = item.next
            raise VersionCheckError("Find more than 1 chain", chains)

        self.chain = chain

    def convert(self, h5file):
        if self.chain is None:
            self.generate_chain()
        version = BaseConverter.get_version(h5file)
        converters = self.converters
        item = self.chain[version]
        while item is not None:
            converter = converters[item.version]
            converter = converter()
            converter.convert(h5file)
            item = item.next

    def clear(self):
        self.converters.clear()
        self.chain = None


converter = _Converters()

register = converter.register
convert = converter.convert
clear = converter.clear
