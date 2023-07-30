from .utils import str2timedelta, timedelta2str, timedelta

def assert_str(s: str):
    assert timedelta2str(str2timedelta(s)) == s

def test():
    assert_str("2h5m")
    assert_str("5w3s")
    assert_str("1w1d1h1m1s")
    assert timedelta2str(str2timedelta("3000s")) == "50m"

