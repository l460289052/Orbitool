import re
from collections import defaultdict

element = re.compile(r"((e?[+-]|[A-Za-z][a-z]{0,2})(\[\d+\])?)(\d*)")
num_re = re.compile(r"\d*")


def get_right_parenthesis_index(s: str, left_index, length: int = None):
    length = length or len(s)
    index = left_index
    sum = 1
    while index < length:
        index += 1
        now_c = s[index]
        if now_c == '(':
            sum += 1
        elif now_c == ')':
            sum -= 1
            if sum == 0:
                return index
    raise ValueError(
        f'Cannot understand {s[left_index:]}')


def convert_to_dict(formula: str) -> dict:
    ret = defaultdict(int)
    now = 0
    length = len(formula)
    while now < length:
        now_c = formula[now]
        if now_c.isupper():
            match = element.match(formula, now)
            if match:
                ele = match.group(2)
                num = match.group(4) or 1
                ret[ele] += int(num)
            now = match.end()
        elif now_c == '(':
            right_index = get_right_parenthesis_index(formula, now, length)
            sub_d = convert_to_dict(formula[now + 1:right_index])

            now = right_index + 1

            match = num_re.match(formula, now)
            num = int(match.group(0) or 1)
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
