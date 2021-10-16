from datetime import datetime, timedelta
import pytest
from . import time_convert
from .time_parser import TimeParser


@pytest.fixture
def parser():
    return TimeParser()


@pytest.fixture
def times():
    base = datetime.now()
    return [base + timedelta(minutes=i) for i in range(10)]


def test_iso_time(parser: TimeParser, times):
    base = times[0]
    str_times = list(map(str, times))
    assert base == parser.parse(str_times[0])
    assert times == list(map(parser._parser, str_times))


def test_igor_time(parser: TimeParser, times):
    igor_times = list(map(time_convert.getIgorTime, times))
    times = [t.replace(microsecond=0) for t in times]
    assert times[0] == parser.parse(igor_times[0])
    assert times == list(map(parser._parser, igor_times))


def test_excel_time(parser: TimeParser, times):
    excel_times = list(map(time_convert.getExcelTime, times))
    delta = timedelta(microseconds=1e3)
    assert abs(times[0] - parser.parse(excel_times[0])) < delta
    for t1, t2 in zip(map(parser._parser, excel_times), times):
        assert abs(t1 - t2) < delta


def test_matlab_time(parser: TimeParser, times):
    matlab_times = list(map(time_convert.getMatlabTime, times))
    times = [t.replace(microsecond=0) for t in times]
    delta = timedelta(seconds=1)
    assert (times[0] - parser.parse(matlab_times[0])) <= delta
    for t1, t2 in zip(map(parser._parser, matlab_times), times):
        assert abs(t1 - t2) <= delta


def test_other_format_time(parser: TimeParser):
    s = "2020/10/3 3:4:05"
    assert parser.parse(s) == datetime(2020, 10, 3, 3, 4, 5)
    s = "10/3/2020 3:4:05"
    assert parser.parse(s) == datetime(2020, 10, 3, 3, 4, 5)


def test_mixed_time(parser: TimeParser, times):
    parsers = set()
    test_iso_time(parser, times)
    parsers.add(parser._parser)
    test_igor_time(parser, times)
    parsers.add(parser._parser)
    test_excel_time(parser, times)
    parsers.add(parser._parser)
    test_matlab_time(parser, times)
    parsers.add(parser._parser)
    test_other_format_time(parser)
    parsers.add(parser._parser)
    assert len(parsers) == 5
