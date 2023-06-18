from datetime import timedelta
import re

pattern = re.compile(r"(\d+)([wdhms])")


def str2timedelta(s: str):
    w = d = h = m = sec = 0
    for group in pattern.finditer(s):
        delta = int(group.group(1))
        match group.group(2):
            case "w": w += delta
            case "d": d += delta
            case "h": h += delta
            case "m": m += delta
            case "s": sec += delta
    td = timedelta(d, sec, 0, 0, m, h, w)
    assert td.total_seconds() > 1, "time interval line edit cannot be empty"
    return td
