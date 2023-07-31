from datetime import timedelta
import re

pattern = re.compile(r"(\d+)([wdhms])")


def str2timedelta(s: str):
    w = d = h = m = sec = 0
    for group in pattern.finditer(s.lower()):
        delta = int(group.group(1))
        match group.group(2):
            case "w": w += delta
            case "d": d += delta
            case "h": h += delta
            case "m": m += delta
            case "s": sec += delta
    td = timedelta(d, sec, 0, 0, m, h, w)
    assert td.total_seconds() >= 1, "time interval must be not less than 1 second"
    return td

def timedelta2str(d: timedelta):
    l = []
    if d.days // 7:
        l.append(f"{d.days // 7}w")
    if d.days % 7:
        l.append(f"{d.days % 7}d")
    if d.seconds // 3600:
        l.append(f"{d.seconds // 3600}h")
    sec = d.seconds % 3600
    if sec // 60:
        l.append(f"{sec // 60}m")
    if sec % 60:
        l.append(f"{sec % 60}s")
    return "".join(l)