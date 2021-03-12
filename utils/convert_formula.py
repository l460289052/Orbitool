import re
from collections import defaultdict

element = re.compile(r"([A-Z][a-z]{0,2})(\d)?")
num_re = re.compile(r"(\d)?")


def convert_to_dict(formula) -> dict:
    ret = defaultdict(int)
    now = 0
    length = len(formula)
    while now < length:
        now_c: str = formula[now]
        if now_c.isupper():
            match = element.match(formula, now)
            if match:
                ele = match.group(1)
                num = match.group(2) or 1
                ret[ele] += int(num)
            now = match.end()
        elif now_c == '(':
            index = 0
            i = now
            while i < length:
                now_c = formula[i]
                if now_c == '(':
                    index += 1
                elif now_c == ')':
                    index -= 1
                    if index <= 0:
                        if index == 0:
                            break
                        else:
                            raise ValueError(
                                f'Cannot understand {formula[now:i+1]}')
                i += 1
            if index != 0:
                raise ValueError(
                    f'Cannot understand {formula[now:i+1]}')

            sub_d = convert_to_dict(formula[now + 1:i])
            now = i + 1

            match = num_re.match(formula, now)
            num = int(match.group(1) or 1)
            for key in sub_d.keys():
                ret[key] += sub_d[key] * num

            now = match.end()

        elif now_c == '-':
            ret['charge'] = -1
            now += 1
        elif now_c == '+':
            ret['charge'] = 1
            now += 1
        else:
            raise ValueError(f"Cannot understand {formula[now:]}")
    return ret


def convert_from_dict(formula: defaultdict):
    charge = formula.pop('charge', 0)
    s = []
    for k, v in formula.items():
        s.append(f'{k}{v}')
    if charge == 1:
        s += '+'
    elif charge == -1:
        s += '-'

    s = ''.join(s)
    return s


def delete_formula_bracket(formula: str):
    """
    >>> f = "(H2O)3NO3-"
    >>> f = delete_formula_bracket(f)
    >>> print(f)
    H6O6N1-

    """
    return convert_from_dict(convert_to_dict(formula))
