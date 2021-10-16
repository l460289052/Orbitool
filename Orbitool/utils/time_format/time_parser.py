import re
from datetime import datetime

from sortedcontainers import SortedDict

from . import time_convert

START_DT = datetime(1990, 1, 1)
END_DT = datetime(3000, 1, 1)

numbers = SortedDict()
numbers[time_convert.getExcelTime(START_DT)] = time_convert.fromExcelTime
numbers[time_convert.getIgorTime(START_DT)] = time_convert.fromIgorTime
numbers[time_convert.getMatlabTime(START_DT)] = time_convert.fromMatlabTime

num_re = re.compile(r"\d+")


def fromOtherTimeFormat(s):
    nums = list(map(int, num_re.findall(s)))
    if nums[0] < 1990:
        if nums[2] > 1990:
            nums[:3] = nums[2], nums[0], nums[1]
        else:
            raise ValueError(f"Unrecognized datetime :{s},\n"
                             "please use numeric like excel time / igor time / matlab time \n"
                             "or ISO format time, or yyyy/mm/dd hh:MM:SS or dd/mm/yyyy hh:MM:SS")
    return datetime(*nums)


class TimeParser:
    def __init__(self) -> None:
        self._parser = None

    def parse(self, s: str) -> datetime:
        if self._parser is not None:
            try:
                ret = self._parser(s)
                assert START_DT < ret < END_DT
                return ret
            except:
                pass
        try:  # number
            tmp = float(s)
            _, converter = numbers.peekitem(numbers.bisect(tmp) - 1)

            def parser(s):
                return converter(float(s))
            self._parser = parser
            return converter(s)
        except:
            pass
        # str
        try:
            ret = time_convert.fromIsoTime(s)
            self._parser = time_convert.fromIsoTime
            return ret
        except:  # not iso
            pass
        ret = fromOtherTimeFormat(s)
        self._parser = fromOtherTimeFormat
        return ret
