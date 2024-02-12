from typing import List
from .. import H5File, BaseStructure, JSONObject, BaseRowStructure


def test_attr():
    class Struct(BaseStructure):
        j: JSONObject = {"a": 123}

    f = H5File()
    s = Struct()
    f.write("s", s)
    assert f.read("s", Struct) == s

    s.j = ["123", "你好", 123]
    f.write("s", s)
    assert f.read("s", Struct) == s


def test_dataset():
    class Row(BaseRowStructure):
        t: str
        j: JSONObject

    class Struct(BaseStructure):
        lr: List[Row] = []
        lj: List[JSONObject] = []

    s = Struct()
    s.lj = [123, ["123", 123], {"a": "你好", "b": 123}]
    s.lr = [Row(t=str(j), j=j) for j in s.lj]

    f = H5File()
    f.write("s", s)
    assert f.read("s", Struct) == s
