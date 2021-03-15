import pytest
import random
from .. import _converter as converter


def test_two_chain():
    for i in range(20):
        a = [(i, i + 1)for i in range(10)]
        b = [(i, i + 1) for i in range(20, 30)]
        random.shuffle(a)
        random.shuffle(b)

        d = dict(a)
        d.update(b)

        chains = converter.generate_chain(d)
        assert len(chains) == 2
        c1 = chains[0]
        c2 = chains[1]
        if c1[0] != 0:
            c1 = chains[1]
            c2 = chains[0]
        assert list(c1) == list(range(11))
        assert list(c2) == list(range(20, 31))
