from collections import Counter, defaultdict
from math import nan
from typing import Any, DefaultDict, Dict, List, Literal, cast
from Orbitool.base.extra_type_handlers import JSONObject

from Orbitool.base.structure import BaseStructure
from Orbitool.utils.readers.spectrum_filter import SpectrumFilter

from .base import BaseInfo
from ..file import FileSpectrumInfo, PathList, PeriodItem


class FileTabInfo(BaseInfo):
    rtol: float = 1e-6
    spectrum_infos: List[FileSpectrumInfo] = []
    pathlist: PathList = PathList()
    periods: List[PeriodItem] = []
    """
            name  ->  { value  ->  count in files }
        Dict[str, Dict[str, int]]

        example:
            files_spectrum_filters["MassRange"]["50-750"] += 1
    """
    files_spectrum_filters: JSONObject = {}
    """
        name -> value
        Dict[str, str]
    """
    use_spectrum_filters: JSONObject = {}
    """
        name -> { key -> value }
        
        example:
            spectrum_scanstats_filters["TIC"]["=="] = 10000
            spectrum_scanstats_filters["TIC"][">="] = 10000
            spectrum_scanstats_filters["TIC"]["<="] = 10000
    """
    spectrum_scanstats_filters: JSONObject = {}

    def add_filter(self, filter: SpectrumFilter):
        current = self.getCastedFilesSpectrumFilters()
        for key, value in filter.items():
            counts = current.setdefault(key, {})
            if value in counts:
                counts[value] += 1
            else:
                counts[value] = 1

    def rm_filter(self, filter: SpectrumFilter):
        current = self.files_spectrum_filters
        for key, value in filter.items():
            current[key][value] -= 1
            if current[key][value] == 0:
                del current[key][value]
                if not current[key]:
                    del current[key]

    def getCastedFilesSpectrumFilters(self):
        return cast(Dict[str, Dict[str, int]], self.files_spectrum_filters)

    def getMostCommonValue_forFilter(self, filter: str):
        filters = self.getCastedFilesSpectrumFilters()
        assert filter in filters, f"{filter} not in file filters "
        return max(filters[filter].items(), key=lambda item: item[1])[0]

    def getCastedUsedSpectrumFilters(self):
        return cast(Dict[str, str], self.use_spectrum_filters)

    def getCastedScanstatsFilters(self):
        return cast(Dict[str, Dict[str, Any]], self.spectrum_scanstats_filters)
