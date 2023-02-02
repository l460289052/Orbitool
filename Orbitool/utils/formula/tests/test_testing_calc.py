from .calc import State


def test_state():
    s = State(1, 1, 1, 1, 1)
    s2 = s + s
    assert s2.DBE2 == s2.HMin == s2.HMax == s2.OMin == s2.OMax == 2
    s3 = s * 4
    assert s3.DBE2 == s3.HMin == s3.HMax == s3.OMin == s3.OMax == 4
    s4 = s3-s3
    assert s4.DBE2 == s4.HMin == s4.HMax == s4.OMin == s4.OMax == 0
