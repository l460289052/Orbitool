from ._formula import Formula


def formula_range(
        base: Formula, group_plus: Formula, group_minus: Formula,
        step_min: int, step_max: int):
    step_max += 1
    if step_min < 0:
        for i in range(abs(step_min)):
            tmp = base + group_minus
            if group_plus in tmp:
                base = tmp - group_plus
            else:
                step_min = -i
                break
    else:
        for i in range(step_min):
            tmp = base + group_plus
            if group_minus in tmp:
                base = tmp - group_minus
            else:
                return
    for i in range(step_max - step_min):
        yield base
        tmp = base + group_plus
        if group_minus in tmp:
            base = tmp - group_minus
        else:
            return
